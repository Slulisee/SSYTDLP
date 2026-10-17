"""A small, manual app updater inside Settings."""
from pathlib import Path
import sys
import threading

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QGridLayout, QProgressBar

import app_updates
from platform_support import open_folder
from ui_widgets import Card, text_label
from version import APP_VERSION


class UpdateCard(Card):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.release = None
        self.downloaded = None
        self.cancelled = threading.Event()
        self.status_key = 'app_version'
        self.status_values = {'version': APP_VERSION}
        app.heading(self.body, 'app_updates', 'refresh', 'app_update_hint')
        self.body.addWidget(text_label('SSYTDLP ' + APP_VERSION, 'heading'))
        self.status = text_label('', 'muted', True)
        self.body.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.hide()
        self.body.addWidget(self.progress)
        controls = self.controls = QGridLayout()
        self.check_button = app.make_button('app_check', 'refresh', self.check, primary=True)
        self.download_button = app.make_button('app_download', 'download', self.download)
        self.install_button = app.make_button('app_install' if self.installable() else 'app_show_download', 'folder', self.install)
        self.notes_button = app.make_button('app_release_notes', 'info', self.notes)
        self.cancel_button = app.make_button('cancel', 'close', self.cancelled.set)
        for i, button in enumerate((self.check_button, self.download_button, self.install_button, self.notes_button, self.cancel_button)):
            controls.addWidget(button, i // 2, i % 2)
        self.body.addLayout(controls)
        self.translate()
        self.sync_state()

    def installable(self):
        return app_updates.can_install(self.app.home, frozen=getattr(sys, 'frozen', False))

    def set_status(self, key, **values):
        self.status_key, self.status_values = key, values
        self.translate()

    def translate(self):
        self.status.setText(self.app.t(self.status_key, **self.status_values))

    def sync_state(self):
        idle = self.app.operation == 'idle'
        self.check_button.setEnabled(idle)
        self.download_button.setVisible(bool(self.release and self.release.newer and self.release.asset and not self.downloaded))
        self.download_button.setEnabled(idle)
        self.install_button.setVisible(bool(self.downloaded))
        self.install_button.setEnabled(idle)
        self.notes_button.setEnabled(idle)
        self.cancel_button.setVisible(self.app.operation == 'app_download')
        self.cancel_button.setEnabled(not self.cancelled.is_set())
        visible = [self.check_button, self.notes_button]
        if self.release and self.release.newer and self.release.asset and not self.downloaded:
            visible.append(self.download_button)
        if self.downloaded:visible.append(self.install_button)
        if self.app.operation == 'app_download':visible.append(self.cancel_button)
        for button in (self.check_button,self.notes_button,self.download_button,self.install_button,self.cancel_button):
            self.controls.removeWidget(button)
        for index,button in enumerate(visible):self.controls.addWidget(button,index//2,index%2)

    def check(self):
        if self.app.operation != 'idle':
            return
        self.app.set_operation('app_check')
        self.set_status('app_checking')
        def worker():
            try:
                value = app_updates.check_release(lightweight=self.installable() and app_updates.has_engines(self.app.home))
                self.app.events.put(('app_release', value))
            except Exception as exc:
                self.app.events.put(('app_update_error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def download(self):
        if self.app.operation != 'idle' or not self.release or not self.release.asset:
            return
        self.cancelled.clear()
        self.app.set_operation('app_download')
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.show()
        self.set_status('app_downloading', percent=0)
        asset = self.release.asset
        def worker():
            try:
                value = app_updates.download_release(asset, self.app.settings_path.parent / 'updates' / self.release.version,
                    lambda count, total: self.app.events.put(('app_update_progress', round(count * 100 / total))), self.cancelled)
                self.app.events.put(('app_downloaded', value))
            except app_updates.UpdateCancelled:
                self.app.events.put(('app_update_cancelled', None))
            except Exception as exc:
                self.app.events.put(('app_update_error', str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def receive(self, kind, value):
        if kind == 'app_update_progress':
            self.progress.setValue(value)
            self.set_status('app_downloading', percent=value)
            return
        self.app.set_operation('idle')
        self.progress.hide()
        if kind == 'app_release':
            self.release, self.downloaded = value, None
            if not value.newer:
                self.set_status('app_up_to_date', version=APP_VERSION)
            elif value.asset:
                self.set_status('app_available', version=value.version, size=f'{value.asset.size / 1048576:.1f}')
            else:
                self.set_status('app_preparing', version=value.version)
        elif kind == 'app_downloaded':
            self.downloaded = Path(value)
            self.set_status('app_verified' if self.installable() else 'app_archive_ready')
        elif kind == 'app_update_cancelled':
            self.set_status('app_update_cancelled')
        else:
            self.set_status('app_update_failed', error=value)
        self.sync_state()

    def install(self):
        if self.app.operation != 'idle' or not self.downloaded:
            return
        try:
            if self.installable():
                self.app.persist()
                app_updates.launch_installer(self.downloaded, self.app.home, self.release.asset)
                self.app.close()
            else:
                open_folder(self.downloaded.parent)
        except Exception as exc:
            self.set_status('app_update_failed', error=str(exc))

    def notes(self):
        QDesktopServices.openUrl(QUrl(self.release.page if self.release else app_updates.RELEASES + '/latest'))
