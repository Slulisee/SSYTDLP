"""Exercise the packaged GUI with isolated settings; no downloads or user state."""
from pathlib import Path
import json
import os
import subprocess
import tempfile


root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as directory:
    report = Path(directory) / 'smoke.json'
    program = root / 'dist/SSYTDLP' / ('SSYTDLP.exe' if os.name == 'nt' else 'SSYTDLP')
    subprocess.run([str(program), '--smoke-test', str(report)], check=True, timeout=60)
    result = json.loads(report.read_text('utf-8'))
    assert result['mapped'] and len(result['extras']) == 6, result
    assert result['watermark'] == 'made by Slulisee', result
    assert result['lyric_provider'] == 'Lrclib', result
    assert result['queue_page'] and result['queue_model'] == 'EntryModel', result
    assert result['thumbnail_cache'] == 'ThumbnailCache' and len(result['themes']) == 16, result
    assert result['metadata_plugin'] and result['cookie_mode']=='none' and result['staged_links']=='pending', result
    from version import APP_VERSION
    assert result['app_version']==APP_VERSION and result['app_updates'], result
    print('FROZEN GUI PASS: window mapped, six toggles, provider, branding, cookie settings, staged links and real nightly metadata plugin loaded')
