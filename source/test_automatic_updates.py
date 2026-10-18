from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import Mock,patch
import hashlib,json,queue,tempfile,unittest
import app_updates as updates
from automatic_updates import save_pending,load_pending,AutomaticUpdater

class AutomaticTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.data=b'installer fixture';tag='v1.6.0';name='SSMD-Windows-AMD64-Update.exe'
        asset=updates.Asset(name,updates.release_url(tag,name),len(self.data),hashlib.sha256(self.data).hexdigest(),'')
        self.release=updates.Release('1.6.0',updates.RELEASES+'/tag/'+tag,True,asset)
        self.path=self.root/'updates/1.6.0'/name;self.path.parent.mkdir(parents=True);self.path.write_bytes(self.data)
    def test_pending_is_verified_and_corruption_blocks_handoff(self):
        save_pending(self.root,self.release,self.path)
        self.assertEqual(load_pending(self.root)[0],self.path.resolve())
        self.assertIsNone(load_pending(self.root,current='1.6.0'))
        self.path.write_bytes(b'corrupted')
        with self.assertRaises(ValueError):load_pending(self.root)
    def test_only_our_cache_and_release_installer_are_accepted(self):
        outside=self.root/'other.exe';outside.write_bytes(self.data)
        with self.assertRaises(ValueError):save_pending(self.root,self.release,outside)
        save_pending(self.root,self.release,self.path);p=self.root/'updates/pending.json';record=json.loads(p.read_text());record['release']['asset']['url']='https://example.com/bad.exe';p.write_text(json.dumps(record))
        with self.assertRaises(ValueError):load_pending(self.root)
    def test_automatic_close_obeys_off_switch_and_uses_silent_handoff(self):
        save_pending(self.root,self.release,self.path)
        app=SimpleNamespace(settings_path=self.root/'settings.json',home=self.root/'program',saved_settings={'automatic_app_updates':False})
        auto=AutomaticUpdater(app,enabled=False);auto.enabled=True
        with patch.object(updates,'launch_installer')as launch:
            auto.close();launch.assert_not_called();auto.closing=False;app.saved_settings['automatic_app_updates']=True;auto.close();self.assertTrue(launch.call_args.kwargs['silent'])
    def test_background_download_does_not_lock_media_jobs_and_is_persisted(self):
        card=Mock();app=SimpleNamespace(settings_path=self.root/'settings.json',home=self.root,operation='idle',saved_settings={},events=queue.Queue(),settings_page=SimpleNamespace(update_card=card))
        auto=AutomaticUpdater(app,enabled=False);auto.enabled=True
        class ImmediateThread:
            def __init__(self,*,target,daemon):self.target=target
            def start(self):self.target()
        with patch('automatic_updates.threading.Thread',ImmediateThread),patch.object(updates,'can_install',return_value=True),patch.object(updates,'has_engines',return_value=True),patch.object(updates,'check_release',return_value=self.release),patch.object(updates,'download_release',return_value=self.path):auto.check_due()
        self.assertEqual(app.operation,'idle');self.assertEqual(app.events.get()[0],'automatic_app_ready');self.assertEqual(load_pending(self.root)[0],self.path.resolve())
if __name__=='__main__':unittest.main()
