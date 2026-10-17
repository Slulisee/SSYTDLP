"""Real, isolated Windows fresh-install/upgrade/guard/uninstall verification.

Only product registry entries and its Start menu shortcut are touched; their
pre-test values are restored in finally. Installation targets stay under build/.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import time
import zipfile


def sha(path):
    with Path(path).open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    if os.name != 'nt':
        raise SystemExit('Windows only')
    import winreg
    root = Path(__file__).resolve().parent.parent
    work = root / 'build/installer-verification'
    work.mkdir(parents=True, exist_ok=True)
    target = work / 'App with spaces'
    if target.exists():
        raise RuntimeError('Use a fresh build directory for installer verification')
    keys = ['Software\\Slulisee\\SSYTDLP', 'Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\SSYTDLP']
    snapshot = {}
    for key in keys:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
                values = []
                for i in range(winreg.QueryInfoKey(handle)[1]):values.append(winreg.EnumValue(handle, i))
                snapshot[key] = values
        except FileNotFoundError:snapshot[key] = None
    programs = ctypes.create_unicode_buffer(32768)
    if ctypes.windll.shell32.SHGetFolderPathW(None, 2, None, 0, programs):
        raise RuntimeError('Could not locate Start menu')
    shortcut = Path(programs.value) / 'SSYTDLP/SSYTDLP.lnk'
    shortcut_before = shortcut.read_bytes() if shortcut.is_file() else None
    user_data = Path(os.environ['LOCALAPPDATA']) / 'SSYTDLP'
    user_before = {p.name:sha(p) for p in user_data.glob('*') if p.is_file()}
    setup = root / 'native-artifacts/SSYTDLP-Windows-AMD64-Setup.exe'
    update = root / 'native-artifacts/SSYTDLP-Windows-AMD64-Update.exe'
    result = {}

    def run(exe, arguments, expected=0):
        command = subprocess.list2cmdline([str(exe)]) + ' ' + arguments
        process = subprocess.run(command, executable=str(exe), cwd=work, timeout=240)
        if process.returncode != expected:
            raise AssertionError(f'{exe.name}: exit {process.returncode}, expected {expected}')
        return process.returncode

    def smoke(name):
        report = work / (name + '.json')
        process = subprocess.run([str(target/'SSYTDLP.exe'),'--smoke-test',str(report)],timeout=60)
        assert process.returncode == 0
        data=json.loads(report.read_text('utf-8'))
        assert data['mapped'] and data['metadata_plugin']
        return data

    guard = None
    try:
        result['fresh_install_exit'] = run(setup, '/S /D=' + str(target))
        assert (target/'SSYTDLP.exe').is_file() and (target/'Uninstall.exe').is_file()
        assert shortcut.is_file()
        result['fresh_gui'] = smoke('fresh-smoke')['mapped']
        if len(sys.argv)==3 and sys.argv[1]=='--baseline-zip':
            baseline=Path(sys.argv[2]).resolve()
            assert sha(baseline)=='3b9d5ff053ce460c8c91f67d330777bfa028b30f8bbcd015e9f904c5ff307af8'
            with zipfile.ZipFile(baseline) as archive:
                assert archive.testzip() is None
                for info in archive.infolist():
                    relative=Path(info.filename)
                    assert relative.parts[0]=='SSYTDLP' and '..' not in relative.parts
                    destination=target.joinpath(*relative.parts[1:])
                    assert destination.resolve().is_relative_to(target.resolve())
                    if info.is_dir():destination.mkdir(parents=True,exist_ok=True)
                    else:
                        destination.parent.mkdir(parents=True,exist_ok=True)
                        destination.write_bytes(archive.read(info))
            result['baseline_1_2_1_gui']=smoke('baseline-smoke')['mapped']
        from queue_model import QueueStore, stage_links
        records=stage_links('https://example.com/upgrade-retention')
        store=QueueStore(work/'queue.json');store.save(records)
        settings=work/'upgrade-smoke.settings.json'
        settings.write_text(json.dumps(dict(theme='carbon',folder=str(work/'my music'),language='de')),encoding='utf-8')
        engines = {p.name:sha(p) for p in (target/'tools').iterdir() if p.is_file()}
        # Engine manifest content is deliberately changed to prove setup preserves
        # an independently updated nightly instead of overwriting the tool folder.
        marker = target/'tools/engines.json'
        marker_before = marker.read_bytes()
        marker.write_bytes(marker_before + b'\n')
        (target/'README.md').write_text('Previous app file: should be replaced',encoding='utf-8')
        (target/'keep-user-file.txt').write_text('User file: keep on uninstall',encoding='utf-8')
        result['upgrade_exit'] = run(update, '/S /D=' + str(target))
        assert 'Previous app file' not in (target/'README.md').read_text('utf-8')
        assert marker.read_bytes() == marker_before + b'\n'
        assert all(sha(target/'tools'/name)==value for name,value in engines.items() if name!='engines.json')
        result['engines_retained'] = True
        result['upgrade_gui'] = smoke('upgrade-smoke')['mapped']
        saved=json.loads(settings.read_text('utf-8'))
        assert saved['theme']=='carbon' and saved['language']=='de' and saved['folder']==str(work/'my music')
        retained=store.load();assert len(retained)==1 and retained[0].id==records[0].id
        result['queue_theme_language_destination_retained']=True
        empty = work/'not installed'
        result['incomplete_update_exit'] = run(update, '/S /D=' + str(empty), 3)
        assert not (empty/'SSYTDLP.exe').exists()
        ready, stop = work/'mutex-ready', work/'mutex-stop'
        code = "from pathlib import Path; import time; from app_updates import hold_application_mutex; h=hold_application_mutex(); Path(r'"+str(ready)+"').touch();\nwhile not Path(r'"+str(stop)+"').exists(): time.sleep(.05)"
        guard = subprocess.Popen([sys.executable,'-c',code],cwd=root/'source')
        end=time.monotonic()+10
        while not ready.exists() and time.monotonic()<end:time.sleep(.05)
        assert ready.exists()
        app_hash=sha(target/'SSYTDLP.exe')
        result['running_app_guard_exit'] = run(update, '/S /D=' + str(target), 2)
        assert sha(target/'SSYTDLP.exe')==app_hash
        stop.touch();assert guard.wait(10)==0;guard=None
        result['uninstall_exit'] = run(target/'Uninstall.exe', '/S _?=' + str(target))
        assert not (target/'SSYTDLP.exe').exists()
        assert (target/'keep-user-file.txt').read_text('utf-8')=='User file: keep on uninstall'
        assert {p.name:sha(p) for p in user_data.glob('*') if p.is_file()} == user_before
        result['user_files_and_settings_retained'] = True
    finally:
        if guard:
            (work/'mutex-stop').touch();guard.wait(10)
        for key, values in snapshot.items():
            try:winreg.DeleteKey(winreg.HKEY_CURRENT_USER,key)
            except FileNotFoundError:pass
            if values is not None:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key) as handle:
                    for name,value,kind in values:winreg.SetValueEx(handle,name,0,kind,value)
        if shortcut_before is not None:
            shortcut.parent.mkdir(parents=True,exist_ok=True);shortcut.write_bytes(shortcut_before)
        elif shortcut.is_file():shortcut.unlink()
        if shortcut_before is None and shortcut.parent.exists():
            try:shortcut.parent.rmdir()
            except OSError:pass
    report = root / 'native-artifacts/installer-verification.json'
    report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
