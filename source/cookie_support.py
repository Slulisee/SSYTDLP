"""Explicit cookie sources. Imported jars are session-only, never preferences."""
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import http.cookiejar
import os
import re
import tempfile
import warnings

BROWSERS = ('firefox', 'chrome', 'edge', 'brave', 'chromium', 'opera', 'safari', 'vivaldi', 'whale')


@dataclass(frozen=True)
class CookieSource:
    mode: str = 'none'
    browser: str = 'firefox'
    content: str = field(default='', repr=False)

    def __post_init__(self):
        if self.mode not in ('none', 'browser', 'file') or self.browser not in BROWSERS:
            raise ValueError('Invalid cookie source.')
        if self.mode == 'file' and not self.content:
            raise ValueError('Import a Netscape cookies.txt file first.')


def import_cookies(path):
    path = Path(path)
    if path.stat().st_size > 10 * 1024 * 1024:
        raise ValueError('Cookie file exceeds 10 MB.')
    content = path.read_text('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    if content.splitlines()[0:1] not in (['# Netscape HTTP Cookie File'], ['# HTTP Cookie File']):
        raise ValueError('Choose a Netscape cookies.txt export, not a JSON file.')
    # Parse without exposing file contents or cookie values in exception messages.
    jar = http.cookiejar.MozillaCookieJar()
    import io
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            jar._really_load(io.StringIO(content), str(path), True, True)
    except Exception:
        raise ValueError('Invalid Netscape cookie file. Export it again using the guide.') from None
    if not list(jar):
        raise ValueError('The cookie export contains no cookies.')
    return CookieSource('file', content=content)


@contextmanager
def cookie_args(source=None):
    source = source or CookieSource()
    if source.mode == 'browser':
        yield ['--cookies-from-browser', source.browser]
    elif source.mode == 'file':
        # yt-dlp writes its cookie jar back. Always give it a disposable copy.
        with tempfile.TemporaryDirectory(prefix='ssytdlp-cookies-') as directory:
            path = Path(directory) / 'cookies.txt'
            with path.open('w', encoding='utf-8', newline=None) as stream:
                os.chmod(path, 0o600)
                stream.write(source.content)
            yield ['--cookies', str(path)]
    else:
        yield []


def redact(message):
    return re.sub(r'(?im)((?:cookie|authorization|set-cookie)\s*:)\s*[^\r\n]+', r'\1 [redacted]', str(message))
