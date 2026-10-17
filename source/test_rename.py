from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch

from data_migration import migrate_data, user_data_directory
from engine import APP_NAME, APP_FULL_NAME
from i18n import STRINGS
from app_updates import can_install, parse_release, RELEASES, release_url


class RenameTests(unittest.TestCase):
    def test_branding_and_all_current_translations(self):
        self.assertEqual(APP_NAME,'SSMD')
        self.assertEqual(APP_FULL_NAME,"Slulisee's simple media downloader")
        for key,translations in STRINGS.items():
            for text in translations:self.assertNotIn('SSYTDLP',text,key)

    def test_migration_copies_queue_wallpaper_and_preferences_without_touching_legacy(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp);old=base/'SSYTDLP';new=base/'SSMD';old.mkdir()
            (old/'settings.json').write_text(json.dumps(dict(language='de',theme='carbon',folder=str(base/'Music'),wallpaper=str(old/'wallpaper.png'))),encoding='utf-8')
            (old/'queue.json').write_bytes(b'generated pending queue fixture')
            (old/'queue.bak').write_bytes(b'generated backup fixture')
            (old/'wallpaper.png').write_bytes(b'generated wallpaper fixture')
            (old/'cookies.txt').write_bytes(b'private export must not be copied')
            (old/'updates').mkdir();(old/'updates/old.exe').touch()
            before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()}
            self.assertEqual(migrate_data(new,old),new)
            self.assertEqual((new/'queue.json').read_bytes(),(old/'queue.json').read_bytes())
            values=json.loads((new/'settings.json').read_text('utf-8'))
            self.assertEqual(values['wallpaper'],str(new/'wallpaper.png'))
            self.assertEqual(values['language'],'de');self.assertEqual(values['theme'],'carbon')
            self.assertFalse((new/'cookies.txt').exists());self.assertFalse((new/'updates').exists())
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in old.iterdir() if p.is_file()})
            self.assertEqual(sorted(p.name for p in base.iterdir()),['SSMD','SSYTDLP'])

    def test_existing_ssmd_data_wins_and_failed_copy_keeps_old_app_usable(self):
        with tempfile.TemporaryDirectory() as temp:
            old=Path(temp)/'SSYTDLP';new=Path(temp)/'SSMD';old.mkdir();new.mkdir()
            (old/'settings.json').write_text('{"theme":"carbon"}',encoding='utf-8')
            (new/'settings.json').write_text('{"theme":"ocean"}',encoding='utf-8')
            migrate_data(new,old)
            self.assertEqual(json.loads((new/'settings.json').read_text())['theme'],'ocean')
            (new/'settings.json').unlink();new.rmdir()
            with patch('data_migration.shutil.copy2',side_effect=OSError('Generated copy failure')):
                with self.assertRaises(OSError):migrate_data(new,old)
            self.assertFalse(new.exists());self.assertTrue((old/'settings.json').is_file())
            self.assertEqual(list(Path(temp).iterdir()),[old])
            with patch('data_migration.config_directory',side_effect=[new,old]),patch('data_migration.migrate_data',side_effect=OSError('copy failure')):
                self.assertEqual(user_data_directory(),old)

    def test_updates_prefer_ssmd_and_accept_legacy_app_folder(self):
        assets=[]
        for name in ['SSYTDLP-Windows-AMD64-Update.exe','SSMD-Windows-AMD64-Update.exe']:
            assets.append(dict(name=name,size=10,digest='sha256:'+'a'*64,browser_download_url=release_url('v1.4.0',name)))
        value=parse_release(dict(tag_name='v1.4.0',html_url=RELEASES+'/tag/v1.4.0',assets=assets),current='1.3.0',system='Windows',machine='AMD64',lightweight=True)
        self.assertEqual(value.asset.name,'SSMD-Windows-AMD64-Update.exe')
        with tempfile.TemporaryDirectory() as temp:
            home=Path(temp);(home/'SSYTDLP.exe').touch()
            self.assertTrue(can_install(home,'Windows',True))
            (home/'SSYTDLP.exe').rename(home/'SSMD.exe')
            self.assertTrue(can_install(home,'Windows',True))


if __name__=='__main__':unittest.main()
