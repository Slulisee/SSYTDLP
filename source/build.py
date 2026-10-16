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
    args = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--windowed', '--onedir' if sys.platform == 'darwin' else '--onefile', '--name', 'SSYTDLP', '--distpath', str(destination), '--workpath', str(root / 'build'), '--specpath', str(root / 'build')]
    if sys.platform == 'win32':
        args += ['--icon', str(root / 'source/app.ico')]
    if sys.platform == 'darwin':
        args += ['--osx-bundle-identifier', 'app.slulisee.ssytdlp']
    args += [str(root / 'source/app.py')]
    subprocess.run(args, check=True)
    target = destination / 'SSYTDLP.app/Contents/MacOS' if sys.platform == 'darwin' else destination
    shutil.copytree(root / 'tools', target / 'tools', dirs_exist_ok=True)
    for name in ('README.md', 'CROSS-PLATFORM.md', 'DISCLAIMER.md', 'LICENSE', 'THIRD_PARTY.md', 'CHANGELOG.md'):
        if (root / name).exists():
            shutil.copy2(root / name, destination / name)
    for name in ('licenses', 'docs'):
        if (root / name).is_dir():
            shutil.copytree(root / name, destination / name, dirs_exist_ok=True)
    print('Built for ' + platform.system() + ' ' + platform.machine() + ': ' + str(destination))


if __name__ == '__main__':
    main()
