from pathlib import Path
import hashlib
import platform
import tarfile
import zipfile
import shutil

root = Path(__file__).resolve().parent.parent
dist = root / 'dist'
name = 'SSMD-' + platform.system() + '-' + platform.machine()
output = root / 'native-artifacts'
output.mkdir(exist_ok=True)
if platform.system() == 'Windows':
    target = output / (name + '.zip')
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in dist.rglob('*'):
            if path.is_file():
                archive.write(path, path.relative_to(dist))
else:
    target = output / (name + '.tar.gz')
    with tarfile.open(target, 'w:gz') as archive:
        for path in dist.iterdir():
            if platform.system() == 'Darwin' and path.name == 'SSMD':
                continue
            archive.add(path, arcname=path.name)
target.with_suffix(target.suffix + '.sha256').write_text(
    hashlib.sha256(target.read_bytes()).hexdigest() + '  ' + target.name + '\n', encoding='utf-8')
print(target)
# v1.3.0's updater requires the old exact asset names and repository URL.
if platform.system() != 'Windows':
    legacy = target.with_name(target.name.replace('SSMD-', 'SSYTDLP-', 1))
    shutil.copy2(target, legacy)
    legacy.with_suffix(legacy.suffix + '.sha256').write_text(
        hashlib.sha256(legacy.read_bytes()).hexdigest() + '  ' + legacy.name + '\n', encoding='utf-8')
