"""Conservative LRCLIB matching using syncedlyrics' community provider and Mutagen."""
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import unicodedata

from syncedlyrics.providers.lrclib import Lrclib
from plugin_bundle.ssytdlp.yt_dlp_plugins.postprocessor._ssy_metadata import artists


def normalized(text):
    return ' '.join(re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKC', str(text or '')).casefold()).split())


def clean_title(text):
    text = re.sub(r'\s*[\[(](?:official[^\])]*|lyrics?[^\])]*|[48]k[^\])]*|hd|hq|audio|visuali[sz]er)[\])]', '', str(text), flags=re.I)
    text = re.sub(r'\s*[\[(](?:feat\.?|ft\.?|featuring)\s+[^\])]+[\])]', '', text, flags=re.I)
    text = re.split(r'\s+(?:feat\.?|ft\.?|featuring)\s+', text, maxsplit=1, flags=re.I)[0]
    return text.strip()


def identity(info):
    title = info.get('track') or info.get('title') or ''
    artist = info.get('artist') or ''
    if title in ('NA', 'None'):
        title = info.get('title') or ''
    parts = re.split(r'\s+[-–—]\s+', title, maxsplit=1)
    if len(parts) == 2 and (not artist or normalized(artist) in ('unknown artist', 'na') or normalized(artist) == normalized(info.get('uploader')) or normalized(parts[0]) == normalized((artists(artist) or [''])[0])):
        artist, title = parts
    artist = re.sub(r'(?:\s*-\s*Topic|VEVO)$', '', str(artist), flags=re.I).strip()
    return clean_title(title), ', '.join(artists(artist))


def valid_lyrics(plain, synced):
    plain = str(plain or '').strip()
    synced = str(synced or '').strip()
    plain_ok = len(plain) >= 24 and len([line for line in plain.splitlines() if line.strip()]) >= 2
    timed = re.findall(r'\[(\d{1,3}):(\d{2})(?:[.:]\d+)?\]', synced)
    synced_ok = len(synced) >= 40 and len(timed) >= 2 and any(int(m) * 60 + int(s) >= 10 for m, s in timed)
    return plain if plain_ok else '', synced if synced_ok else ''


@dataclass
class LyricsResult:
    id: int
    plain: str
    synced: str
    source: str


class LyricsFinder:
    def __init__(self):
        self.provider = Lrclib()
        self.provider.session.headers.update({'User-Agent': 'SSMD/3.0 (personal desktop lyrics client)'})
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        self.provider.session.mount('https://lrclib.net/', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=.5, status_forcelist=[429, 500, 502, 503, 504], respect_retry_after_header=False)))

    def find(self, info, cancelled=None):
        title, artist = identity(info)
        if not title or not artist or normalized(artist) in ('unknown artist', 'na', 'none'):
            return None
        duration = info.get('duration')
        duration = duration if isinstance(duration, (int, float)) and duration > 0 else None
        primary = artists(artist)[0]
        params = {'track_name': title, 'artist_name': artist}
        if duration:
            params['duration'] = duration
        if info.get('album'):
            params['album_name'] = info['album']
        queries = [('get', params), ('search', {'track_name': title, 'artist_name': artist})]
        if primary != artist:
            queries.append(('search', {'track_name': title, 'artist_name': primary}))
        queries.append(('search', {'q': primary + ' ' + title}))
        good = []
        for endpoint, query in queries:
            if cancelled is not None and cancelled.is_set():
                return None
            try:
                response = self.provider.session.get('https://lrclib.net/api/' + endpoint, params=query, timeout=(5, 12))
                response.raise_for_status()
                data = response.json()
                candidates = [data] if isinstance(data, dict) else data if isinstance(data, list) else []
                good = [item for item in candidates if self.accept(item, title, artist, duration)]
                if good:
                    break
            except Exception:
                # A missing exact signature or provider outage must not block
                # independent search fallbacks or fail an otherwise valid file.
                continue
        if not good:
            return None
        best = min(good, key=lambda item: (0 if item.get('syncedLyrics') else 1, abs(float(item.get('duration') or 0) - (duration or 0))))
        if cancelled is not None and cancelled.is_set():
            return None
        plain, synced = valid_lyrics(best.get('plainLyrics'), best.get('syncedLyrics'))
        if not plain and synced:
            plain = re.sub(r'\[[^\]]+\]', '', synced).strip()
        return LyricsResult(int(best['id']), plain, synced, f'https://lrclib.net/api/get/{best["id"]}') if plain or synced else None

    @staticmethod
    def accept(item, title, artist, duration):
        if not isinstance(item, dict) or item.get('instrumental'):
            return False
        if SequenceMatcher(None, normalized(title), normalized(clean_title(item.get('trackName') or ''))).ratio() < .90:
            return False
        wanted = artists(artist)
        found = artists(item.get('artistName'))
        if not wanted or not found or SequenceMatcher(None, normalized(wanted[0]), normalized(found[0])).ratio() < .90:
            return False
        # Keep remixes, live takes and tempo edits from matching the original.
        versions = lambda value: set(re.findall(r'\b(?:live|remix|slowed|sped|acoustic|instrumental|nightcore)\b', normalized(value)))
        if versions(title) != versions(item.get('trackName')):
            return False
        if duration and (not isinstance(item.get('duration'), (int, float)) or abs(item['duration'] - duration) > max(8, duration * .04)):
            return False
        plain, synced = valid_lyrics(item.get('plainLyrics'), item.get('syncedLyrics'))
        if plain and len(plain) < 80 and not synced:
            # Short indie songs are useful records too, but demand an exact
            # title/primary artist and a matching known runtime.
            if not duration or normalized(title) != normalized(clean_title(item.get('trackName') or '')) or normalized(wanted[0]) != normalized(found[0]):
                return False
        return bool(plain or synced)


def write_new(path, text):
    if path.exists():
        return
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(text, encoding='utf-8')
    os.replace(temporary, path)


def embed_lyrics(path, result):
    import mutagen
    from mutagen.id3 import ID3, USLT
    from mutagen.mp4 import MP4
    temporary = path.with_name(path.stem + '.ssytdlp-tags' + path.suffix)
    try:
        shutil.copy2(path, temporary)
        media = mutagen.File(temporary)
        if media is None:
            return False
        if media.tags is None:
            media.add_tags()
        if isinstance(media.tags, ID3):
            if media.tags.getall('USLT'):
                return True
            media.tags.add(USLT(encoding=3, lang='und', desc='', text=result.plain))
        elif isinstance(media, MP4):
            if media.tags.get('\xa9lyr'):
                return True
            media.tags['\xa9lyr'] = [result.plain]
        else:
            if media.tags.get('lyrics'):
                return True
            media.tags['lyrics'] = [result.plain]
            if result.synced:
                media.tags['syncedlyrics'] = [result.synced]
        media.save()
        os.replace(temporary, path)
        return True
    finally:
        temporary.unlink(missing_ok=True)


def add_lyrics(path, info, embed=True, emit=lambda *_: None, cancelled=None):
    path = Path(path)
    try:
        result = LyricsFinder().find(info, cancelled)
        if cancelled is not None and cancelled.is_set():
            return
        if result is None:
            emit('log', '[Lyrics] No confident lyrics match found; media download is complete.')
            return
        if result.synced:
            write_new(path.with_suffix('.lrc'), result.synced + '\n')
        if result.plain:
            write_new(path.with_suffix('.lyrics.txt'), result.plain + '\n')
        write_new(path.with_suffix('.lyrics.json'), json.dumps({'provider': 'LRCLIB via syncedlyrics', 'record_id': result.id, 'source': result.source, 'synced': bool(result.synced), 'plain_sha256': hashlib.sha256(result.plain.encode()).hexdigest()}, indent=2))
        embedded = embed_lyrics(path, result) if embed else False
        emit('log', f'[Lyrics] Saved lyrics for {path.name}; synced={bool(result.synced)}; embedded={embedded}; LRCLIB id={result.id}')
    except Exception as exc:
        emit('log', f'[Lyrics] Lyrics enrichment did not finish: {exc}. The media file was retained.')
