"""Regression coverage for navigation, large playlists and real HTTP thumbnails."""
from collections import Counter
from io import BytesIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtGui import QTransform
from PySide6.QtTest import QTest

import test_desktop as support
from test_desktop import fixture
from queue_model import MediaEntry, MediaSource, QueueRecord
from thumbnails import ThumbnailCache
from ui_widgets import icon


class QueueViewTests(unittest.TestCase):
    setUpClass=classmethod(support.DesktopTests.setUpClass.__func__)
    setUp=support.DesktopTests.setUp
    tearDown=support.DesktopTests.tearDown
    until=support.DesktopTests.until
    def test_queue_navigation_opens_all_playlist_entries_and_searches(self):
        first=QueueRecord(fixture(),[1,3])
        large=MediaSource('https://example.org/playlist','Large playlist',True,
            [MediaEntry(i,f'Track {i:05d}','Artist',123,f'https://example.org/covers/{i}.png') for i in range(1,5001)])
        second=QueueRecord(large,list(range(1,5001)))
        loader=patch.object(self.app.thumbnails,'get',return_value=None)
        requests=loader.start();self.addCleanup(loader.stop)
        self.app.records=[first,second];self.app.refresh_queue()
        QTest.mouseClick(self.app.nav['queue'],Qt.MouseButton.LeftButton);self.qt.processEvents()
        page=self.app.queue_page
        self.assertIs(self.app.pages.currentWidget(),page)
        self.assertTrue(self.app.nav['queue'].isChecked())
        self.assertEqual(page.model.rowCount(),5003)
        self.assertEqual(page.proxy.rowCount(),5003)
        self.assertIsNone(page.table.indexWidget(page.proxy.index(0,2)))
        page.sources.setCurrentIndex(2);self.assertEqual(page.proxy.rowCount(),5000)
        page.search.setText('Track 05000');self.assertEqual(page.proxy.rowCount(),1)
        self.assertEqual(page.proxy.data(page.proxy.index(0,3)),'Track 05000')
        page.search.clear();page.table.scrollToBottom();self.qt.processEvents()
        self.assertGreater(page.table.verticalScrollBar().value(),0)
        self.assertLess(len(self.app.thumbnails.pending),65)
        self.assertLess(len({call.args[0] for call in requests.call_args_list if call.args[0]}),150)
        self.assertEqual(self.app.records[1].selected,list(range(1,5001)))

    def test_queue_selection_editor_saves_the_correct_playlist(self):
        first=QueueRecord(fixture(),[1]);second=QueueRecord(fixture(),[3])
        self.app.records=[first,second];self.app.refresh_queue();self.app.navigate('queue')
        page=self.app.queue_page;page.sources.setCurrentIndex(2);page.table.selectRow(0)
        QTest.mouseClick(page.edit,Qt.MouseButton.LeftButton);self.qt.processEvents()
        dialog=self.app.selection_dialog;self.assertEqual(dialog.selected,{3})
        dialog.change_all('none');dialog.checks[1].setChecked(True);dialog.accept_selection();self.qt.processEvents()
        self.assertEqual(first.selected,[1]);self.assertEqual(second.selected,[1])
        self.assertEqual(self.app.store.load()[1].selected,[1])
        self.assertEqual(page.proxy.data(page.proxy.index(0,0),Qt.ItemDataRole.CheckStateRole),Qt.CheckState.Checked)
        self.assertEqual(page.proxy.data(page.proxy.index(1,7)),self.app.t('unavailable'))
        self.assertEqual(page.proxy.data(page.proxy.index(2,7)),self.app.t('queue_not_selected'))
        # A destroyed preview's buttons must not break later theme changes.
        QTest.qWait(20);self.qt.processEvents();self.app.choose_theme('carbon')
        self.assertIs(self.app.pages.currentWidget(),page)

    def test_queue_stays_browsable_while_download_controls_are_locked(self):
        record=QueueRecord(fixture(),[1,3]);self.app.records=[record];self.app.refresh_queue();self.app.navigate('queue')
        page=self.app.queue_page;page.table.selectRow(0)
        self.app.set_operation('download');self.app.events.put(('item','One'));self.app.events.put(('progress',{'total_bytes':100,'downloaded_bytes':62}))
        self.app.poll();self.qt.processEvents()
        self.assertFalse(page.edit.isEnabled());self.assertFalse(page.download.isEnabled());self.assertTrue(page.cancel.isEnabled())
        self.assertEqual(page.progress.value(),62);self.assertTrue(page.current.isVisible());self.assertEqual(page.current.text(),'One')
        page.search.setText('Three');self.assertEqual(page.proxy.rowCount(),1)
        self.app.set_operation('idle');self.assertTrue(page.download.isEnabled())

    def test_queue_empty_filter_and_translations(self):
        self.app.navigate('queue');page=self.app.queue_page
        self.assertEqual(page.proxy.rowCount(),0);self.assertFalse(page.download.isEnabled())
        self.app.records=[QueueRecord(fixture(),[1])];self.app.refresh_queue()
        page.search.setText('no matching title');self.assertTrue(page.empty.isVisible())
        self.assertEqual(page.empty.text(),self.app.t('queue_no_matches'))
        for language in ('en','de','es','fr'):
            self.app.language=language;self.app.apply_appearance()
            self.app.resize(900,680);self.qt.processEvents()
            self.assertEqual(page.sources.itemText(0),self.app.t('queue_all_sources'))
            self.assertEqual(page.model.headerData(7,Qt.Orientation.Horizontal),self.app.t('queue_source_status'))
            for button in (page.options,page.download,page.cancel):
                self.assertTrue(page.rect().contains(button.mapTo(page,button.rect().center())),language)

    def test_metadata_images_load_share_cache_and_fail_without_blocking(self):
        png=BytesIO();Image.new('RGB',(96,54),'#f27135').save(png,'PNG');payload=png.getvalue();requests=Counter()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                requests[self.path]+=1
                self.send_response(200);self.end_headers();self.wfile.write(payload if self.path=='/cover' else b'not an image')
            def log_message(self,*_):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
        try:
            base=f'http://127.0.0.1:{server.server_port}'
            source=MediaSource(base+'/media','Metadata title',False,[MediaEntry(1,'Metadata title',thumbnail=base+'/cover')])
            self.app.records=[QueueRecord(source,[1])];self.app.refresh_queue()
            self.app.tree.scrollToTop();self.qt.processEvents()
            self.until(lambda:self.app.thumbnails.get(base+'/cover') is not None)
            pixmap=self.app.thumbnails.get(base+'/cover')
            self.assertEqual(pixmap.toImage().pixelColor(20,20).name(),'#f27135')
            self.assertEqual(self.app.tree.cellWidget(0,2).url,base+'/cover')
            self.app.navigate('queue');self.qt.processEvents()
            image=self.app.queue_page.proxy.data(self.app.queue_page.proxy.index(0,2),Qt.ItemDataRole.DecorationRole)
            self.assertFalse(image.isNull())
            self.app.show_selection(source);self.qt.processEvents()
            self.assertEqual(self.app.selection_dialog.thumbnail.url,base+'/cover')
            self.app.selection_dialog.reject();self.qt.processEvents();self.app.choose_theme('sakura')
            self.assertEqual(requests['/cover'],1)
            self.app.thumbnails.get(base+'/broken');self.until(lambda:base+'/broken' in self.app.thumbnails.cache,timeout=12)
            for _ in range(5):self.assertIsNone(self.app.thumbnails.get(base+'/broken'))
            self.assertEqual(requests['/broken'],1)
            self.app.thumbnails.get('file:///etc/passwd');self.assertNotIn('file:///etc/passwd',self.app.thumbnails.pending)
            cache=ThumbnailCache(self.app,limit=2)
            for i in range(4):cache.complete(str(i),payload)
            self.assertEqual(list(cache.cache),['2','3']);cache.close()
        finally:server.shutdown();server.server_close()

    def test_settings_gear_renders_centered_and_symmetric_at_ui_sizes(self):
        for size in (19,23,29):
            image=icon('settings','#ffffff',size).pixmap(size,size).toImage()
            rotated=image.transformed(QTransform().rotate(90))
            differences=[abs(image.pixelColor(x,y).alpha()-rotated.pixelColor(x,y).alpha()) for x in range(image.width()) for y in range(image.height())]
            self.assertLess(sum(differences)/len(differences),3)
            self.assertEqual(image.pixelColor(image.width()//2,image.height()//2).alpha(),0)


if __name__=='__main__':unittest.main()
