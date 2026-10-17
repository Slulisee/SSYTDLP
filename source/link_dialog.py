"""Stage multiple links in one transaction, without fetching previews."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit
from ui_widgets import text_label
from queue_model import stage_links


class BulkDialog(QDialog):
    def __init__(self, app):
        super().__init__(app); self.app = app
        self.setWindowTitle(app.t('bulk_links')); self.resize(650, 420)
        layout = QVBoxLayout(self); layout.setContentsMargins(22,22,22,22); layout.setSpacing(12)
        layout.addWidget(text_label(app.t('bulk_hint'), 'muted', True))
        self.links = QPlainTextEdit(); self.links.setPlaceholderText('https://youtu.be/…\nhttps://www.youtube.com/playlist?list=…')
        self.links.setAccessibleName(app.t('bulk_links')); layout.addWidget(self.links,1)
        self.feedback = text_label('', 'muted', True); layout.addWidget(self.feedback)
        buttons = QHBoxLayout(); buttons.addStretch()
        buttons.addWidget(app.make_button('cancel','close',self.reject))
        buttons.addWidget(app.make_button('quick_add','plus',self.stage,primary=True)); layout.addLayout(buttons)

    def stage(self):
        try:
            records = stage_links(self.links.toPlainText(), self.app.records)
        except ValueError:
            self.feedback.setText(self.app.t('bulk_invalid')); return
        self.app.accept_staged(records)
        self.app.navigate('queue'); self.accept()
