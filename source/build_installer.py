"""Build full setup and smaller app-only Windows upgrade with NSIS 3.x."""
from pathlib import Path
import hashlib
import os
import shutil
import subprocess

from version import APP_VERSION


def compiler():
    candidates = [os.environ.get('NSIS_MAKENSIS'), shutil.which('makensis'),
        str(Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'NSIS/makensis.exe'),
        str(Path(os.environ.get('LOCALAPPDATA', '')) / 'tauri/NSIS/makensis.exe')]
    for value in candidates:
        if value and Path(value).is_file():
            return str(Path(value).resolve())
    raise FileNotFoundError('NSIS 3.x is required. Set NSIS_MAKENSIS to its makensis.exe.')


def quoted(value):
    return str(value).replace('$', '$$').replace('"', '$\\"')


def main():
    root = Path(__file__).resolve().parent.parent
    app = root / 'dist/SSMD'
    if not (app / 'SSMD.exe').is_file():
        raise FileNotFoundError('Build the Windows app first')
    work = root / 'build/installer'
    work.mkdir(parents=True, exist_ok=True)
    output = root / 'native-artifacts'
    output.mkdir(exist_ok=True)
    files = sorted(p for p in app.rglob('*') if p.is_file())
    uninstall = work / 'uninstall.nsh'
    lines = [f'Delete "$INSTDIR\\{quoted(p.relative_to(app))}"' for p in files]
    directories = sorted((p for p in app.rglob('*') if p.is_dir()), key=lambda p: len(p.parts), reverse=True)
    lines += [f'RMDir "$INSTDIR\\{quoted(p.relative_to(app))}"' for p in directories]
    uninstall.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for mode in ('Setup', 'Update'):
        payload = work / (mode + '.nsh')
        lines = []
        current = None
        for p in files:
            relative = p.relative_to(app)
            engine = relative.parts[0] == 'tools'
            if mode == 'Update' and engine:
                continue
            parent = relative.parent
            if parent != current:
                lines += [f'SetOutPath "$INSTDIR\\{quoted(parent)}"', 'SetOverwrite ' + ('off' if engine else 'on')]
                current = parent
            lines.append(f'File "{quoted(p)}"')
        payload.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        target = output / f'SSMD-Windows-AMD64-{mode}.exe'
        args = [compiler(), '/V2', '/DROOT=' + str(root), '/DVERSION=' + APP_VERSION,
            '/DOUTPUT=' + str(target), '/DPAYLOAD=' + str(payload), '/DUNINSTALL_FILES=' + str(uninstall)]
        if mode == 'Update':
            args.append('/DUPDATE_ONLY')
        env = os.environ.copy()
        windows = Path(env.get('SystemRoot', 'C:/Windows'))
        env['PATH'] = os.pathsep.join(map(str, (windows / 'System32', windows)))
        subprocess.run(args + [str(root / 'source/installer.nsi')], check=True, env=env)
        checksum = hashlib.sha256(target.read_bytes()).hexdigest()
        target.with_suffix('.exe.sha256').write_text(checksum + '  ' + target.name + '\n', encoding='ascii')
        legacy = target.with_name(target.name.replace('SSMD-', 'SSYTDLP-', 1))
        shutil.copy2(target, legacy)
        legacy.with_suffix('.exe.sha256').write_text(checksum + '  ' + legacy.name + '\n', encoding='ascii')
        print(f'{target.name}: {target.stat().st_size} bytes; SHA256 {checksum}', flush=True)


if __name__ == '__main__':
    main()
