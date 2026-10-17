"""Cookie settings with explicit activation and a local, readable guide."""
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QTextBrowser
from cookie_support import BROWSERS, CookieSource, import_cookies
from ui_widgets import Card, Combo, text_label
from html import escape


class CookieCard(Card):
    def __init__(self, app):
        super().__init__(app); self.app = app
        title = QHBoxLayout(); title.addWidget(app.label('cookies_title','heading',True),1)
        self.info = app.make_button('cookie_info','info',self.guide)
        self.info.setFixedSize(40,40)
        title.addWidget(self.info); self.body.addLayout(title)
        self.body.addWidget(app.label('cookie_help','muted',True))
        self.browser = Combo(app); self.browser.addItems(BROWSERS); self.browser.setCurrentText(app.cookies.browser)
        self.browser.setAccessibleName(app.t('cookie_browser'))
        browsers = QHBoxLayout(); browsers.addWidget(self.browser,1)
        browsers.addWidget(app.make_button('cookie_use_browser','link',self.use_browser)); self.body.addLayout(browsers)
        files = QHBoxLayout(); files.addWidget(app.make_button('cookie_import','folder',self.choose_file))
        files.addWidget(app.make_button('cookie_clear','close',self.clear)); files.addStretch(); self.body.addLayout(files)
        self.state = text_label('','muted',True); self.body.addWidget(self.state); self.sync()

    def sync(self):
        app = self.app
        key = {'none':'cookie_none','browser':'cookie_browser_active','file':'cookie_file_active'}[app.cookies.mode]
        self.state.setText(app.t(key,browser=app.cookies.browser))
        self.info.setText(''); self.info.setAccessibleName(app.t('cookie_info'))
        self.info.setToolTip('<qt>'+escape(app.t('cookie_help'))+'</qt>')
        self.browser.setAccessibleName(app.t('cookie_browser'))

    def use_browser(self):
        self.app.cookies = CookieSource('browser',self.browser.currentText())
        self.sync(); self.app.persist()

    def choose_file(self):
        path,_ = QFileDialog.getOpenFileName(self,self.app.t('cookie_import'),'','Netscape cookies (*.txt);;All files (*)')
        if path:
            try:
                self.app.cookies = import_cookies(path)
                self.sync(); self.app.persist()
            except (ValueError,OSError,UnicodeError):
                QMessageBox.warning(self,self.app.t('cookies_title'),self.app.t('cookie_invalid'))

    def clear(self):
        self.app.cookies = CookieSource(); self.sync(); self.app.persist()

    def guide(self):
        dialog = QDialog(self); dialog.setWindowTitle(self.app.t('cookie_info')); dialog.resize(760,580)
        layout = QVBoxLayout(dialog); browser = QTextBrowser(); browser.setOpenExternalLinks(True)
        path = self.app.home/'docs/COOKIES.md'
        browser.setMarkdown(path.read_text('utf-8') if path.exists() else self.app.t('cookie_help'))
        layout.addWidget(browser); dialog.exec()
