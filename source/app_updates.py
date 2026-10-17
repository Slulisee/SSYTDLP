"""Manual updates from this project's published, stable GitHub releases."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os
import platform
import re
import subprocess
from urllib.request import Request, urlopen

from version import APP_VERSION

REPOSITORY = 'Slulisee/SSYTDLP'
RELEASES = f'https://github.com/{REPOSITORY}/releases'
LATEST_API = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
MUTEX_NAME = 'Local\\Slulisee.SSYTDLP.Application'
MAX_PACKAGE = 1024 * 1024 * 1024


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r'v?\d{1,5}\.\d{1,5}\.\d{1,5}', value):
        raise ValueError('Invalid stable app version')
    return tuple(map(int, value.removeprefix('v').split('.')))


def release_url(tag, name):
    version_tuple(tag)
    if not re.fullmatch(r'SSYTDLP-[A-Za-z0-9_.-]+', name):
        raise ValueError('Invalid release filename')
    return f'{RELEASES}/download/{tag}/{name}'


def read_url(url, limit=2 * 1024 * 1024):
    with urlopen(Request(url, headers={'User-Agent': f'SSYTDLP/{APP_VERSION}', 'Accept': 'application/vnd.github+json' if url == LATEST_API else 'application/octet-stream'}), timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Update response is too large')
    return data


@dataclass(frozen=True)
class Asset:
    name: str
    url: str
    size: int
    sha256: str
    checksum_url: str


@dataclass(frozen=True)
class Release:
    version: str
    page: str
    newer: bool
    asset: Asset | None


def can_install(home, system=None, frozen=False):
    home = Path(home)
    return (system or platform.system()) == 'Windows' and frozen and (home / 'SSYTDLP.exe').is_file()


def has_engines(home):
    return all((Path(home) / 'tools' / name).is_file() for name in ('yt-dlp.exe', 'ffmpeg.exe', 'ffprobe.exe', 'deno.exe', 'engines.json'))


def parse_release(data, current=APP_VERSION, system=None, machine=None, lightweight=False):
    tag = data['tag_name']
    newer = version_tuple(tag) > version_tuple(current)
    if data.get('draft') or data.get('prerelease'):
        raise ValueError('Only published stable releases are supported')
    page = f'{RELEASES}/tag/{tag}'
    if data.get('html_url') != page:
        raise ValueError('Unexpected release repository')
    system, machine = system or platform.system(), (machine or platform.machine()).lower()
    assets = {a.get('name'): a for a in data.get('assets', []) if isinstance(a, dict)}
    if system == 'Windows' and machine in ('amd64', 'x86_64'):
        names = (['SSYTDLP-Windows-AMD64-Update.exe'] if lightweight else []) + ['SSYTDLP-Windows-AMD64-Setup.exe']
    elif system == 'Darwin' and machine in ('arm64', 'aarch64'):
        names = ['SSYTDLP-Darwin-arm64.tar.gz']
    elif system == 'Linux' and machine in ('amd64', 'x86_64'):
        names = ['SSYTDLP-Linux-x86_64.tar.gz']
    else:
        names = []
    selected = None
    for name in names:
        asset = assets.get(name)
        if not asset:
            continue
        url = release_url(tag, name)
        if asset.get('browser_download_url') != url:
            raise ValueError('Unexpected update download URL')
        size = asset.get('size')
        if not isinstance(size, int) or not 0 < size <= MAX_PACKAGE:
            raise ValueError('Invalid update size')
        digest = asset.get('digest') or ''
        sha = digest[7:] if re.fullmatch(r'sha256:[a-fA-F0-9]{64}', digest) else ''
        checksum = assets.get(name + '.sha256', {})
        checksum_url = release_url(tag, name + '.sha256') if checksum.get('browser_download_url') == release_url(tag, name + '.sha256') else ''
        if not sha and not checksum_url:
            continue  # Publication may still be uploading assets; allow a later check.
        selected = Asset(name, url, size, sha.lower(), checksum_url)
        break
    return Release(tag.removeprefix('v'), page, newer, selected)


def check_release(**kwargs):
    return parse_release(json.loads(read_url(LATEST_API)), **kwargs)


def expected_checksum(asset):
    if asset.sha256:
        return asset.sha256
    text = read_url(asset.checksum_url, 4096).decode('ascii').strip()
    match = re.fullmatch(r'([a-fA-F0-9]{64})\s+\*?' + re.escape(asset.name), text)
    if not match:
        raise ValueError('Invalid update checksum')
    return match[1].lower()


class UpdateCancelled(Exception):
    pass


def download_release(asset, directory, progress=lambda *_: None, cancelled=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    expected = expected_checksum(asset)
    target = directory / asset.name
    temporary = target.with_suffix(target.suffix + '.part')
    count = 0
    digest = hashlib.sha256()
    try:
        with urlopen(Request(asset.url, headers={'User-Agent': f'SSYTDLP/{APP_VERSION}'}), timeout=30) as response, temporary.open('wb') as output:
            while True:
                if cancelled is not None and cancelled.is_set():
                    raise UpdateCancelled()
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > asset.size or count > MAX_PACKAGE:
                    raise ValueError('Update download exceeds its published size')
                output.write(chunk)
                digest.update(chunk)
                progress(count, asset.size)
        if count != asset.size or digest.hexdigest() != expected:
            raise ValueError('Update checksum or size does not match; check again and retry')
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def launch_installer(path, home, asset):
    path, home = Path(path).resolve(), Path(home).resolve()
    if platform.system() != 'Windows' or path.name != asset.name or path.suffix != '.exe':
        raise ValueError('Not a Windows app installer')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_checksum(asset):
        raise ValueError('Installer changed after download')
    if not (home / 'SSYTDLP.exe').is_file():
        raise ValueError('App installation folder is missing')
    # NSIS requires /D last and without quotes, even when its path has spaces.
    # This is a native CreateProcess command line; no shell interprets it.
    command = subprocess.list2cmdline([str(path)]) + ' /D=' + str(home)
    return subprocess.Popen(command, executable=str(path), cwd=str(path.parent), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def hold_application_mutex():
    """An installer must wait until *all* running app instances have exited."""
    if os.name != 'nt':
        return None
    import ctypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    kernel.CreateMutexW.restype = ctypes.c_void_p
    handle = kernel.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle  # The process owns the handle until exit, including Qt shutdown.
