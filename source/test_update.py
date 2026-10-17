"""Behavior regressions for cookies, staged links, sorting and indie lyrics."""
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch
import json
import tempfile
import unittest

from cookie_support import CookieSource, cookie_args, import_cookies, redact
from queue_model import QueueStore, ResolveBatch, stage_links, link_key, QueueRecord, normalize_preview
from plugin_bundle.ssytdlp.yt_dlp_plugins.postprocessor._ssy_metadata import normalize_info, artists
from lyrics import LyricsFinder

COOKIE = '# Netscape HTTP Cookie File\n.example.com\tTRUE\t/\tFALSE\t0\tsession\tsynthetic-session-value\n'


class UpdateTests(unittest.TestCase):
    def test_cookie_copy_cleanup_on_success_failure_and_original_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory)/'export.txt'; original.write_text(COOKIE)
            source = import_cookies(original)
            self.assertNotIn('synthetic-session-value', repr(source))
            for fail in (False, True):
                try:
                    with cookie_args(source) as args:
                        jar = Path(args[1]); self.assertTrue(jar.is_file())
                        self.assertEqual(jar.read_text(), COOKIE)
                        jar.write_text('changed by engine')
                        if fail: raise InterruptedError('cancel fixture')
                except InterruptedError: pass
                self.assertFalse(jar.parent.exists())
            self.assertEqual(original.read_text(), COOKIE)
            original.write_text('{"cookies":[]}')
            with self.assertRaises(ValueError): import_cookies(original)
        with cookie_args(CookieSource('browser','firefox')) as args:
            self.assertEqual(args,['--cookies-from-browser','firefox'])
        self.assertEqual(redact('Cookie: session=secret'),'Cookie: [redacted]')

    def test_staging_is_atomic_deduplicated_persistent_and_has_no_network(self):
        records=stage_links('https://youtu.be/abcdefghijk?si=one\nhttps://youtube.com/watch?v=abcdefghijk&si=two\nhttps://youtube.com/playlist?list=PLexample')
        self.assertEqual(len(records),2)
        self.assertEqual(stage_links(records[0].source.url,records),[])
        with self.assertRaises(ValueError): stage_links('https://example.com/a\n--exec=anything',records)
        with tempfile.TemporaryDirectory() as directory:
            store=QueueStore(Path(directory)/'queue.json')
            records[0].status='fetching';store.save(records)
            restored=store.load();self.assertEqual(len(restored),2)
            self.assertEqual(restored[0].status,'pending')
            self.assertEqual(restored[0].selected,[])
            resolved=QueueRecord(normalize_preview('https://example.com/ready',{'title':'Ready'}),[1])
            store.save([records[0],resolved,records[1]])
            payload=json.loads(store.path.read_text('utf-8'))
            self.assertEqual([item['source']['title'] for item in payload['items']],['Ready'])
            self.assertEqual(len(payload['pending_items']),2)
            self.assertEqual([r.id for r in store.load()],[records[0].id,resolved.id,records[1].id])

    def test_resolve_continues_after_failure_without_selection_dialogs(self):
        records=stage_links('https://example.com/one\nhttps://example.com/two')
        previews=[];events=[]
        class Preview:
            def __init__(self,*args):previews.append(args)
            def fetch(self,url):
                if url.endswith('one'):raise ValueError('missing source')
                return {'_type':'playlist','title':'Two','entries':[{'title':'Track A'},{'title':'[Private video]'}]}
            def cancel(self):pass
        source=CookieSource('browser','firefox')
        job=ResolveBatch(Path('.'),lambda *event:events.append(event),source,Preview)
        job.run(records)
        self.assertEqual(len(previews),2);self.assertIs(previews[0][2],source)
        self.assertEqual([v['status'] for k,v in events if k=='queue_status'],['fetching','fetch_error','fetching'])
        resolved=next(v['source'] for k,v in events if k=='resolved')
        self.assertEqual([e.index for e in resolved.entries if e.available],[1])
        self.assertEqual(events[-1],('resolve_done',{'resolved':1,'errors':1,'cancelled':False}))

    def test_resolve_cancel_keeps_remaining_links_unfetched(self):
        records=stage_links('https://example.com/a https://example.com/b');events=[]
        class Preview:
            def __init__(self,*args):pass
            def fetch(self,url):job.cancel();return {'title':'A'}
            def cancel(self):pass
        job=ResolveBatch(Path('.'),lambda *x:events.append(x),preview_factory=Preview)
        job.run(records)
        self.assertFalse(any(k=='resolved' for k,v in events))
        self.assertTrue(events[-1][1]['cancelled'])

    def test_repeated_artist_credits_and_collaborations_share_primary_folder(self):
        source=normalize_preview('https://example.com/song',{'title':'Song','artist':'Artist, Artist','url':'https://cdn.example.com/temporary','webpage_url':'https://example.com/song'})
        self.assertEqual(source.entries[0].artist,'Artist');self.assertEqual(source.entries[0].url,'https://example.com/song')
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'s0rrow').mkdir()
            for flat in ('s0rrow, s0rrow, s0rrow','S0rrow, she left me today, S0rrow'):
                result=normalize_info({'artist':flat,'album':'Album'},directory)
                self.assertEqual(result['folder_artist'],'s0rrow')
                self.assertEqual(len(artists(result['artist'])),len(set(artists(result['artist']))))
        result=normalize_info({'artists':['Earth, Wind & Fire','Earth, Wind & Fire'],'album_artist':'Various Artists'})
        self.assertEqual(result['artist'],'Earth, Wind & Fire')
        self.assertEqual(result['folder_artist'],'Various Artists')
        result=normalize_info({'artist':'Toby Fox, DJ HASEBE, Toby Fox, DJ HASEBE'})
        self.assertEqual(result['artist'],'Toby Fox, DJ HASEBE');self.assertEqual(result['folder_artist'],'Toby Fox')
        result=normalize_info({'artist':'C418 - Topic','uploader':'C418 - Topic','album_artist':'C418 - Topic'})
        self.assertEqual(result['folder_artist'],'C418')

    def test_indie_primary_artist_fallback_and_short_song_guards(self):
        short='A small original fixture\nAnother quiet fixture line'
        record=dict(id=42,trackName='Small Song',artistName='Indie Artist',duration=49,plainLyrics=short)
        with patch('lyrics.Lrclib') as provider:
            missing=Mock();missing.raise_for_status.side_effect=ValueError('not found')
            empty=Mock(json=lambda:[],raise_for_status=lambda:None)
            found=Mock(json=lambda:[record],raise_for_status=lambda:None)
            provider.return_value.session.get.side_effect=[missing,empty,found]
            result=LyricsFinder().find({'track':'Small Song (Official Audio)','artist':'Indie Artist, Friend, Indie Artist','duration':50})
            self.assertEqual(result.id,42)
            self.assertEqual(provider.return_value.session.get.call_args.kwargs['params']['artist_name'],'Indie Artist')
        self.assertFalse(LyricsFinder.accept(record,'Small Song','Indie Artist',None))
        self.assertFalse(LyricsFinder.accept(record,'Small Song (Live)','Indie Artist',50))
        self.assertFalse(LyricsFinder.accept(record,'Small Song','Other Artist',50))
        cancelled=Event();cancelled.set()
        with patch('lyrics.Lrclib') as provider:
            self.assertIsNone(LyricsFinder().find({'track':'Small Song','artist':'Indie Artist'},cancelled))
            provider.return_value.session.get.assert_not_called()


from test_desktop import DesktopTests
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest


class UpdateDesktopTests(unittest.TestCase):
    setUpClass=classmethod(DesktopTests.setUpClass.__func__)
    setUp=DesktopTests.setUp
    tearDown=DesktopTests.tearDown
    until=DesktopTests.until

    def test_quick_and_bulk_add_dont_fetch_until_requested(self):
        with patch('desktop.Preview') as preview:
            self.app.url_entry.setText('https://example.com/a');self.app.quick_add()
            self.app.url_entry.setText('https://example.com/b');QTest.keyClick(self.app.url_entry,Qt.Key.Key_Return)
            self.assertEqual(len(self.app.records),2);preview.assert_not_called()
        self.app.navigate('queue');self.qt.processEvents()
        self.assertEqual(self.app.queue_page.model.rowCount(),2)
        self.app.bulk_add();dialog=self.app.bulk_dialog
        dialog.links.setPlainText('https://example.com/c\nhttps://example.com/d');dialog.stage()
        self.assertEqual(len(self.app.records),4)
        self.assertIsNone(self.app.selection_dialog)
        self.assertTrue(self.app.queue_page.fetch.isEnabled())

    def test_cookie_contents_not_saved_and_import_is_session_only(self):
        self.app.cookies=CookieSource('file',content=COOKIE);self.app.persist()
        saved=self.path.read_text('utf-8')
        self.assertNotIn('synthetic-session-value',saved);self.assertNotIn('content',saved)
        self.assertEqual(json.loads(saved)['cookie_mode'],'none')
        self.app.cookies=CookieSource('browser','edge');self.app.persist()
        self.assertEqual(json.loads(self.path.read_text())['cookie_browser'],'edge')

    def test_fetch_populates_all_entries_without_preview_popups(self):
        self.app.accept_staged(stage_links('https://example.com/a https://example.com/b'))
        with patch('engine.Preview.fetch',return_value={'_type':'playlist','title':'Example','entries':[{'title':'One'},{'title':'Two'}]}):
            self.app.resolve_links();self.until(lambda:self.app.operation=='idle')
        self.assertEqual(self.app.queue_page.model.rowCount(),4)
        self.assertEqual([r.selected for r in self.app.records],[[1,2],[1,2]])
        self.assertIsNone(self.app.selection_dialog)

    def test_failed_fetch_does_not_start_a_partial_download(self):
        self.app.accept_staged(stage_links('https://example.com/a https://example.com/b'))
        with patch('engine.Preview.fetch',side_effect=[{'title':'One'},ValueError('missing')]),patch('desktop.Batch') as batch:
            self.app.start();self.until(lambda:self.app.operation=='idle')
            batch.assert_not_called()
        self.assertEqual([r.status for r in self.app.records],['queued','fetch_error'])
        self.assertTrue(self.app.queue_page.fetch.isEnabled())

    def test_queue_grows_with_window_and_cookie_settings_fit_all_languages(self):
        self.app.resize(1360,950);self.qt.processEvents();small=self.app.tree.height()
        self.app.resize(1600,1300);self.qt.processEvents();large=self.app.tree.height()
        self.assertGreater(large,small+200)
        for language in ('en','de','es','fr'):
            self.app.language=language;self.app.apply_appearance(False);self.app.resize(900,680)
            self.app.navigate('settings');self.app.settings_page.select_section('cookies');self.qt.processEvents()
            self.assertEqual(self.app.settings_page.horizontalScrollBar().maximum(),0,language)
            self.assertGreaterEqual(self.app.metadata.width(),30)

del DesktopTests
