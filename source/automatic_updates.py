"""Background stable updates, applied only after a normal app close."""
from dataclasses import asdict, replace
from pathlib import Path
import hashlib,json,threading,time
import app_updates
from version import APP_VERSION

def pending_path(directory):return Path(directory)/'updates/pending.json'

def save_pending(directory,release,path):
    path=Path(path).resolve();cache=(Path(directory)/'updates').resolve()
    if not path.is_relative_to(cache):raise ValueError('Update is outside its cache')
    if not release.asset or path.name!=release.asset.name:raise ValueError('Unexpected installer')
    expected=app_updates.expected_checksum(release.asset)
    if path.stat().st_size!=release.asset.size or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError('Installer changed after download')
    release=replace(release,asset=replace(release.asset,sha256=expected))
    target=pending_path(directory);temporary=target.with_suffix('.part')
    temporary.write_text(json.dumps({'release':asdict(release),'path':str(path)},indent=2),encoding='utf-8');temporary.replace(target)

def load_pending(directory,current=APP_VERSION):
    record=json.loads(pending_path(directory).read_text(encoding='utf-8'));release=record['release'];asset=release['asset'];tag='v'+release['version']
    app_updates.version_tuple(tag)
    if app_updates.version_tuple(tag)<=app_updates.version_tuple(current):return None
    expected=app_updates.release_url(tag,asset['name'])
    if release['page']!=app_updates.RELEASES+'/tag/'+tag or asset['url']!=expected or asset['checksum_url'] not in ('',expected+'.sha256'):raise ValueError('Unexpected staged update URL')
    if not isinstance(asset['size'],int) or not 0<asset['size']<=app_updates.MAX_PACKAGE:raise ValueError('Invalid staged update size')
    if asset['name'] not in ('SSMD-Windows-AMD64-Setup.exe','SSMD-Windows-AMD64-Update.exe'):raise ValueError('Unexpected staged installer')
    value=app_updates.Asset(**asset);path=Path(record['path']).resolve()
    if not path.is_relative_to((Path(directory)/'updates').resolve()) or path.name!=value.name:raise ValueError('Invalid staged update path')
    if path.stat().st_size!=value.size or hashlib.sha256(path.read_bytes()).hexdigest()!=app_updates.expected_checksum(value):raise ValueError('Staged installer checksum changed')
    return path,value

class AutomaticUpdater:
    def __init__(self,app,enabled=True):
        self.app=app;self.enabled=enabled;self.running=False;self.cancelled=threading.Event();self.closing=False
        if enabled:
            from PySide6.QtCore import QTimer
            self.timer=QTimer(app);self.timer.timeout.connect(self.check_due);self.timer.start(60000)
            QTimer.singleShot(8000,self.check_due)

    def check_due(self):
        if not self.enabled or self.running or self.closing or not self.app.saved_settings.get('automatic_app_updates',True):return
        if not app_updates.can_install(self.app.home,frozen=True) or self.app.operation!='idle':return
        stamp=self.app.settings_path.parent/'updates/automatic-last-check.txt'
        try:last=float(stamp.read_text(encoding='ascii'))
        except (OSError,ValueError):last=0
        if time.time()-last<86400:return
        self.running=True;self.cancelled.clear()
        self.app.settings_page.update_card.sync_state()
        def worker():
            try:
                release=app_updates.check_release(lightweight=app_updates.has_engines(self.app.home))
                if release.newer and release.asset:
                    path=app_updates.download_release(release.asset,self.app.settings_path.parent/'updates'/release.version,cancelled=self.cancelled)
                    if not self.cancelled.is_set():save_pending(self.app.settings_path.parent,release,path)
                    self.app.events.put(('automatic_app_ready',release.version))
                else:self.app.events.put(('automatic_app_current',None))
                stamp.parent.mkdir(parents=True,exist_ok=True);stamp.write_text(str(time.time()),encoding='ascii')
            except app_updates.UpdateCancelled:self.app.events.put(('automatic_app_current',None))
            except Exception as exc:self.app.events.put(('automatic_app_error',str(exc)))
        threading.Thread(target=worker,daemon=True).start()

    def receive(self,kind,value):
        self.running=False
        card=self.app.settings_page.update_card
        if kind=='automatic_app_ready':card.set_status('app_automatic_ready',version=value)
        elif kind=='automatic_app_error':card.set_status('app_update_failed',error=value)
        card.sync_state()

    def close(self):
        self.closing=True;self.cancelled.set()
        if not self.enabled or not self.app.saved_settings.get('automatic_app_updates',True):return
        try:
            staged=load_pending(self.app.settings_path.parent)
            if staged:app_updates.launch_installer(staged[0],self.app.home,staged[1],silent=True)
        except FileNotFoundError:pass
        except Exception as exc:
            directory=self.app.settings_path.parent/'updates';directory.mkdir(parents=True,exist_ok=True)
            (directory/'last-automatic-error.txt').write_text(str(exc),encoding='utf-8')
