"""Playlist preview rendered with the same appearance as the main window."""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from ui_widgets import Card, Check, icon, text_label
from thumbnails import ThumbnailCell


def duration_text(seconds):
    if not isinstance(seconds,(int,float)) or seconds < 0:
        return '—'
    hours, remainder=divmod(int(seconds),3600);minutes,seconds=divmod(remainder,60)
    return f'{hours}:{minutes:02d}:{seconds:02d}' if hours else f'{minutes}:{seconds:02d}'


class SelectionDialog(QDialog):
    def __init__(self,app,source,selected,callback,editing=False):
        super().__init__(app)
        self.app,self.source,self.callback=app,source,callback
        self.selected=set(selected)
        self.checks={}
        self.setWindowTitle(app.t('preview'))
        self.resize(1020,620);self.setMinimumSize(800,480)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        layout=QVBoxLayout(self);layout.setContentsMargins(24,22,24,22);layout.setSpacing(14)
        layout.addWidget(text_label(source.title,'heading',True))
        layout.addWidget(text_label(app.t('source_catalog',provider=source.provider) if source.kind=='catalog' else app.t('select_hint'),'muted',True))
        actions=QHBoxLayout()
        for key,mode in [('select_all','all'),('select_none','none'),('invert','invert')]:
            button=app.make_button(key,command=lambda checked=False,m=mode:self.change_all(m))
            actions.addWidget(button)
        actions.addStretch();self.counter=text_label('','muted');actions.addWidget(self.counter);layout.addLayout(actions)
        middle=QHBoxLayout()
        self.tree=QTableWidget(0,5)
        self.tree.setHorizontalHeaderLabels(['✓','#',app.t('title'),app.t('channel'),app.t('duration')])
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.verticalHeader().hide();self.tree.setShowGrid(False)
        self.tree.horizontalHeader().setSectionResizeMode(2,QHeaderView.ResizeMode.Stretch)
        for col,width in ((0,44),(1,42),(3,145),(4,75)):
            self.tree.setColumnWidth(col,width)
        self.tree.verticalHeader().setDefaultSectionSize(42)
        self.tree.setRowCount(len(source.entries))
        for row,entry in enumerate(source.entries):
            box=QWidget();box_layout=QHBoxLayout(box);box_layout.setContentsMargins(9,0,0,0)
            check=Check('',app,entry.index in self.selected);check.setFixedWidth(31);check.setEnabled(entry.available)
            check.toggled.connect(lambda checked,index=entry.index:self.set_selected(index,checked))
            box_layout.addWidget(check);self.checks[entry.index]=check
            self.tree.setCellWidget(row,0,box)
            for col,text in ((1,str(entry.index)),(2,entry.title),(3,entry.channel if entry.available else app.t('unavailable')),(4,duration_text(entry.duration))):
                item=QTableWidgetItem(text)
                if not entry.available:
                    item.setForeground(QColor(app.colors['muted']))
                self.tree.setItem(row,col,item)
        self.tree.itemSelectionChanged.connect(self.show_details)
        self.tree.cellDoubleClicked.connect(lambda row,col:self.toggle_rows([row]) if col else None)
        space_shortcut=QShortcut(QKeySequence(Qt.Key.Key_Space),self.tree,activated=lambda:self.toggle_rows(sorted({x.row() for x in self.tree.selectedIndexes()})))
        space_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        middle.addWidget(self.tree,1)
        detail=Card(app);detail.setFixedWidth(215);detail.body.setContentsMargins(13,15,13,15)
        self.thumbnail=ThumbnailCell(app,fallback='music' if source.kind=='catalog' else 'image')
        self.thumbnail.setMinimumHeight(155)
        detail.body.addWidget(self.thumbnail);self.detail_title=text_label('','heading',True);detail.body.addWidget(self.detail_title)
        self.detail_channel=text_label('','muted',True);detail.body.addWidget(self.detail_channel);detail.body.addStretch()
        middle.addWidget(detail);layout.addLayout(middle,1)
        footer=QHBoxLayout();footer.addStretch()
        self.accept_button=app.make_button('save_selection' if editing else 'add_queue','plus',self.accept_selection,primary=True)
        footer.addWidget(self.accept_button);footer.addWidget(app.make_button('cancel',command=self.reject));layout.addLayout(footer)
        self.refresh_count();self.tree.selectRow(0)
        self.finished.connect(self.on_finished)

    def set_selected(self,index,checked):
        self.selected.add(index) if checked else self.selected.discard(index)
        self.refresh_count()

    def refresh_count(self):
        self.counter.setText(self.app.t('selection_count',selected=len(self.selected),total=len(self.source.entries)))
        self.accept_button.setEnabled(bool(self.selected))

    def change_all(self,mode):
        available={e.index for e in self.source.entries if e.available}
        self.selected=available if mode=='all' else set() if mode=='none' else available-self.selected
        for index,check in self.checks.items():
            check.blockSignals(True);check.setChecked(index in self.selected);check.blockSignals(False)
        self.refresh_count()

    def toggle_rows(self,rows):
        for row in rows:
            entry=self.source.entries[row]
            if entry.available:
                self.checks[entry.index].toggle()

    def show_details(self):
        row=self.tree.currentRow()
        if row < 0:
            return
        entry=self.source.entries[row]
        self.detail_title.setText(entry.title)
        self.detail_channel.setText(entry.channel+' · '+duration_text(entry.duration))
        self.thumbnail.set_url(entry.thumbnail)

    def accept_selection(self):
        if self.selected:
            self.callback(sorted(self.selected));self.accept()

    def on_finished(self,_result):
        if self.app.selection_dialog is self:
            self.app.selection_dialog=None
        self.deleteLater()
