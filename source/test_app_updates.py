from dataclasses import replace
from pathlib import Path
import hashlib
import io
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

import app_updates as updates


def fixture(tag='v1.4.0', name='SSMD-Windows-AMD64-Update.exe', data=b'installer fixture'):
    return dict(tag_name=tag, html_url=updates.RELEASES + '/tag/' + tag,
        assets=[dict(name=name, size=len(data), digest='sha256:' + hashlib.sha256(data).hexdigest(),
                     browser_download_url=updates.release_url(tag, name))])


class AppUpdateTests(unittest.TestCase):
    def test_stable_version_order_and_no_downgrade(self):
        for current, tag, newer in [('1.9.0','v1.10.0',True),('1.3.0','v1.3.0',False),('2.0.0','v1.3.0',False)]:
            self.assertEqual(updates.parse_release(fixture(tag), current, 'Windows', 'AMD64', True).newer, newer)
        for value in ['1.0', 'v1.0.0-beta', '../1.0.0', '1.0.0\n']:
            with self.assertRaises(ValueError):updates.version_tuple(value)

    def test_stable_release_and_fixed_repository_urls_only(self):
        for field, value in [('prerelease',True),('draft',True),('html_url','https://example.com/release')]:
            data=fixture();data[field]=value
            with self.assertRaises(ValueError):updates.parse_release(data)
        data=fixture();data['assets'][0]['browser_download_url']='https://example.com/setup.exe'
        with self.assertRaises(ValueError):updates.parse_release(data,system='Windows',machine='amd64',lightweight=True)

    def test_matching_platform_and_waiting_for_complete_publication(self):
        data=fixture()
        self.assertIsNotNone(updates.parse_release(data,system='Windows',machine='amd64',lightweight=True).asset)
        self.assertIsNone(updates.parse_release(data,system='Windows',machine='arm64').asset)
        self.assertIsNone(updates.parse_release(data,system='Darwin',machine='x86_64').asset)
        data['assets'][0]['digest']=None
        self.assertIsNone(updates.parse_release(data,system='Windows',machine='amd64',lightweight=True).asset)
        name=data['assets'][0]['name']+'.sha256'
        data['assets'].append(dict(name=name,browser_download_url=updates.release_url('v1.4.0',name)))
        self.assertTrue(updates.parse_release(data,system='Windows',machine='amd64',lightweight=True).asset.checksum_url)

    def test_checksum_fallback_names_are_exact(self):
        asset=updates.parse_release(fixture(),system='Windows',machine='amd64',lightweight=True).asset
        asset=replace(asset,sha256='',checksum_url=asset.url+'.sha256')
        with patch.object(updates,'read_url',return_value=('a'*64+'  '+asset.name+'\n').encode()):
            self.assertEqual(updates.expected_checksum(asset),'a'*64)
        with patch.object(updates,'read_url',return_value=('a'*64+'  wrong.exe').encode()):
            with self.assertRaises(ValueError):updates.expected_checksum(asset)

    def test_download_verified_atomic_and_rejects_corruption_truncation_overflow(self):
        asset=updates.parse_release(fixture(),system='Windows',machine='amd64',lightweight=True).asset
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/asset.name
            for contents in [b'tampered contents',b'short',b'installer fixture extra']:
                target.write_bytes(b'previous verified file')
                with patch.object(updates,'urlopen',return_value=io.BytesIO(contents)):
                    with self.assertRaises(ValueError):updates.download_release(asset,temp)
                self.assertEqual(target.read_bytes(),b'previous verified file')
                self.assertFalse(target.with_suffix('.exe.part').exists())
            progress=[]
            with patch.object(updates,'urlopen',return_value=io.BytesIO(b'installer fixture')):
                self.assertEqual(updates.download_release(asset,temp,lambda a,b:progress.append((a,b))),target)
            self.assertEqual(target.read_bytes(),b'installer fixture')
            self.assertEqual(progress[-1],(17,17))

    def test_cancelled_download_leaves_current_app_and_no_partial_file(self):
        asset=updates.parse_release(fixture(),system='Windows',machine='amd64',lightweight=True).asset
        event=threading.Event();event.set()
        with tempfile.TemporaryDirectory() as temp, patch.object(updates,'urlopen',return_value=io.BytesIO(b'installer fixture')):
            with self.assertRaises(updates.UpdateCancelled):updates.download_release(asset,temp,cancelled=event)
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_installer_is_reverified_and_uses_native_command_with_space_path(self):
        asset=updates.parse_release(fixture(),system='Windows',machine='amd64',lightweight=True).asset
        with tempfile.TemporaryDirectory(prefix='app update ') as temp:
            home=Path(temp)/'installed app';home.mkdir();(home/'SSMD.exe').touch()
            exe=Path(temp)/asset.name;exe.write_bytes(b'installer fixture')
            with patch.object(updates.platform,'system',return_value='Windows'),patch.object(updates.subprocess,'Popen') as launch:
                updates.launch_installer(exe,home,asset)
                self.assertTrue(launch.call_args.args[0].endswith(' /D='+str(home.resolve())))
                self.assertFalse(launch.call_args.kwargs.get('shell',False))
                exe.write_bytes(b'changed')
                with self.assertRaises(ValueError):updates.launch_installer(exe,home,asset)
                self.assertEqual(launch.call_count,1)


if __name__=='__main__':unittest.main()
