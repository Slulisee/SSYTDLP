"""Copy legacy user state once; keep the old app usable for rollback."""
from pathlib import Path
import json
import os
import shutil
import tempfile

from platform_support import config_directory

FILES = ('settings.json', 'queue.json', 'queue.bak', 'wallpaper.png')


def migrate_data(destination, legacy):
    destination, legacy = Path(destination), Path(legacy)
    if destination.exists() or not legacy.is_dir():
        return destination
    if not any((legacy / name).is_file() for name in FILES):
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Rename the complete staging directory, so interruption leaves the original
    # intact and no half-migrated SSMD directory can be mistaken for user state.
    with tempfile.TemporaryDirectory(prefix='.ssmd-migration-', dir=destination.parent) as temporary:
        stage = Path(temporary) / 'data'
        stage.mkdir()
        for name in FILES:
            if (legacy / name).is_file():shutil.copy2(legacy / name, stage / name)
        settings = stage / 'settings.json'
        if settings.is_file():
            try:
                values = json.loads(settings.read_text('utf-8'))
                wallpaper = Path(values.get('wallpaper', ''))
                if wallpaper.resolve() == (legacy / 'wallpaper.png').resolve() and (stage / 'wallpaper.png').is_file():
                    values['wallpaper'] = str(destination / 'wallpaper.png')
                    settings.write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding='utf-8')
            except (ValueError, TypeError, AttributeError):
                pass  # Leave recovery of an existing malformed settings file to the loader.
        try:os.rename(stage, destination)
        except FileExistsError:pass  # Another starting instance completed migration first.
    return destination


def user_data_directory():
    destination = config_directory()
    legacy = config_directory(product='SSYTDLP')
    try:return migrate_data(destination, legacy)
    except OSError:
        # A failed copy must not hide a working legacy queue or damage its files.
        if (legacy / 'settings.json').is_file() or (legacy / 'queue.json').is_file():return legacy
        raise
