"""Provision native tools and collect license notices for release packaging."""
from pathlib import Path
from importlib import metadata
import hashlib
import io
import json
import os
import re
import subprocess
import zipfile

from prepare_tools import fetch, prepare


def collect_notices(root):
    for distribution in metadata.distributions():
        name = distribution.metadata.get('Name', 'unknown')
        if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
            continue
        target = root / 'licenses' / 'python-packages' / name
        target.mkdir(parents=True, exist_ok=True)
        (target / 'METADATA.txt').write_text(str(distribution.metadata), encoding='utf-8')
        for index, file in enumerate(distribution.files or []):
            if 'license' in file.name.lower() or 'copying' in file.name.lower():
                path = distribution.locate_file(file)
                if path.is_file():
                    (target / f'{index}-{file.name}').write_bytes(path.read_bytes())


def main():
    root = Path(__file__).resolve().parent.parent
    prepare(root)
    if os.name == 'nt':
        url = 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip'
        checksum = re.search(r'\b[0-9a-fA-F]{64}\b', fetch(url + '.sha256').decode())
        data = fetch(url)
        if not checksum or hashlib.sha256(data).hexdigest() != checksum[0].lower():
            raise ValueError('FFmpeg archive checksum mismatch.')
        manifest_path = root / 'tools/engines.json'
        manifest = json.loads(manifest_path.read_text('utf-8'))
        notices = root / 'licenses/ffmpeg'
        notices.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for name in ('ffmpeg', 'ffprobe'):
                member = next(p for p in archive.namelist() if p.endswith('/bin/' + name + '.exe'))
                output = root / 'tools' / (name + '.exe')
                output.write_bytes(archive.read(member))
                version = subprocess.check_output([str(output), '-version'], text=True).splitlines()[0]
                manifest[name] = {'version': version, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'source': url}
            for member in archive.namelist():
                leaf = Path(member).name
                if leaf.lower() in ('license', 'license.txt', 'readme.txt'):
                    (notices / leaf).write_bytes(archive.read(member))
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    collect_notices(root)


if __name__ == '__main__':
    main()
