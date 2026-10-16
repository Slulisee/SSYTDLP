"""Exercise the packaged GUI with isolated settings; no downloads or user state."""
from pathlib import Path
import json
import os
import subprocess
import tempfile


root = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory() as directory:
    report = Path(directory) / 'smoke.json'
    program = root / 'dist' / ('SSYTDLP.exe' if os.name == 'nt' else 'SSYTDLP')
    subprocess.run([str(program), '--smoke-test', str(report)], check=True, timeout=60)
    result = json.loads(report.read_text('utf-8'))
    assert result['mapped'] and len(result['extras']) == 6, result
    assert result['watermark'] == 'made by Slulisee', result
    assert result['lyric_provider'] == 'Lrclib', result
    print('FROZEN GUI PASS: window mapped, six toggles, provider and branding loaded')
