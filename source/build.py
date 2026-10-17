"""Run on the target OS: Windows EXE, macOS .app, Linux executable."""
from pathlib import Path
import os
import platform
import shutil
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    destination = root / 'dist'
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir', '--name', 'SSMD', '--distpath', str(destination), '--workpath', str(root / 'build'), '--specpath', str(root / 'build')]
    if sys.platform == 'win32':
        args += ['--icon', str(root / 'source/app.ico')]
    if sys.platform == 'darwin':
        args += ['--osx-bundle-identifier', 'app.slulisee.ssmd']
    args += [str(root / 'source/app.py')]
    env = os.environ.copy()
    if sys.platform == 'win32':
        # Dependency scanning must resolve Windows' own ICU runtime, rather
        # than an incompatible DLL from an unrelated PDF/media tool on PATH.
        windows = Path(env.get('SystemRoot', 'C:/Windows'))
        paths = [Path(sys.executable).parent, Path(sys.base_prefix), windows / 'System32', windows]
        env['PATH'] = os.pathsep.join(str(path) for path in paths if path.is_dir())
    subprocess.run(args, check=True, env=env)
    target = destination / 'SSMD.app/Contents/MacOS' if sys.platform == 'darwin' else destination / 'SSMD'
    shutil.copytree(root / 'source/plugin_bundle', target / 'plugin_bundle', dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(root / 'tools', target / 'tools', dirs_exist_ok=True)
    shutil.copytree(root / 'licenses', target / 'licenses', dirs_exist_ok=True)
    for name in ('README.md', 'CROSS-PLATFORM.md', 'DISCLAIMER.md', 'LICENSE', 'LICENSE.txt', 'THIRD_PARTY.md', 'APPEARANCE.md', 'CHANGELOG.md', 'SSMP-INTEGRATION.md'):
        if (root / name).exists():
            shutil.copy2(root / name, target / name)
    if (root / 'docs').is_dir():
        shutil.copytree(root / 'docs', target / 'docs', dirs_exist_ok=True)
    print('Built for ' + platform.system() + ' ' + platform.machine() + ': ' + str(destination))


if __name__ == '__main__':
    main()
