from dataclasses import replace
from pathlib import Path
import json
import os
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

try:
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication
    import desktop
    from desktop import App
    QT_AVAILABLE=True
except ImportError:
    QT_AVAILABLE=False

from engine import Options, PRESETS, build_args
from queue_model import Batch, MediaEntry, MediaSource, QueueRecord


def fixture():
    return MediaSource('https://www.youtube.com/playlist?list=fixture','Example playlist',True,
        [MediaEntry(1,'One','Artist',90),MediaEntry(2,'[Private video]',available=False),MediaEntry(3,'Three','Artist',130)])


@unittest.skipUnless(QT_AVAILABLE,'Install the GUI requirements for desktop tests')
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])
        cls.qt.setStyle('Fusion');cls.qt.setQuitOnLastWindowClosed(False)
        if os.name=='nt' and cls.qt.platformName()=='offscreen':
            # The Windows offscreen plugin has no system-font enumerator.
            # Load the same fonts used by the native desktop before measuring layout.
            from PySide6.QtGui import QFontDatabase
            for name in ('segoeui.ttf','segoeuib.ttf'):
                path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'/name
                if path.is_file():QFontDatabase.addApplicationFont(str(path))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'settings.json'
        self.app=App(self.path);self.app.show();self.qt.processEvents()

    def tearDown(self):
        if self.app.selection_dialog:self.app.selection_dialog.reject()
        self.app.operation='idle';self.app.close();self.app.deleteLater();self.qt.processEvents();self.temp.cleanup()

    def test_app_update_page_checks_async_translates_and_respects_busy_state(self):
        from app_updates import Release, Asset
        page=self.app.settings_page;card=page.update_card
        self.app.navigate('settings');page.select_section('updates')
        self.assertTrue(card.isVisible())
        for language in desktop.LANGUAGES:
            self.app.language=language;self.app.apply_appearance(persist=False)
            self.assertEqual(card.check_button.text(),self.app.t('app_check'))
            self.app.resize(900,760);self.qt.processEvents()
            self.assertEqual(page.horizontalScrollBar().maximum(),0)
        release=Release('1.4.0','https://github.com/Slulisee/SSYTDLP/releases/tag/v1.4.0',True,Asset('setup.exe','https://example.com',100,'a'*64,''))
        with patch('app_updates.check_release',return_value=release):
            QTest.mouseClick(card.check_button,Qt.MouseButton.LeftButton)
            self.assertEqual(self.app.operation,'app_check')
            self.until(lambda:self.app.operation=='idle')
        self.assertTrue(card.download_button.isVisible());self.assertEqual(card.status_key,'app_available')
        self.app.set_operation('download')
        self.assertFalse(card.check_button.isEnabled());self.assertFalse(card.download_button.isEnabled())
        self.app.set_operation('idle')
        card.receive('app_update_error','Offline fixture')
        self.assertIn('Offline fixture',card.status.text());self.assertTrue(card.check_button.isEnabled())

    def test_app_update_download_reaches_verified_install_handoff(self):
        import hashlib
        import io
        import app_updates
        card=self.app.settings_page.update_card
        self.app.navigate('settings');self.app.settings_page.select_section('updates')
        content=b'Generated update fixture'
        asset=app_updates.Asset('SSYTDLP-Windows-AMD64-Update.exe','https://example.com/fixture',len(content),hashlib.sha256(content).hexdigest(),'')
        card.receive('app_release',app_updates.Release('1.4.0',app_updates.RELEASES+'/tag/v1.4.0',True,asset))
        with patch.object(app_updates,'urlopen',return_value=io.BytesIO(content)):
            QTest.mouseClick(card.download_button,Qt.MouseButton.LeftButton)
            self.until(lambda:self.app.operation=='idle')
        self.assertEqual(card.downloaded.read_bytes(),content)
        self.assertTrue(card.install_button.isVisible());self.assertFalse(card.download_button.isVisible())
        with patch.object(card,'installable',return_value=True),patch.object(app_updates,'launch_installer') as launch:
            card.install()
            launch.assert_called_once_with(card.downloaded,self.app.home,asset)
            self.assertFalse(self.app.isVisible())
            self.assertTrue(self.path.is_file())

    def until(self,predicate,timeout=4):
        end=time.monotonic()+timeout
        while not predicate() and time.monotonic()<end:
            self.qt.processEvents();QTest.qWait(15)
        self.assertTrue(predicate())

    def test_queue_preview_choices_and_options_remain_the_same(self):
        self.app.show_selection(fixture());dialog=self.app.selection_dialog
        dialog.change_all('none');self.assertFalse(dialog.accept_button.isEnabled())
        dialog.change_all('invert');self.assertEqual(dialog.selected,{1,3})
        dialog.toggle_rows([0,1]);self.assertEqual(dialog.selected,{3})
        dialog.accept_selection();self.qt.processEvents()
        self.assertEqual(self.app.records[0].selected,[3])
        self.assertEqual(self.app.operation,'idle');self.assertIsNone(self.app.batch)
        self.app.preset_box.setCurrentIndex(3);self.app.lyrics.setChecked(True)
        actual=self.app.records[0].options(self.app.get_options())
        expected=replace(Options(fixture().url,self.app.folder_entry.text()),preset=list(PRESETS)[3],playlist=True,playlist_items=(3,),lyrics=True)
        self.assertEqual(build_args(actual,Path('tools')),build_args(expected,Path('tools')))
        self.app.tree.selectRow(0);self.assertTrue(self.app.edit_button.isEnabled())
        self.app.edit_selection();self.assertEqual(self.app.selection_dialog.selected,{3})

    def test_themes_custom_colors_preserve_queue_and_download_options(self):
        self.app.records=[QueueRecord(fixture(),[1,3])];self.app.refresh_queue()
        before=self.app.get_options()
        self.app.navigate('settings')
        QTest.mouseClick(self.app.settings_page.tiles['carbon'],Qt.MouseButton.LeftButton)
        self.assertEqual(self.app.theme,'carbon')
        self.assertTrue(self.app.set_custom_color('accent','#ad33dd'))
        self.assertEqual(self.app.get_options(),before)
        self.assertEqual(self.app.records[0].selected,[1,3])
        saved=json.loads(self.path.read_text('utf-8'))
        self.assertEqual(saved['theme_colors']['accent'],'#ad33dd')
        self.assertEqual(self.app.store.load()[0].selected,[1,3])
        self.app.settings_page.reset_colors();self.assertEqual(self.app.theme_colors,{})

    def test_checkbox_mark_and_keyboard_state_are_visible_in_every_theme(self):
        for theme in desktop.THEMES:
            self.app.choose_theme(theme)
            check=self.app.metadata
            check.setChecked(False);self.qt.processEvents();off=check.grab().toImage()
            check.setFocus();QTest.keyClick(check,Qt.Key.Key_Space);self.qt.processEvents()
            self.assertTrue(check.isChecked(),theme)
            on=check.grab().toImage()
            self.assertNotEqual(off,on,theme)
            self.assertIn(self.app.colors['accent'],[on.pixelColor(x,y).name() for x in range(5,18) for y in range(8,22)],theme)

    def test_translations_keep_preset_and_selection(self):
        self.app.preset_box.setCurrentIndex(4)
        for index,language in enumerate(desktop.LANGUAGES):
            self.app.settings_page.language.setCurrentIndex(index);self.qt.processEvents()
            self.assertEqual(self.app.language,language)
            self.assertEqual(self.app.add_button.text(),self.app.t('preview_add'))
            self.assertEqual(self.app.preset_box.currentIndex(),4)
            self.assertEqual(self.app.preset,list(PRESETS)[4])

    def test_existing_media_and_ssmp_settings_round_trip(self):
        page=self.app.settings_page
        page.subtitle_languages.setText('en.*,de.*');page.automatic_subtitles.setChecked(True)
        page.embed_subtitles.setChecked(True);page.embed_lyrics.setChecked(False)
        page.ssmp_enabled.setChecked(True);page.ssmp_inbox.setText(str(Path(self.temp.name)/'inbox'))
        page.apply_media()
        options=self.app.get_options()
        self.assertTrue(options.ssmp_enabled and options.automatic_subtitles and options.embed_subtitles)
        self.assertFalse(options.embed_lyrics)
        self.assertFalse(Path(options.ssmp_inbox).exists())
        saved=json.loads(self.path.read_text('utf-8'))
        self.assertEqual(saved['ssmp_inbox'],options.ssmp_inbox)

    def test_preview_worker_stages_a_link_without_starting_a_download(self):
        info={'_type':'playlist','title':'Preview','entries':[{'id':'a','title':'One'},{'id':'b','title':'Two'}]}
        class FakePreview:
            def __init__(self,*args):self.cancelled=threading.Event()
            def fetch(self,url):return info
        with patch.object(desktop,'Preview',FakePreview):
            self.app.url_entry.setText('https://www.youtube.com/playlist?list=fixture')
            self.app.preview_link();self.until(lambda:self.app.selection_dialog is not None)
            self.app.selection_dialog.accept_selection();self.qt.processEvents()
        self.assertEqual(len(self.app.records),1);self.assertIsNone(self.app.batch)
        self.assertEqual(self.app.url_entry.text(),'')

    def test_batch_uses_existing_options_and_continues_after_error(self):
        options=[]
        class FakeDownload:
            def __init__(self,tools,emit):self.emit=emit
            def run(self,value):
                options.append(value)
                self.emit('progress',{'total_bytes':100,'downloaded_bytes':75,'speed':1024,'eta':1})
                self.emit('done',{'status':'error' if len(options)==1 else 'success','files':0 if len(options)==1 else 1})
        self.app.records=[QueueRecord(fixture(),[1]),QueueRecord(fixture(),[3])];self.app.refresh_queue()
        with patch.object(desktop,'Batch',lambda tools,emit:Batch(tools,emit,FakeDownload)):
            self.app.start();self.until(lambda:self.app.operation=='idle')
        self.assertEqual([x.playlist_items for x in options],[(1,),(3,)])
        self.assertEqual([r.status for r in self.app.records],['error','completed'])
        self.assertIn('1 errors',self.app.status.text());self.assertTrue(self.app.clear_button.isEnabled())

    def test_appearance_preserves_unknown_settings_and_wallpaper(self):
        from PIL import Image
        path=Path(self.temp.name)/'original.png';Image.new('RGB',(32,32),'purple').save(path)
        self.app.saved_settings['future_setting']={'keep':True}
        self.app.wallpaper_path=str(path);self.app.apply_appearance()
        self.assertFalse(self.app.background.wallpaper.isNull())
        self.app.choose_theme('sakura')
        saved=json.loads(self.path.read_text('utf-8'))
        self.assertEqual(saved['future_setting'],{'keep':True});self.assertEqual(saved['wallpaper'],str(path))

    def test_cancel_does_not_start_the_next_queued_source(self):
        calls=[]
        class SlowDownload:
            def __init__(self,tools,emit):self.emit=emit;self.stopped=threading.Event()
            def cancel(self):self.stopped.set()
            def run(self,options):
                calls.append(options)
                self.stopped.wait(3)
                self.emit('done',{'status':'cancelled' if self.stopped.is_set() else 'success','files':0})
        self.app.records=[QueueRecord(fixture(),[1]),QueueRecord(fixture(),[3])];self.app.refresh_queue()
        with patch.object(desktop,'Batch',lambda tools,emit:Batch(tools,emit,SlowDownload)):
            self.app.start();self.until(lambda:bool(calls))
            self.assertFalse(self.app.add_button.isEnabled())
            self.app.cancel();self.until(lambda:self.app.operation=='idle')
        self.assertEqual(len(calls),1)
        self.assertEqual([r.status for r in self.app.records],['cancelled','queued'])
        self.assertTrue(self.app.add_button.isEnabled())

    def test_saved_legacy_settings_and_queue_reopen_with_the_new_appearance(self):
        self.app.close();self.app.deleteLater();self.qt.processEvents()
        self.path.write_text(json.dumps({'theme':'dark','preset':list(PRESETS)[3],'metadata':False,'ssmp_enabled':True,'future':'keep'}))
        self.app=App(self.path);self.app.show();self.qt.processEvents()
        self.assertEqual(self.app.theme,'ocean');self.assertFalse(self.app.metadata.isChecked())
        self.assertTrue(self.app.ssmp_enabled)
        self.app.records=[QueueRecord(fixture(),[3])];self.app.refresh_queue()
        self.app.choose_theme('lavender');self.app.set_custom_color('accent','#990099');self.app.persist()
        saved=json.loads(self.path.read_text('utf-8'))
        self.assertEqual(saved['future'],'keep');self.assertEqual(saved['preset'],list(PRESETS)[3])
        self.assertEqual(self.app.store.load()[0].selected,[3])

    def test_compact_layout_in_each_ui_language(self):
        self.app.resize(900,680)
        for index,language in enumerate(desktop.LANGUAGES):
            self.app.settings_page.language.setCurrentIndex(index)
            self.app.navigate('downloader');self.qt.processEvents();QTest.qWait(20)
            self.assertEqual(self.app.downloader_scroll.horizontalScrollBar().maximum(),0,language)
            self.app.navigate('settings');self.qt.processEvents();QTest.qWait(20)
            self.assertEqual(self.app.settings_page.horizontalScrollBar().maximum(),0,language)

    def test_compact_window_scrolls_vertically_without_clipping_the_main_controls(self):
        self.app.resize(900,680);self.qt.processEvents();QTest.qWait(50)
        self.assertTrue(self.app.compact_checks)
        self.assertEqual(self.app.downloader_scroll.horizontalScrollBar().maximum(),0)
        self.app.downloader_scroll.ensureWidgetVisible(self.app.download_button);self.qt.processEvents()
        button=self.app.download_button
        point=button.mapTo(self.app.downloader_scroll.viewport(),button.rect().center())
        self.assertTrue(self.app.downloader_scroll.viewport().rect().contains(point))
        self.app.navigate('settings');self.qt.processEvents();QTest.qWait(50)
        self.assertLessEqual(self.app.settings_page.gallery_columns,3)
        self.assertEqual(self.app.settings_page.horizontalScrollBar().maximum(),0)

    def test_delete_in_link_field_does_not_remove_selected_queue_entries(self):
        self.app.records=[QueueRecord(fixture(),[1])];self.app.refresh_queue();self.app.tree.selectRow(0)
        self.app.url_entry.setText('https://example.com/test');self.app.url_entry.setFocus();self.app.url_entry.selectAll()
        QTest.keyClick(self.app.url_entry,Qt.Key.Key_Delete);self.qt.processEvents()
        self.assertEqual(len(self.app.records),1)
        self.app.tree.setFocus();self.qt.processEvents();QTest.keyClick(self.app.tree,Qt.Key.Key_Delete);self.qt.processEvents()
        self.assertEqual(len(self.app.records),0)

    def test_preview_space_key_is_scoped_to_the_table(self):
        self.app.show_selection(fixture());self.qt.processEvents();dialog=self.app.selection_dialog
        dialog.tree.setFocus();self.qt.processEvents();QTest.keyClick(dialog.tree,Qt.Key.Key_Space);self.qt.processEvents()
        self.assertEqual(dialog.selected,{3})
        dialog.accept_button.setFocus();self.qt.processEvents();QTest.keyClick(dialog.accept_button,Qt.Key.Key_Space);self.qt.processEvents()
        self.assertEqual(self.app.records[0].selected,[3])

    def test_hex_color_controls_apply_and_persist_without_changing_download_options(self):
        before=self.app.get_options();page=self.app.settings_page
        self.app.navigate('settings');page.ensureWidgetVisible(page.color_controls['accent'][1])
        edit=page.color_controls['accent'][1];edit.setFocus();edit.selectAll()
        QTest.keyClicks(edit,'#a044cc');QTest.keyClick(edit,Qt.Key.Key_Tab);self.qt.processEvents()
        self.assertEqual(self.app.colors['accent'],'#a044cc')
        self.assertEqual(json.loads(self.path.read_text('utf-8'))['theme_colors']['accent'],'#a044cc')
        self.assertEqual(self.app.get_options(),before)
        self.app.navigate('settings');page.select_section('ssmp');self.qt.processEvents()
        self.assertTrue(page.ssmp_enabled.isVisible());self.assertFalse(page.subtitle_languages.isVisible())
        page.select_section('media');self.qt.processEvents()
        self.assertTrue(page.subtitle_languages.isVisible());self.assertFalse(page.ssmp_inbox.isVisible())


if __name__=='__main__':unittest.main()
