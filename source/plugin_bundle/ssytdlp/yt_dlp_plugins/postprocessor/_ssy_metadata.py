"""Shared, standard-library-only normalization used before naming and tagging."""
from pathlib import Path
import re
import unicodedata


def key(value):
    return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())


def artists(value):
    # Structured lists preserve names containing commas. Flat extractor credits
    # use comma/semicolon/feat separators; don't split ordinary '&' band names.
    values = value if isinstance(value, (list, tuple)) else re.split(r'\s*[,;]\s*|\s+(?:feat\.?|ft\.?|featuring)\s+', str(value or ''), flags=re.I)
    result, seen = [], set()
    for name in values:
        name = ' '.join(unicodedata.normalize('NFKC', str(name)).split()).strip(' ,;')
        identity = key(name)
        if identity and identity not in seen and identity not in ('na', 'none', 'unknown artist'):
            result.append(name); seen.add(identity)
    return result


def folder_name(value):
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', value).strip(' .') or 'Unknown artist'
    value = value.encode('utf-8')[:70].decode('utf-8', 'ignore').rstrip(' .')
    if re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(?:\..*)?', value, re.I):
        value = '_' + value
    return value


def normalize_info(info, root=None, prefer_flat=False):
    # Prefer an extractor's structured credits, falling back to the flat tag.
    credit = artists(info.get('artist') if prefer_flat else info.get('artists') or info.get('artist'))
    if not info.get('artists') and key(info.get('artist')) in (key(info.get('uploader')), key(info.get('creator'))):
        credit = artists(re.sub(r'(?:\s*-\s*Topic|VEVO)$', '', str(info.get('artist') or ''), flags=re.I))
    if not credit:
        fallback = info.get('creator') or info.get('uploader') or 'Unknown artist'
        fallback = re.sub(r'(?:\s*-\s*Topic|VEVO)$', '', str(fallback), flags=re.I).strip()
        credit = [fallback or 'Unknown artist']
    album_credit = artists(info.get('album_artist') if prefer_flat else info.get('album_artists') or info.get('album_artist'))
    if key(info.get('album_artist')) == key(info.get('artist')) and credit:
        album_credit = credit
    # Earlier releases filled album_artist with the full artist string. Its
    # primary credit remains stable across repeated and featured performers.
    primary = (album_credit or credit)[0]
    info['artists'] = credit
    info['artist'] = ', '.join(credit)
    info['album_artist'] = primary
    info['album'] = info.get('album') or info.get('playlist_title') or 'Singles'
    name = folder_name(primary)
    if root:
        try:
            existing = sorted((p.name for p in Path(root).iterdir() if p.is_dir() and key(p.name) == key(name)))
            if existing:
                name = existing[0]
        except OSError:
            pass
    info['folder_artist'] = name
    return info
