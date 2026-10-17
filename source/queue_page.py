"""Full-height, virtualized view of every entry inside the staged sources."""
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSize, QSortFilterProxyModel, Qt
from PySide6.QtGui import QColor, QIcon
from PySide6.QtWidgets import (QAbstractItemView, QHBoxLayout, QHeaderView, QLineEdit,
    QProgressBar, QTableView, QVBoxLayout, QWidget)

from qt_dialogs import duration_text
from ui_widgets import Card, Combo, icon, text_label


class EntryModel(QAbstractTableModel):
    keys=('selected','#','thumbnail','title','queue_source','channel','duration','queue_source_status')

    def __init__(self,app):
        super().__init__(app)
        self.app=app;self.rows=[];self.structure=();self.selections={}
        app.thumbnails.ready.connect(self.thumbnail_ready)

    def refresh(self):
        self.selections={record.id:set(record.selected) for record in self.app.records}
        rows=[(record,entry) for record in self.app.records for entry in (record.source.entries or [None])]
        structure=tuple((record.id,id(entry)) for record,entry in rows)
        if structure!=self.structure:
            self.beginResetModel();self.rows=rows;self.structure=structure;self.endResetModel()
        elif rows:
            self.dataChanged.emit(self.index(0,0),self.index(len(rows)-1,len(self.keys)-1))

    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.rows)
    def columnCount(self,parent=QModelIndex()):return len(self.keys)

    def headerData(self,section,orientation,role=Qt.ItemDataRole.DisplayRole):
        if role==Qt.ItemDataRole.DisplayRole and orientation==Qt.Orientation.Horizontal:
            return '#' if section==1 else self.app.t(self.keys[section])

    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():return None
        record,entry=self.rows[index.row()];col=index.column()
        if entry is None:
            if role==Qt.ItemDataRole.DisplayRole:
                return ('','','',record.source.url,self.app.t('pending'),'','',self.app.t(record.status))[col]
            if role==Qt.ItemDataRole.UserRole:return record.id
            if role==Qt.ItemDataRole.ToolTipRole:return record.source.url
            if role==Qt.ItemDataRole.ForegroundRole:return QColor(self.app.colors['muted'])
            return None
        selected=entry.index in self.selections[record.id]
        if role==Qt.ItemDataRole.CheckStateRole and col==0:
            return Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked
        if role==Qt.ItemDataRole.DisplayRole:
            status='unavailable' if not entry.available else 'queue_not_selected' if not selected else record.status
            return ('',str(entry.index),'',entry.title,record.source.title,entry.channel,duration_text(entry.duration),self.app.t(status))[col]
        if role==Qt.ItemDataRole.DecorationRole and col==2:
            pixmap=self.app.thumbnails.get(entry.thumbnail)
            return QIcon(pixmap) if pixmap is not None else icon('music' if record.source.kind=='catalog' else 'image',self.app.colors['muted'],25)
        if role==Qt.ItemDataRole.ForegroundRole and (not entry.available or not selected):return QColor(self.app.colors['muted'])
        if role==Qt.ItemDataRole.ToolTipRole:
            return '\n'.join(filter(None,(entry.title,entry.channel,entry.album,record.source.title,entry.url)))
        if role==Qt.ItemDataRole.UserRole:return record.id

    def thumbnail_ready(self,url):
        # Only the thumbnail column repaints; scroll position/selection remain stable.
        if self.rows:self.dataChanged.emit(self.index(0,2),self.index(len(self.rows)-1,2),[Qt.ItemDataRole.DecorationRole])


class EntryFilter(QSortFilterProxyModel):
    def __init__(self,parent=None):
        super().__init__(parent);self.source_id='';self.query=''

    def filterAcceptsRow(self,row,parent):
        record,entry=self.sourceModel().rows[row]
        return (not self.source_id or record.id==self.source_id) and (not self.query or self.query in ' '.join((entry.title,entry.channel,entry.album,record.source.title) if entry else (record.source.url,record.source.title)).casefold())

    def update_filter(self,source_id,query):
        self.beginFilterChange();self.source_id=source_id or '';self.query=query.strip().casefold();self.endFilterChange()


class QueuePage(QWidget):
    def __init__(self,app):
        super().__init__();self.app=app
        layout=QVBoxLayout(self);layout.setContentsMargins(22,20,22,20);layout.setSpacing(14)
        card=Card(app);app.heading(card.body,'queue','queue','queue_detail_hint');layout.addWidget(card,1)
        filters=QHBoxLayout();self.sources=Combo(app);self.sources.setMinimumWidth(170);self.sources.setMaximumWidth(330)
        self.sources.setSizeAdjustPolicy(self.sources.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.sources.setMinimumContentsLength(14);self.sources.setAccessibleName(app.t('queue_source'))
        self.search=QLineEdit();self.search.setClearButtonEnabled(True);self.search.setPlaceholderText(app.t('queue_search'))
        self.search.setAccessibleName(app.t('queue_search'));filters.addWidget(self.sources,1);filters.addWidget(self.search,2);card.body.addLayout(filters)
        actions=QHBoxLayout();self.count=text_label('','muted');actions.addWidget(self.count,1)
        self.edit=app.make_button('edit','edit',self.edit_current);self.options=app.make_button('queue_options','settings',lambda:app.navigate('downloader'))
        self.remove=app.make_button('remove','trash',self.remove_current)
        actions.addWidget(self.edit);actions.addWidget(self.remove);card.body.addLayout(actions)
        staged=QHBoxLayout()
        self.add=app.make_button('bulk_links','plus',app.bulk_add)
        self.fetch=app.make_button('fetch_links','refresh',lambda:app.resolve_links(),primary=True)
        staged.addWidget(self.add);staged.addStretch();staged.addWidget(self.fetch);card.body.addLayout(staged)
        self.model=EntryModel(app);self.proxy=EntryFilter(self);self.proxy.setSourceModel(self.model)
        self.table=QTableView();self.table.setModel(self.proxy);self.table.setIconSize(QSize(82,46))
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().hide();self.table.verticalHeader().setDefaultSectionSize(58)
        self.table.setShowGrid(False);self.table.setWordWrap(False);self.table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        for col,width in ((0,78),(1,47),(2,100),(4,170),(5,145),(6,80),(7,128)):self.table.setColumnWidth(col,width)
        self.table.horizontalHeader().setMinimumSectionSize(35)
        self.table.selectionModel().selectionChanged.connect(self.selection_changed)
        self.table.doubleClicked.connect(lambda *_:self.edit_current())
        card.body.addWidget(self.table,1)
        self.empty=text_label('','muted',True);card.body.addWidget(self.empty)
        self.current=text_label('','muted',True);card.body.addWidget(self.current)
        self.progress=QProgressBar();self.progress.setTextVisible(False);card.body.addWidget(self.progress)
        self.state=text_label('','muted',True);card.body.addWidget(self.state)
        footer=QHBoxLayout();footer.addWidget(self.options);footer.addStretch()
        self.download=app.make_button('download','download',app.start,primary=True)
        self.cancel=app.make_button('cancel','close',app.cancel);footer.addWidget(self.download);footer.addWidget(self.cancel)
        card.body.addLayout(footer)
        self.sources.currentIndexChanged.connect(self.filter_changed);self.search.textChanged.connect(self.filter_changed)

    def refresh(self):
        current=self.sources.currentData();signature=tuple((r.id,r.source.title,len(r.source.entries)) for r in self.app.records)
        if signature!=getattr(self,'source_signature',None):
            self.source_signature=signature;self.sources.blockSignals(True);self.sources.clear()
            self.sources.addItem(self.app.t('queue_all_sources'),'')
            for record in self.app.records:self.sources.addItem(f'{record.source.title} ({len(record.source.entries)})',record.id)
            self.sources.setCurrentIndex(max(0,self.sources.findData(current)));self.sources.blockSignals(False)
        self.model.refresh();self.filter_changed();self.sync_state()

    def translate(self):
        self.sources.setItemText(0,self.app.t('queue_all_sources'));self.sources.setAccessibleName(self.app.t('queue_source'))
        self.search.setPlaceholderText(self.app.t('queue_search'));self.search.setAccessibleName(self.app.t('queue_search'))
        self.model.headerDataChanged.emit(Qt.Orientation.Horizontal,0,len(self.model.keys)-1)

    def filter_changed(self,*_):
        self.proxy.update_filter(self.sources.currentData(),self.search.text())
        self.count.setText(self.app.t('queue_entry_count',visible=self.proxy.rowCount(),total=self.model.rowCount(),selected=sum(len(r.selected) for r in self.app.records)))
        self.empty.setText(self.app.t('empty_queue_hint' if not self.model.rows else 'queue_no_matches'))
        self.empty.setVisible(not self.proxy.rowCount());self.selection_changed()

    def current_record(self):
        index=self.table.currentIndex()
        if index.isValid():return self.proxy.data(index,Qt.ItemDataRole.UserRole)

    def selection_changed(self,*_):
        record=next((r for r in self.app.records if r.id==self.current_record()),None)
        self.edit.setEnabled(self.app.operation=='idle' and record is not None and record.source.kind!='pending')
        self.remove.setEnabled(self.app.operation=='idle' and record is not None)

    def remove_current(self):
        if self.app.operation=='idle':
            record_id=self.current_record()
            self.app.records=[r for r in self.app.records if r.id!=record_id]
            self.app.refresh_queue();self.app.persist()

    def edit_current(self):
        record_id=self.current_record()
        if record_id:self.app.edit_record(record_id)

    def sync_state(self):
        idle=self.app.operation=='idle';self.selection_changed()
        self.add.setEnabled(idle);self.fetch.setEnabled(idle and any(r.source.kind=='pending' for r in self.app.records))
        self.download.setEnabled(idle and any(r.status!='completed' for r in self.app.records))
        self.cancel.setEnabled(self.app.cancel_button.isEnabled())
        self.current.setText(self.app.current_text);self.current.setVisible(not self.app.current.isHidden())
        self.progress.setRange(self.app.progress.minimum(),self.app.progress.maximum());self.progress.setValue(self.app.progress.value())
        self.progress.setVisible(self.app.operation!='idle')
        self.state.setText(self.app.status.text());self.state.setVisible(self.app.status_key!='ready')

    def resizeEvent(self,event):
        super().resizeEvent(event)
        for col in (4,5):self.table.setColumnHidden(col,self.width()<1000)
