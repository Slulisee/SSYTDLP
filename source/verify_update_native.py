"""Real bundled-engine regression using generated audio and a loopback server.

No user cookies, accounts, media or settings are read. Requires prepared tools.
"""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
import hashlib
import json
import os
import subprocess
import tempfile
import threading

import engine
from platform_support import tool_path
from cookie_support import import_cookies
from plugin_bundle.ssytdlp.yt_dlp_plugins.postprocessor._ssy_metadata import normalize_info


def main():
    root=Path(__file__).resolve().parent.parent;tools=root/'tools';seen=[]
    with tempfile.TemporaryDirectory(prefix='ssytdlp-native-') as directory:
        base=Path(directory);audio=base/'input.wav'
        subprocess.run([str(tool_path(tools,'ffmpeg')),'-hide_banner','-loglevel','error','-f','lavfi','-i','sine=frequency=440:duration=2',str(audio)],check=True,**engine.process_kwargs())
        data=audio.read_bytes()
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                seen.append(self.headers.get('Cookie',''))
                self.send_response(200);self.send_header('Content-Type','audio/wav');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            url=f'http://127.0.0.1:{server.server_port}/song.wav'
            cookie=base/'original.txt';cookie.write_text('# Netscape HTTP Cookie File\n127.0.0.1\tFALSE\t/\tFALSE\t0\tsession\tsynthetic-native-cookie\n')
            before=hashlib.sha256(cookie.read_bytes()).hexdigest()
            media=base/'library';media.mkdir();(media/'s0rrow').mkdir()
            real_build=engine.build_args
            for number,artist in enumerate(['s0rrow, s0rrow, s0rrow','s0rrow, Friend, s0rrow']):
                info=base/f'info{number}.json'
                info.write_text(json.dumps(dict(id=f'fixture{number}',title=f'Original fixture {number}',artist=artist,album='Fixture Album',duration=2,url=url,ext='wav',extractor='generic',webpage_url=url)),encoding='utf-8')
                options=engine.Options(url,str(media),preset='MP3 audio · 320 kbps',cover=False,skip_existing=False,cookies=import_cookies(cookie))
                def args(*a):
                    result=real_build(*a);result[-2:-2]=['--load-info-json',str(info)];return result
                events=[]
                with patch('engine.build_args',side_effect=args):
                    engine.Download(tools,lambda *x:events.append(x)).run(options)
                final=next(v for k,v in reversed(events) if k=='done')
                if final['status']!='success':raise AssertionError(events)
            files=sorted(media.rglob('*.mp3'));assert len(files)==2,files
            from mutagen.easyid3 import EasyID3
            tags=[EasyID3(path) for path in files]
            assert all(path.parent==media/'s0rrow'/'Fixture Album' for path in files),files
            assert tags[0]['artist']==['s0rrow'],tags[0]
            assert tags[1]['artist']==['s0rrow, Friend'],tags[1]
            assert all(tag['albumartist']==['s0rrow'] for tag in tags),tags
            assert seen and all('synthetic-native-cookie' in value for value in seen),seen
            assert hashlib.sha256(cookie.read_bytes()).hexdigest()==before
            print('NATIVE PASS: two real MP3 conversions; normalized credits and shared primary folder; imported cookie delivered; original export unchanged.')
        finally:
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
