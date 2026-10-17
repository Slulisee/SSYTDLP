"""SSYTDLP's themed Qt view. Downloads continue through the existing engine/queue."""
from __future__ import annotations
from pathlib import Path
import json
import queue
import re
import sys
import threading

from PySide6.QtCore import QEvent, QSize, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPalette, QPixmap, QShortcut
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QColorDialog, QComboBox,
    QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QScrollArea, QSizePolicy,
    QStackedLayout, QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from appearance import import_wallpaper, read_wallpaper
from engine import (APP_NAME, APP_FULL_NAME, PRESETS, Options, Preview, build_args,
                    load_settings, save_settings, update_nightly, validate_url)
from i18n import LANGUAGES, tr
from platform_support import config_directory, open_folder
from queue_model import Batch, ResolveBatch, QueueRecord, QueueStore, normalize_preview, stage_links
from cookie_support import BROWSERS, CookieSource, redact
from cookie_page import CookieCard
from link_dialog import BulkDialog
from qt_dialogs import SelectionDialog
from thumbnails import ThumbnailCache, ThumbnailCell
from queue_page import QueuePage
from themes import COLOR_KEYS, THEMES, appearance_settings, palette, valid_color
from ui_widgets import Background, BrandIcon, Card, Check, Combo, ThemeTile, Wave, icon, stylesheet, text_label


def app_directory():
    return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent.parent


def row(*widgets,spacing=9):
    layout=QHBoxLayout();layout.setSpacing(spacing);layout.setContentsMargins(0,0,0,0)
    for widget in widgets:
        layout.addWidget(widget)
    return layout


def scroll_page(content):
    scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QScrollArea.Shape.NoFrame)
    scroll.setWidget(content)
    return scroll


class App(QMainWindow):
    def __init__(self,settings_path=None,tools=None):
        super().__init__()
        self.home=app_directory();self.tools=Path(tools) if tools else self.home/'tools'
        self.settings_path=Path(settings_path) if settings_path else config_directory()/'settings.json'
        settings=load_settings(self.settings_path)
        if settings_path is None and not self.settings_path.exists():
            settings=load_settings(config_directory().parent/'yt-dlp Simple/settings.json')
        self.saved_settings=settings.copy()
        self.cookies=CookieSource('browser',settings.get('cookie_browser','firefox')) if settings.get('cookie_mode')=='browser' and settings.get('cookie_browser') in BROWSERS else CookieSource()
        self.resolver=None;self.resolve_then_download=False
        self.language=settings.get('language','en')
        if self.language not in LANGUAGES:self.language='en'
        self.theme,self.theme_colors=appearance_settings(settings)
        self.colors=palette(self.theme,self.theme_colors)
        self.wallpaper_path=str(settings.get('wallpaper',''))
        self.store=QueueStore(self.settings_path.with_name('queue.json'))
        self.records=self.store.load();self.events=queue.Queue();self.logs=[]
        self.thumbnails=ThumbnailCache(self)
        self.batch=None;self.preview_job=None;self.selection_dialog=None
        self.operation='idle';self.close_pending=False;self.status_key='ready';self.status_values={}
        self.current_text='';self.bound_labels=[];self.bound_buttons=[];self.icon_labels=[]
        self.editable=[];self.active_page='downloader'
        self.preset=settings.get('preset',next(iter(PRESETS)))
        if self.preset not in PRESETS:self.preset=next(iter(PRESETS))
        self.embed_lyrics=bool(settings.get('embed_lyrics',True))
        self.subtitle_languages=str(settings.get('subtitle_languages','en.*,de.*'))
        self.automatic_subtitles=bool(settings.get('automatic_subtitles',False))
        self.embed_subtitles=bool(settings.get('embed_subtitles',False))
        self.ssmp_enabled=bool(settings.get('ssmp_enabled',False));self.ssmp_inbox=str(settings.get('ssmp_inbox',''))
        self.setWindowTitle(APP_NAME+' - '+APP_FULL_NAME)
        self.setMinimumSize(900,680)
        self.background=Background(self);self.setCentralWidget(self.background)
        outer=QHBoxLayout(self.background);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        self.build_sidebar(outer)
        self.pages=QStackedWidget();outer.addWidget(self.pages,1)
        self.downloader_content=QWidget();self.downloader_content.setObjectName('downloaderContent')
        main=QVBoxLayout(self.downloader_content);main.setContentsMargins(22,20,22,20);main.setSpacing(14)
        self.build_link_card(main)
        self.build_queue_card(main)
        self.build_options_card(main,settings)
        self.build_destination_card(main,settings)
        self.downloader_scroll=scroll_page(self.downloader_content);self.pages.addWidget(self.downloader_scroll)
        self.activity_content=QWidget();activity_layout=QVBoxLayout(self.activity_content);activity_layout.setContentsMargins(24,24,24,24)
        activity=Card(self);activity.body.addWidget(self.label('nav_history','heading'))
        activity.body.addWidget(self.label('activity_hint','muted',True))
        self.log=QPlainTextEdit();self.log.setReadOnly(True);self.log.setPlaceholderText(self.t('no_activity'))
        activity.body.addWidget(self.log,1);activity_layout.addWidget(activity,1)
        self.pages.addWidget(self.activity_content)
        self.settings_page=SettingsPage(self);self.pages.addWidget(self.settings_page)
        self.about_page=self.build_about();self.pages.addWidget(self.about_page)
        self.queue_page=QueuePage(self);self.pages.addWidget(self.queue_page)
        self.apply_appearance(persist=False)
        self.refresh_queue();self.preset_changed();self.set_status('ready');self.set_operation('idle')
        self.poll_timer=QTimer(self);self.poll_timer.timeout.connect(self.poll);self.poll_timer.start(65)
        self.url_entry.returnPressed.connect(self.quick_add)
        QShortcut(QKeySequence('Ctrl+L'),self,activated=lambda:(self.navigate('downloader'),self.url_entry.setFocus(),self.url_entry.selectAll()))
        QShortcut(QKeySequence('Ctrl+,'),self,activated=lambda:self.navigate('settings'))
        delete_shortcut=QShortcut(QKeySequence(Qt.Key.Key_Delete),self.tree,activated=self.remove_selected)
        delete_shortcut.setContext(Qt.ShortcutContext.WidgetShortcut)
        available=QApplication.primaryScreen().availableGeometry()
        self.resize(min(1320,available.width()-60),min(1000,available.height()-65))

    def t(self,key,**values):
        return tr(self.language,key,**values)

    def label(self,key,role='',wrap=False):
        label=text_label(self.t(key),role,wrap)
        self.bound_labels.append((label,key));return label

    def make_button(self,key,icon_name=None,command=None,primary=False,role=None):
        button=QPushButton(self.t(key).replace('&','&&'));button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setProperty('role','primary' if primary else role or '')
        if command:button.clicked.connect(command)
        self.bound_buttons.append((button,key,icon_name,primary,role))
        if icon_name:button.setIcon(icon(icon_name,self.colors['on_accent'] if primary else self.colors['text'],19));button.setIconSize(QSize(19,19))
        return button

    def symbol(self,name,size=28):
        label=QLabel();label.setFixedSize(size+2,size+2)
        label.setPixmap(icon(name,self.colors['icon'],size).pixmap(size,size))
        self.icon_labels.append((label,name,size));return label

    def heading(self,layout,key,icon_name,hint=None):
        heading=QHBoxLayout();heading.setSpacing(13)
        heading.addWidget(self.symbol(icon_name,29))
        column=QVBoxLayout();column.setSpacing(4);column.addWidget(self.label(key,'heading'))
        if hint:column.addWidget(self.label(hint,'muted',True))
        heading.addLayout(column,1);layout.addLayout(heading)
        return heading

    def build_sidebar(self,outer):
        self.sidebar=QWidget();self.sidebar.setProperty('role','sidebar');self.sidebar.setFixedWidth(226)
        side=QVBoxLayout(self.sidebar);side.setContentsMargins(16,24,16,19);side.setSpacing(9)
        brand=QHBoxLayout();brand.setSpacing(11);self.brand_icon=BrandIcon(self)
        brand.addWidget(self.brand_icon)
        texts=QVBoxLayout();texts.setSpacing(1);texts.addWidget(text_label(APP_NAME,'title'))
        subtitle=text_label("Slulisee's Simple yt-dlp\nDownloader",'muted');subtitle.setStyleSheet('font-size: 11px;')
        texts.addWidget(subtitle);brand.addLayout(texts,1);side.addLayout(brand);side.addSpacing(23)
        self.nav={}
        for page,key,symbol in [('downloader','nav_downloader','home'),('queue','nav_queue','queue'),('history','nav_history','clock'),('settings','settings','settings'),('about','nav_about','info')]:
            button=self.make_button(key,symbol,lambda checked=False,p=page:self.navigate(p),role='nav')
            button.setCheckable(True);button.setMinimumHeight(45);button.setIconSize(QSize(23,23));side.addWidget(button);self.nav[page]=button
        side.addStretch()
        self.version_label=text_label(self.read_version(),'muted',True);side.addWidget(self.version_label)
        side.addWidget(text_label('made by Slulisee','muted'))
        outer.addWidget(self.sidebar)

    def build_link_card(self,main):
        self.link_card=Card(self);header=self.heading(self.link_card.body,'link','link','link_hint')
        self.wave=Wave(self);header.addWidget(self.wave)
        self.url_entry=QLineEdit();self.url_entry.setPlaceholderText('https://www.youtube.com/watch?v=…')
        self.url_entry.setClearButtonEnabled(True);self.url_entry.setAccessibleName(self.t('link'))
        self.paste_button=self.make_button('paste','paste',self.paste)
        self.add_button=self.make_button('preview_add','image',self.preview_link)
        self.quick_button=self.make_button('quick_add','plus',self.quick_add,primary=True)
        self.bulk_button=self.make_button('bulk_links','queue',self.bulk_add)
        self.link_card.body.addLayout(row(self.url_entry,self.paste_button,self.quick_button))
        extras=QHBoxLayout();extras.addWidget(self.bulk_button);extras.addStretch();extras.addWidget(self.add_button);self.link_card.body.addLayout(extras)
        self.editable.extend((self.url_entry,self.paste_button,self.add_button,self.quick_button,self.bulk_button));main.addWidget(self.link_card)

    def build_queue_card(self,main):
        self.queue_card=Card(self);header=self.queue_header=QHBoxLayout();header.setSpacing(13);header.addWidget(self.symbol('queue',29))
        headings=QVBoxLayout();headings.setSpacing(3);headings.addWidget(self.label('queue','heading'))
        self.queue_count=text_label('','muted');headings.addWidget(self.queue_count);header.addLayout(headings,1)
        self.edit_button=self.make_button('edit','edit',self.edit_selection)
        self.remove_button=self.make_button('remove','trash',self.remove_selected)
        self.clear_button=self.make_button('clear_done','check',self.clear_completed)
        self.fetch_button=self.make_button('fetch_links','refresh',lambda:self.resolve_links(),primary=True)
        self.queue_actions=QWidget();actions=self.queue_action_layout=QGridLayout(self.queue_actions);actions.setContentsMargins(0,0,0,0);actions.setSpacing(9)
        for index,button in enumerate((self.fetch_button,self.edit_button,self.remove_button,self.clear_button)):actions.addWidget(button,index//2,index%2)
        header.addWidget(self.queue_actions)
        self.queue_card.body.addLayout(header)
        self.tree=QTableWidget(0,6);self.tree.setMinimumHeight(190);self.tree.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.tree.setHorizontalHeaderLabels(['','#',self.t('thumbnail'),self.t('title'),self.t('selected'),self.t('status')])
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.verticalHeader().hide();self.tree.setShowGrid(False);self.tree.verticalHeader().setDefaultSectionSize(57)
        self.tree.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.tree.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)
        for col,width in ((0,40),(1,42),(2,92),(4,90),(5,114)):self.tree.setColumnWidth(col,width)
        self.tree.cellDoubleClicked.connect(lambda *_:self.edit_selection())
        self.tree.itemSelectionChanged.connect(self.selection_state)
        self.table_container=QWidget();table_layout=self.table_stack=QStackedLayout(self.table_container);table_layout.setContentsMargins(0,0,0,0)
        table_layout.setStackingMode(QStackedLayout.StackingMode.StackAll);table_layout.addWidget(self.tree)
        self.empty_overlay=QWidget();self.empty_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        empty=QVBoxLayout(self.empty_overlay);empty.setContentsMargins(0,43,0,0);empty.setSpacing(7);empty.addStretch()
        self.empty_icon=QLabel();self.empty_icon.setProperty('role','empty-icon');self.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter);self.empty_icon.setFixedSize(66,66);empty.addWidget(self.empty_icon,0,Qt.AlignmentFlag.AlignHCenter)
        self.empty_title=self.label('empty_queue','empty-title');self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter);empty.addWidget(self.empty_title)
        empty_hint=self.label('empty_queue_hint','muted');empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter);empty.addWidget(empty_hint);empty.addStretch()
        table_layout.addWidget(self.empty_overlay);self.queue_card.body.addWidget(self.table_container,1)
        self.editable.extend((self.edit_button,self.remove_button,self.clear_button));main.addWidget(self.queue_card,1)

    def build_options_card(self,main,settings):
        self.options_card=Card(self);self.heading(self.options_card.body,'options','settings','options_hint')
        self.preset_box=Combo(self,'music');self.preset_box.setAccessibleName(self.t('options'))
        self.preset_box.addItems([self.t(f'preset_{i}') for i in range(len(PRESETS))])
        self.preset_box.setCurrentIndex(list(PRESETS).index(self.preset))
        self.preset_box.currentIndexChanged.connect(self.preset_changed)
        self.options_card.body.addWidget(self.preset_box)
        self.hint=text_label('','hint',True);hint_row=QHBoxLayout();hint_row.addWidget(self.symbol('info',14));hint_row.addWidget(self.hint,1);self.options_card.body.addLayout(hint_row)
        self.checks_grid=QGridLayout();self.checks_grid.setHorizontalSpacing(20);self.checks_grid.setVerticalSpacing(3)
        self.checks=[];self.check_rows=[]
        for name,key,default,symbol in [('metadata','metadata',True,'music'),('cover','cover',True,'image'),('organize','organize',True,'folder'),('skip_existing','skip',True,'skip'),('lyrics','lyrics',False,'tag'),('subtitles','subtitles',False,'subtitles')]:
            line=QWidget();line_layout=QHBoxLayout(line);line_layout.setContentsMargins(0,0,0,0);line_layout.setSpacing(10)
            check=Check('',self,bool(settings.get(name,default)));check.setFixedWidth(31);check.setAccessibleName(self.t(key))
            line_layout.addWidget(check);line_layout.addWidget(self.symbol(symbol,17))
            label=self.label(key,'',True);label.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
            label.setMinimumHeight(25);line_layout.addWidget(label,1)
            line.setMinimumHeight(30)
            # A label click toggles the same native checkbox, preserving keyboard focus.
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.mousePressEvent=lambda event,c=check:c.click() if c.isEnabled() else None
            check.toggled.connect(self.options_changed)
            setattr(self,name,check);self.checks.append(check);self.check_rows.append(line)
            self.checks_grid.addWidget(line,len(self.check_rows)//2-1 if len(self.check_rows)%2==0 else len(self.check_rows)//2,(len(self.check_rows)-1)%2)
        self.options_card.body.addLayout(self.checks_grid)
        self.options_card.body.addWidget(self.label('fallback','muted',True))
        self.editable.extend(self.checks);self.editable.append(self.preset_box);main.addWidget(self.options_card)

    def build_destination_card(self,main,settings):
        self.destination_card=Card(self);heading=QHBoxLayout();heading.setSpacing(12)
        heading.addWidget(self.symbol('folder',24));heading.addWidget(self.label('save_to','heading'))
        heading.addWidget(self.label('destination_hint','muted',True),1);self.destination_card.body.addLayout(heading)
        self.folder_entry=QLineEdit(str(settings.get('folder',Path.home()/'Downloads')))
        self.folder_decoration=self.folder_entry.addAction(icon('folder',self.colors['muted'],20),QLineEdit.ActionPosition.LeadingPosition)
        self.folder_entry.setAccessibleName(self.t('save_to'))
        self.browse_button=self.make_button('browse','folder',self.browse)
        self.open_button=self.make_button('open_folder','folder',self.open_folder,primary=True)
        self.destination_card.body.addLayout(row(self.folder_entry,self.browse_button,self.open_button))
        actions=self.destination_actions=QHBoxLayout()
        self.download_button=self.make_button('download','download',self.start,primary=True);self.download_button.setMinimumWidth(208)
        self.cancel_button=self.make_button('cancel','close',self.cancel)
        actions.addWidget(self.download_button);actions.addWidget(self.cancel_button);actions.addStretch()
        self.update_button=self.make_button('update','refresh',self.update_engine);actions.addWidget(self.update_button)
        self.destination_card.body.addLayout(actions)
        self.update_footer=QWidget();footer=QHBoxLayout(self.update_footer)
        footer.setContentsMargins(0,0,0,0);footer.addStretch();self.update_footer.hide()
        self.destination_card.body.addWidget(self.update_footer)
        self.progress=QProgressBar();self.progress.setTextVisible(False);self.progress.setRange(0,100);self.progress.hide()
        self.current=text_label('','muted');self.current.hide()
        self.status=text_label('','muted',True)
        self.destination_card.body.addWidget(self.progress);self.destination_card.body.addWidget(self.current);self.destination_card.body.addWidget(self.status)
        self.editable.extend((self.folder_entry,self.browse_button,self.download_button,self.update_button));main.addWidget(self.destination_card)
        self.folder_entry.editingFinished.connect(self.persist)

    def build_about(self):
        content=QWidget();layout=QVBoxLayout(content);layout.setContentsMargins(24,24,24,24)
        card=Card(self);brand=QHBoxLayout();brand.addWidget(BrandIcon(self,64));brand.addSpacing(9)
        texts=QVBoxLayout();texts.addWidget(text_label(APP_NAME,'title'));texts.addWidget(text_label(APP_FULL_NAME,'muted',True));brand.addLayout(texts,1);card.body.addLayout(brand)
        card.body.addWidget(self.label('about_hint','',True));card.body.addWidget(text_label('made by Slulisee','muted'))
        card.body.addWidget(self.label('service_help','',True));card.body.addWidget(self.label('disclaimer','muted',True));layout.addWidget(card);layout.addStretch()
        return scroll_page(content)

    def navigate(self,page):
        self.active_page=page
        self.navigate_checked()
        self.pages.setCurrentIndex({'downloader':0,'queue':4,'history':1,'settings':2,'about':3}[page])
        if page=='downloader':self.downloader_scroll.ensureWidgetVisible(self.link_card)
        elif page=='queue':self.queue_page.refresh()
        elif page=='settings':self.settings_page.reload_media()

    def apply_appearance(self,persist=True):
        from shiboken6 import isValid
        self.bound_buttons=[entry for entry in self.bound_buttons if isValid(entry[0])]
        self.colors=palette(self.theme,self.theme_colors)
        qt_palette=self.palette()
        for role,key in ((QPalette.ColorRole.Window,'bg'),(QPalette.ColorRole.WindowText,'text'),
            (QPalette.ColorRole.Base,'field'),(QPalette.ColorRole.Text,'text'),
            (QPalette.ColorRole.Button,'button'),(QPalette.ColorRole.ButtonText,'text'),
            (QPalette.ColorRole.Highlight,'selected'),(QPalette.ColorRole.HighlightedText,'text'),
            (QPalette.ColorRole.PlaceholderText,'muted'),(QPalette.ColorRole.Link,'accent')):
            qt_palette.setColor(role,QColor(self.colors[key]))
        self.setPalette(qt_palette)
        self.setStyleSheet(stylesheet(self.colors))
        for label,key in self.bound_labels:label.setText(self.t(key))
        for button,key,symbol,primary,role in self.bound_buttons:
            button.setText(self.t(key).replace('&','&&'))
            if symbol:button.setIcon(icon(symbol,self.colors['on_accent'] if primary else self.colors['glow'] if role=='nav' else self.colors['text'],23 if role=='nav' else 19))
        for label,symbol,size in self.icon_labels:label.setPixmap(icon(symbol,self.colors['icon'],size).pixmap(size,size))
        self.empty_icon.setPixmap(icon('download',self.colors['muted'],48).pixmap(48,48))
        self.preset_box.blockSignals(True)
        for i in range(len(PRESETS)):self.preset_box.setItemText(i,self.t(f'preset_{i}'))
        self.preset_box.blockSignals(False)
        self.tree.setHorizontalHeaderLabels(['','#',self.t('thumbnail'),self.t('title'),self.t('selected'),self.t('status')])
        self.log.setPlaceholderText(self.t('no_activity'))
        self.folder_decoration.setIcon(icon('folder',self.colors['muted'],20))
        for check,key in zip(self.checks,('metadata','cover','organize','skip','lyrics','subtitles')):check.setAccessibleName(self.t(key))
        self.setWindowIcon(icon('download',self.colors['accent'],32))
        try:
            image=read_wallpaper(self.wallpaper_path)
            if image is not None:
                from PIL.ImageQt import ImageQt
                self.background.wallpaper=QPixmap.fromImage(ImageQt(image))
            else:self.background.wallpaper=QPixmap()
        except Exception:
            self.wallpaper_path='';self.background.wallpaper=QPixmap()
        self.settings_page.sync_appearance();self.refresh_queue();self.preset_changed()
        self.queue_page.translate()
        self.set_status(self.status_key,**self.status_values)
        self.background.update()
        for widget in self.findChildren(QWidget):widget.update()
        self.navigate_checked()
        self.apply_titlebar()
        if persist:self.persist()

    def navigate_checked(self):
        symbols=dict(downloader='home',queue='queue',history='clock',settings='settings',about='info')
        for key,button in self.nav.items():
            button.setChecked(key==self.active_page)
            button.setIcon(icon(symbols[key],self.colors['icon'] if key==self.active_page else self.colors['muted'],23))

    def apply_titlebar(self):
        if sys.platform=='win32' and QApplication.platformName()=='windows':
            import ctypes
            try:
                dwm=ctypes.WinDLL('dwmapi')
                handle=ctypes.c_void_p(int(self.winId()))
                dark=ctypes.c_int(not self.colors['light'])
                dwm.DwmSetWindowAttribute(handle,20,ctypes.byref(dark),ctypes.sizeof(dark))
                for attribute,key in ((35,'bg'),(36,'text')):
                    rgb=self.colors[key]
                    color=ctypes.c_uint(int(rgb[1:3],16)|(int(rgb[3:5],16)<<8)|(int(rgb[5:7],16)<<16))
                    dwm.DwmSetWindowAttribute(handle,attribute,ctypes.byref(color),ctypes.sizeof(color))
            except (OSError,AttributeError):pass

    def choose_theme(self,key):
        if key not in THEMES:return
        self.theme=key;self.theme_colors={};self.apply_appearance();self.settings_page.feedback.setText(self.t('appearance_saved'))

    def set_custom_color(self,key,value):
        if key in COLOR_KEYS and valid_color(value):
            self.theme_colors[key]=value.lower();self.apply_appearance();return True
        return False

    def read_version(self):
        try:return 'yt-dlp nightly\n'+str(json.loads((self.tools/'engines.json').read_text('utf-8'))['yt-dlp']['version'])
        except (OSError,ValueError,KeyError):return 'yt-dlp nightly'

    def preset_changed(self,_index=None):
        self.preset=list(PRESETS)[max(0,self.preset_box.currentIndex())]
        kind,_,ext=PRESETS[self.preset]
        self.preset_box.leading='image' if kind=='video' else 'music';self.preset_box.update()
        self.hint.setText(self.t('hint_video' if kind=='video' else 'hint_flac' if ext=='flac' else 'hint_audio'))

    def options_changed(self,*_):
        if hasattr(self,'folder_entry'):self.persist()

    def get_options(self):
        return Options('https://example.com',self.folder_entry.text(),self.preset,False,
            self.metadata.isChecked(),self.cover.isChecked(),self.organize.isChecked(),self.skip_existing.isChecked(),
            lyrics=self.lyrics.isChecked(),embed_lyrics=self.embed_lyrics,subtitles=self.subtitles.isChecked(),
            subtitle_languages=self.subtitle_languages,automatic_subtitles=self.automatic_subtitles,
            embed_subtitles=self.embed_subtitles,ssmp_enabled=self.ssmp_enabled,ssmp_inbox=self.ssmp_inbox,cookies=self.cookies)

    def persist(self):
        values=self.saved_settings.copy();values.update(self.get_options().__dict__)
        for key in ('cookies','url','playlist','playlist_items','catalog_title','catalog_artist','catalog_album','catalog_number'):values.pop(key,None)
        values.update(cookie_mode='browser' if self.cookies.mode=='browser' else 'none',cookie_browser=self.cookies.browser)
        values.update(language=self.language,theme=self.theme,theme_colors=self.theme_colors,wallpaper=self.wallpaper_path)
        try:
            save_settings(self.settings_path,values);self.store.save(self.records);self.saved_settings=values
        except OSError as exc:
            self.append_log(str(exc));self.set_status('save_error')

    def selected_record_ids(self):
        return {self.tree.item(row,3).data(Qt.ItemDataRole.UserRole) for row in {x.row() for x in self.tree.selectedIndexes()} if self.tree.item(row,3)}

    def refresh_queue(self):
        selected=self.selected_record_ids()
        self.tree.blockSignals(True);self.tree.setRowCount(len(self.records))
        for row_index,record in enumerate(self.records):
            for col,text in ((1,str(row_index+1)),(3,record.source.title),(4,f'{len(record.selected)} / {len(record.source.entries)}'),(5,self.t(record.status))):
                item=QTableWidgetItem(text);item.setData(Qt.ItemDataRole.UserRole,record.id)
                if col in (1,4,5):item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tree.setItem(row_index,col,item)
            selected_indices=set(record.selected)
            candidates=[e for e in record.source.entries if e.thumbnail and e.index in selected_indices]
            if not candidates:candidates=[e for e in record.source.entries if e.thumbnail]
            thumb=ThumbnailCell(self,candidates[0].thumbnail if candidates else '', 'music' if record.source.kind=='catalog' else 'image')
            self.tree.setCellWidget(row_index,2,thumb)
            mark=QLabel();mark.setAlignment(Qt.AlignmentFlag.AlignCenter);mark.setPixmap(icon('check' if record.status=='completed' else 'clock',self.colors['accent'] if record.status=='completed' else self.colors['muted'],17).pixmap(17,17));self.tree.setCellWidget(row_index,0,mark)
        self.tree.clearSelection()
        from PySide6.QtCore import QItemSelectionModel
        for row_index,record in enumerate(self.records):
            if record.id in selected:self.tree.selectionModel().select(self.tree.model().index(row_index,3),QItemSelectionModel.SelectionFlag.Select|QItemSelectionModel.SelectionFlag.Rows)
        self.tree.blockSignals(False)
        self.empty_overlay.setVisible(not self.records)
        self.table_stack.setCurrentWidget(self.tree if self.records else self.empty_overlay)
        self.queue_count.setText(self.t('queue_count',links=len(self.records),videos=sum(len(r.selected) for r in self.records)))
        self.queue_page.refresh()
        self.selection_state()
        self.queue_page.sync_state()

    def selection_state(self):
        idle=self.operation=='idle';selection=bool(self.selected_record_ids())
        self.edit_button.setEnabled(idle and selection);self.remove_button.setEnabled(idle and selection)
        self.clear_button.setEnabled(idle and any(r.status=='completed' for r in self.records))
        self.fetch_button.setEnabled(idle and any(r.source.kind=='pending' for r in self.records))

    def set_operation(self,operation):
        self.operation=operation
        for widget in self.editable:widget.setEnabled(operation=='idle')
        self.settings_page.media_container.setEnabled(operation=='idle')
        self.settings_page.cookie_card.setEnabled(operation=='idle')
        self.cancel_button.setEnabled(operation in ('preview','download','resolve'))
        self.progress.setVisible(operation!='idle')
        self.selection_state()
        self.queue_page.sync_state()

    def set_status(self,key,**values):
        self.status_key,self.status_values=key,values
        self.status.setText(self.t(key,**values))
        self.status.setVisible(key!='ready')

    def paste(self):
        value=QApplication.clipboard().text().strip()
        if value:self.url_entry.setText(value)
        else:self.set_status('empty_clipboard')

    def browse(self):
        folder=QFileDialog.getExistingDirectory(self,self.t('save_to'),self.folder_entry.text())
        if folder:self.folder_entry.setText(folder);self.persist()

    def open_folder(self):
        try:open_folder(Path(self.folder_entry.text()).expanduser().absolute())
        except OSError as exc:QMessageBox.warning(self,self.t('open_folder'),str(exc))

    def accept_staged(self,records):
        self.records.extend(records);self.refresh_queue();self.persist()
        self.set_status('staged',count=len(records))

    def quick_add(self):
        if self.operation!='idle':return
        try:records=stage_links(self.url_entry.text(),self.records)
        except ValueError:self.set_status('invalid_link');return
        self.accept_staged(records);self.url_entry.clear();self.url_entry.setFocus()

    def bulk_add(self):
        if self.operation=='idle':
            self.bulk_dialog=BulkDialog(self);self.bulk_dialog.show()

    def resolve_links(self,download_after=False):
        if self.operation!='idle':return
        pending=[r for r in self.records if r.source.kind=='pending']
        if not pending:return
        self.resolve_then_download=download_after
        self.navigate('queue');self.set_operation('resolve');self.set_status('fetching');self.progress.setRange(0,0)
        self.resolver=ResolveBatch(self.tools,lambda kind,value:self.events.put((kind,value)),self.cookies)
        threading.Thread(target=self.resolver.run,args=(pending,),daemon=True).start()

    def preview_link(self):
        if self.operation!='idle':return
        try:url=validate_url(self.url_entry.text())
        except ValueError:self.set_status('invalid_link');return
        self.set_operation('preview');self.set_status('preview_loading');self.progress.setRange(0,0)
        job=self.preview_job=Preview(self.tools,lambda *_:None,self.cookies)
        def fetch():
            try:self.events.put(('preview_ok',normalize_preview(url,job.fetch(url))))
            except Exception as exc:self.events.put(('preview_error',str(exc)))
        threading.Thread(target=fetch,daemon=True).start()

    def show_selection(self,source,record=None):
        selected=record.selected if record else [e.index for e in source.entries if e.available]
        def accept(indices):
            if record is not None:record.selected=indices;record.status='queued'
            else:
                if any(r.source.url==source.url and r.selected==indices and r.status!='completed' for r in self.records):self.set_status('duplicate');return
                self.records.append(QueueRecord(source,indices));self.url_entry.clear()
            self.refresh_queue();self.persist();self.set_status('added')
        self.selection_dialog=SelectionDialog(self,source,selected,accept,record is not None)
        self.selection_dialog.show()

    def edit_selection(self):
        selected=self.selected_record_ids()
        if selected:self.edit_record(next(iter(selected)))

    def edit_record(self,record_id):
        if self.operation=='idle':
            record=next((r for r in self.records if r.id==record_id),None)
            if record:
                if record.source.kind=='pending':self.resolve_links()
                else:self.show_selection(record.source,record)

    def remove_selected(self):
        if self.operation=='idle':
            selected=self.selected_record_ids();self.records=[r for r in self.records if r.id not in selected];self.refresh_queue();self.persist()

    def clear_completed(self):
        if self.operation=='idle':self.records=[r for r in self.records if r.status!='completed'];self.refresh_queue();self.persist()

    def start(self):
        if self.operation!='idle':return
        pending=[r for r in self.records if r.status!='completed']
        if not pending:self.set_status('nothing');return
        if any(r.source.kind=='pending' for r in pending):
            self.resolve_links(download_after=True);return
        defaults=self.get_options()
        try:
            for record in pending:build_args(record.options(defaults),self.tools)
        except ValueError as exc:self.append_log(str(exc));self.set_status('nothing');return
        self.persist();self.set_operation('download');self.set_status('connecting');self.progress.setRange(0,0)
        self.batch=Batch(self.tools,lambda kind,value:self.events.put((kind,value)))
        threading.Thread(target=self.batch.run,args=(pending,defaults),daemon=True).start()

    def cancel(self):
        job=self.batch if self.operation=='download' else self.resolver if self.operation=='resolve' else self.preview_job
        if job is not None:
            self.set_status('cancelling');self.cancel_button.setEnabled(False)
            threading.Thread(target=job.cancel,daemon=True).start()

    def update_engine(self):
        if self.operation=='idle':
            self.set_operation('update');self.set_status('update_check')
            threading.Thread(target=update_nightly,args=(self.tools,lambda kind,value:self.events.put((kind,value))),daemon=True).start()

    def append_log(self,value):
        self.logs=(self.logs+[redact(value)])[-350:]
        self.log.setPlainText('\n'.join(self.logs));self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def poll(self):
        try:
            for _ in range(150):
                kind,value=self.events.get_nowait()
                if kind=='log':
                    self.append_log(value)
                    if any(word in str(value) for word in ('[ExtractAudio]','[Merger]','[Metadata]','[EmbedThumbnail]','[VideoRemuxer]')):self.set_status('finishing')
                elif kind=='item':
                    self.current_text=str(value)[:115];self.current.setText(self.current_text);self.current.show();self.progress.setRange(0,100);self.progress.setValue(0)
                elif kind=='file':self.append_log(self.t('saved',path=value))
                elif kind=='progress' and isinstance(value,dict):
                    total=value.get('total_bytes') or value.get('total_bytes_estimate') or 0
                    percent=min(100,(value.get('downloaded_bytes') or 0)*100/total) if total else 0
                    self.progress.setRange(0,100);self.progress.setValue(round(percent))
                    text=self.t('speed',percent=f'{percent:.0f}',speed=f'{(value.get("speed") or 0)/1048576:.1f}')
                    if isinstance(value.get('eta'),(int,float)):text+=' · '+self.t('remaining',seconds=int(value['eta']))
                    self.status.setText(text)
                elif kind=='queue_status':
                    for record in self.records:
                        if record.id==value['id']:record.status=value['status']
                    self.refresh_queue();self.persist()
                elif kind=='resolved':
                    record=next((r for r in self.records if r.id==value['id']),None)
                    if record:
                        record.source=value['source'];record.selected=[e.index for e in record.source.entries if e.available];record.status='queued'
                    self.refresh_queue();self.persist()
                elif kind=='resolve_done':
                    for record in self.records:
                        if record.status=='fetching':record.status='pending'
                    self.resolver=None;self.set_operation('idle');self.progress.setRange(0,100);self.refresh_queue();self.persist()
                    self.set_status('resolve_stopped' if value['cancelled'] else 'resolve_done',**value)
                    if self.resolve_then_download and not value['cancelled'] and not value['errors'] and not self.close_pending:
                        self.resolve_then_download=False;self.start()
                    else:self.resolve_then_download=False
                elif kind=='batch_done':
                    self.progress.setRange(0,100);self.progress.setValue(0 if value['cancelled'] else 100)
                    self.batch=None;self.set_operation('idle');self.current.hide()
                    self.set_status('batch_cancelled' if value['cancelled'] else 'batch_done',**value);self.persist()
                elif kind in ('preview_ok','preview_error'):
                    cancelled=self.preview_job is not None and self.preview_job.cancelled.is_set()
                    self.preview_job=None;self.progress.setRange(0,100);self.progress.setValue(0);self.set_operation('idle')
                    if cancelled:self.set_status('preview_stopped')
                    elif kind=='preview_ok' and not self.close_pending:self.show_selection(value);self.set_status('ready')
                    else:self.append_log(value);self.set_status('preview_failed')
                elif kind in ('updated','update_error'):
                    self.set_operation('idle')
                    if kind=='updated':self.version_label.setText('yt-dlp nightly\n'+str(value));self.set_status('update_ok')
                    else:self.append_log(value);self.set_status('update_error')
                if self.close_pending and self.operation=='idle':self.close();return
        except queue.Empty:pass
        self.queue_page.sync_state()

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not hasattr(self,'wave'):return
        self.wave.setVisible(self.width()>1150)
        compact=self.width()<1120
        self.sidebar.setFixedWidth(210 if compact else 226)
        if getattr(self,'compact_checks',None)!=compact:
            self.compact_checks=compact
            if compact:
                self.queue_header.removeWidget(self.queue_actions);self.queue_card.body.insertWidget(1,self.queue_actions)
                self.destination_actions.removeWidget(self.update_button)
                self.update_footer.layout().addWidget(self.update_button);self.update_footer.show()
            else:
                self.queue_card.body.removeWidget(self.queue_actions);self.queue_header.addWidget(self.queue_actions)
                self.update_footer.layout().removeWidget(self.update_button)
                self.destination_actions.addWidget(self.update_button);self.update_footer.hide()
            for index,button in enumerate((self.fetch_button,self.edit_button,self.remove_button,self.clear_button)):
                self.queue_action_layout.removeWidget(button)
                self.queue_action_layout.addWidget(button,index//2,index%2)
            for index,line in enumerate(self.check_rows):
                self.checks_grid.removeWidget(line);self.checks_grid.addWidget(line,index if compact else index//2,0 if compact else index%2)
            self.checks_grid.setColumnStretch(1,0 if compact else 1);self.checks_grid.setColumnStretch(0,1)
        self.tree.setColumnHidden(2,compact)

    def closeEvent(self,event):
        if self.operation!='idle':
            key='close_update' if self.operation=='update' else 'close_busy'
            answer=QMessageBox.question(self,APP_NAME,self.t(key),QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer==QMessageBox.StandardButton.Yes:
                self.close_pending=True
                if self.operation!='update':self.cancel()
            event.ignore();return
        self.persist();self.poll_timer.stop();self.thumbnails.close();event.accept()


class SettingsPage(QScrollArea):
    def __init__(self,app):
        super().__init__();self.app=app;self.setWidgetResizable(True);self.setFrameShape(QScrollArea.Shape.NoFrame)
        content=QWidget();self.setWidget(content);layout=QVBoxLayout(content);layout.setContentsMargins(24,24,24,24);layout.setSpacing(15)
        intro=Card(app);app.heading(intro.body,'settings','palette','appearance_hint')
        self.language=Combo(app);self.language.addItems(list(LANGUAGES.values()));self.language.setCurrentIndex(list(LANGUAGES).index(app.language))
        language_row=QHBoxLayout();language_row.addWidget(app.label('language','heading'));language_row.addStretch();language_row.addWidget(self.language)
        intro.body.addLayout(language_row);layout.addWidget(intro)
        self.language.currentIndexChanged.connect(self.change_language)
        self.tabs={};tabs=self.tabs_layout=QGridLayout();tabs.setSpacing(8)
        for index,(section,key) in enumerate([('appearance','appearance'),('media','media'),('cookies','cookies_tab'),('ssmp','SSMP'),('services','services')]):
            button=QPushButton('SSMP') if section=='ssmp' else app.make_button(key,role='tab')
            button.setProperty('role','tab');button.setCheckable(True);button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda checked=False,s=section:self.select_section(s));tabs.addWidget(button,index//3,index%3);self.tabs[section]=button
        layout.addLayout(tabs)
        gallery_card=Card(app);gallery_card.body.addWidget(app.label('theme_gallery','heading'))
        self.gallery=QWidget();self.gallery.installEventFilter(self);self.gallery_layout=QGridLayout(self.gallery);self.gallery_layout.setContentsMargins(0,0,0,0);self.gallery_layout.setSpacing(12)
        self.tiles={}
        for i,key in enumerate(THEMES):
            tile=ThemeTile(key,app);tile.chosen.connect(app.choose_theme);self.tiles[key]=tile;self.gallery_layout.addWidget(tile,i//4,i%4)
        gallery_card.body.addWidget(self.gallery);self.theme_label=text_label('','muted');gallery_card.body.addWidget(self.theme_label);layout.addWidget(gallery_card)
        colors=Card(app);color_heading=QHBoxLayout();color_heading.addWidget(app.label('custom_colors','heading'));color_heading.addStretch()
        self.reset=app.make_button('reset_colors','refresh',self.reset_colors);color_heading.addWidget(self.reset);colors.body.addLayout(color_heading)
        colors.body.addWidget(app.label('color_hint','muted',True))
        grid=QGridLayout();grid.setHorizontalSpacing(22);grid.setVerticalSpacing(8);self.color_controls={}
        for index,key in enumerate(COLOR_KEYS):
            box=QWidget();h=QHBoxLayout(box);h.setContentsMargins(0,4,0,4);h.setSpacing(9)
            title=app.label('color_'+key,'muted');title.setMinimumWidth(100);h.addWidget(title,1)
            swatch=QPushButton();swatch.setFixedSize(34,30);swatch.setCursor(Qt.CursorShape.PointingHandCursor);swatch.setAccessibleName(app.t('color_'+key))
            swatch.clicked.connect(lambda checked=False,k=key:self.pick_color(k));h.addWidget(swatch)
            edit=QLineEdit();edit.setFixedWidth(100);edit.setMaxLength(7);edit.setAccessibleName(app.t('color_'+key))
            edit.editingFinished.connect(lambda k=key:self.edit_color(k));h.addWidget(edit)
            grid.addWidget(box,index//2,index%2);self.color_controls[key]=(swatch,edit)
        colors.body.addLayout(grid);self.feedback=text_label('','muted');colors.body.addWidget(self.feedback);layout.addWidget(colors)
        wallpaper=Card(app);wallpaper.body.addWidget(app.label('wallpaper','heading'));wallpaper.body.addWidget(app.label('wallpaper_new_hint','muted',True))
        self.wallpaper_name=text_label('','muted');wallpaper.body.addWidget(self.wallpaper_name)
        wallpaper.body.addLayout(row(app.make_button('choose_image','image',self.choose_wallpaper),app.make_button('remove_image','close',self.remove_wallpaper)));layout.addWidget(wallpaper)
        self.media_container=QWidget();media_layout=QVBoxLayout(self.media_container);media_layout.setContentsMargins(0,0,0,0);media_layout.setSpacing(15)
        media=Card(app);media.body.addWidget(app.label('media','heading'));media.body.addWidget(app.label('lyrics_help','muted',True))
        self.embed_lyrics=Check(app.t('embed_lyrics'),app,app.embed_lyrics);media.body.addWidget(self.embed_lyrics)
        media.body.addWidget(app.label('sub_languages','muted'));self.subtitle_languages=QLineEdit(app.subtitle_languages);media.body.addWidget(self.subtitle_languages)
        self.automatic_subtitles=Check(app.t('auto_subtitles'),app,app.automatic_subtitles);media.body.addWidget(self.automatic_subtitles)
        self.embed_subtitles=Check(app.t('embed_subtitles'),app,app.embed_subtitles);media.body.addWidget(self.embed_subtitles)
        media.body.addWidget(app.label('sub_help','muted',True));media_layout.addWidget(media)
        integration=Card(app);integration.body.addWidget(text_label('SSMP','heading'))
        self.ssmp_enabled=Check(app.t('ssmp_enable'),app,app.ssmp_enabled);integration.body.addWidget(self.ssmp_enabled)
        integration.body.addWidget(app.label('ssmp_inbox','muted'));self.ssmp_inbox=QLineEdit(app.ssmp_inbox)
        integration.body.addLayout(row(self.ssmp_inbox,app.make_button('browse','folder',self.choose_inbox)))
        integration.body.addWidget(app.label('ssmp_help','muted',True));media_layout.addWidget(integration)
        save_row=QHBoxLayout();save_row.addStretch();self.apply_button=app.make_button('apply','check',self.apply_media,primary=True);save_row.addWidget(self.apply_button);media_layout.addLayout(save_row)
        layout.addWidget(self.media_container)
        services=Card(app);services.body.addWidget(app.label('services','heading'));services.body.addWidget(app.label('service_help','',True));services.body.addWidget(app.label('disclaimer','muted',True));layout.addWidget(services);layout.addStretch()
        self.cookie_card=CookieCard(app);layout.insertWidget(layout.count()-1,self.cookie_card)
        self.sections={'cookies':[self.cookie_card],'appearance':[gallery_card,colors,wallpaper],'media':[media],'ssmp':[integration],'services':[services]}
        self.current_section='appearance';self.select_section('appearance')
        self.gallery_columns=4

    def select_section(self,section):
        if not hasattr(self,'sections'):return
        self.current_section=section
        for key,widgets in self.sections.items():
            for widget in widgets:widget.setVisible(key==section)
        self.media_container.setVisible(section in ('media','ssmp'))
        for key,button in self.tabs.items():button.setChecked(key==section)
        self.verticalScrollBar().setValue(0)

    def eventFilter(self,watched,event):
        if watched is getattr(self,'gallery',None) and event.type()==QEvent.Type.Resize:
            self.reflow_gallery()
        return super().eventFilter(watched,event)

    def reflow_gallery(self):
        if not hasattr(self,'tiles'):return
        columns=max(2,min(4,(self.viewport().width()-78)//185))
        if columns!=getattr(self,'gallery_columns',4):
            self.gallery_columns=columns
            for i,tile in enumerate(self.tiles.values()):self.gallery_layout.removeWidget(tile);self.gallery_layout.addWidget(tile,i//columns,i%columns)

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.reflow_gallery()
        if hasattr(self,'tabs'):
            columns=5 if self.viewport().width()>950 else 3
            for i,button in enumerate(self.tabs.values()):
                self.tabs_layout.removeWidget(button);self.tabs_layout.addWidget(button,i//columns,i%columns)

    def sync_appearance(self):
        app=self.app
        self.language.blockSignals(True);self.language.setCurrentIndex(list(LANGUAGES).index(app.language));self.language.blockSignals(False)
        self.cookie_card.sync()
        for key,tile in self.tiles.items():tile.setChecked(key==app.theme);tile.update()
        self.theme_label.setText(app.t('theme_selected',theme=THEMES[app.theme].name))
        for key,(swatch,edit) in self.color_controls.items():
            swatch.setStyleSheet(f"QPushButton {{ background: {app.colors[key]}; border: 1px solid {app.colors['border']}; border-radius: 7px; padding: 0; }}")
            if not edit.hasFocus():edit.setText(app.colors[key])
        self.wallpaper_name.setText(Path(app.wallpaper_path).name if app.wallpaper_path else app.t('no_image'))
        for control,key in ((self.embed_lyrics,'embed_lyrics'),(self.automatic_subtitles,'auto_subtitles'),(self.embed_subtitles,'embed_subtitles'),(self.ssmp_enabled,'ssmp_enable')):control.setText(app.t(key))

    def change_language(self,index):
        self.app.language=list(LANGUAGES)[index];self.app.apply_appearance()

    def reset_colors(self):
        self.app.theme_colors={};self.app.apply_appearance();self.feedback.setText(self.app.t('appearance_saved'))

    def pick_color(self,key):
        value=QColorDialog.getColor(QColor(self.app.colors[key]),self,self.app.t('color_'+key))
        if value.isValid():self.app.set_custom_color(key,value.name());self.color_controls[key][1].setText(value.name());self.feedback.setText(self.app.t('appearance_saved'))

    def edit_color(self,key):
        edit=self.color_controls[key][1]
        if self.app.set_custom_color(key,edit.text().strip()):self.feedback.setText(self.app.t('appearance_saved'))
        else:edit.setText(self.app.colors[key]);self.feedback.setText(self.app.t('color_invalid'))

    def choose_wallpaper(self):
        path,_=QFileDialog.getOpenFileName(self,self.app.t('choose_image'),'','Images (*.png *.jpg *.jpeg *.webp *.bmp)')
        if path:
            try:self.app.wallpaper_path=import_wallpaper(path,self.app.settings_path.parent/'wallpaper.png');self.app.apply_appearance()
            except Exception:QMessageBox.warning(self,self.app.t('wallpaper'),self.app.t('image_error'))

    def remove_wallpaper(self):
        self.app.wallpaper_path='';self.app.apply_appearance()

    def choose_inbox(self):
        folder=QFileDialog.getExistingDirectory(self,'SSMP',self.ssmp_inbox.text())
        if folder:self.ssmp_inbox.setText(folder)

    def reload_media(self):
        self.embed_lyrics.setChecked(self.app.embed_lyrics);self.subtitle_languages.setText(self.app.subtitle_languages)
        self.automatic_subtitles.setChecked(self.app.automatic_subtitles);self.embed_subtitles.setChecked(self.app.embed_subtitles)
        self.ssmp_enabled.setChecked(self.app.ssmp_enabled);self.ssmp_inbox.setText(self.app.ssmp_inbox)

    def apply_media(self):
        if not re.fullmatch(r'[A-Za-z0-9_.*,\-]+',self.subtitle_languages.text().strip()):
            QMessageBox.warning(self,self.app.t('settings'),self.app.t('sub_languages'));return
        for name in ('embed_lyrics','automatic_subtitles','embed_subtitles','ssmp_enabled'):setattr(self.app,name,getattr(self,name).isChecked())
        self.app.subtitle_languages=self.subtitle_languages.text().strip();self.app.ssmp_inbox=self.ssmp_inbox.text()
        self.app.persist();self.feedback.setText(self.app.t('settings_saved'));self.app.set_status('settings_saved')


def main():
    qt=QApplication(sys.argv[:1]);qt.setStyle('Fusion');qt.setApplicationName(APP_NAME);qt.setOrganizationName('Slulisee')
    smoke=len(sys.argv)>2 and sys.argv[1]=='--smoke-test'
    app=App(Path(sys.argv[2]).with_suffix('.settings.json') if smoke else None)
    app.show()
    if smoke:
        def verify():
            from lyrics import LyricsFinder
            from services import catalog_provider
            from engine import bundled_plugins, process_kwargs
            from platform_support import tool_path
            import subprocess
            app.navigate('queue');qt.processEvents()
            fixture=Path(sys.argv[2]).with_suffix('.plugin.json')
            fixture.write_text(json.dumps(dict(id='smoke',title='Generated smoke fixture',artist='Example Artist, Friend, Example Artist',album='Example Album',url='https://example.com/generated.wav',ext='wav',extractor='generic')),encoding='utf-8')
            try:
                result=subprocess.run([str(tool_path(app.tools,'yt-dlp')),'--ignore-config','--no-plugin-dirs','--plugin-dirs',str(bundled_plugins()),'--use-postprocessor','SSYTDLPMetadata:when=after_filter','--load-info-json',str(fixture),'--simulate','--print','video:%(artist)s|%(folder_artist)s'],capture_output=True,text=True,timeout=20,**process_kwargs())
                metadata_plugin=result.returncode==0 and 'Example Artist, Friend|Example Artist' in result.stdout
            except Exception:metadata_plugin=False
            finally:fixture.unlink(missing_ok=True)
            values=dict(title=app.windowTitle(),presets=list(PRESETS),nightly=app.read_version().replace('\n',' '),mapped=app.isVisible(),
                buttons=[app.download_button.text(),app.add_button.text(),app.nav['settings'].text()],languages=LANGUAGES,
                theme=app.theme,themes=list(THEMES),watermark='made by Slulisee',extras=[app.t(k) for k in ('metadata','cover','organize','skip','lyrics','subtitles')],
                lyric_provider=type(LyricsFinder().provider).__name__,spotify_import=catalog_provider('https://open.spotify.com/track/example'),
                ssmp_enabled=app.ssmp_enabled,qt_version=__import__('PySide6').__version__,
                queue_page=app.pages.currentWidget() is app.queue_page,
                queue_model=type(app.queue_page.table.model().sourceModel()).__name__,
                thumbnail_cache=type(app.thumbnails).__name__)
            values.update(metadata_plugin=metadata_plugin,cookie_mode=app.cookies.mode,staged_links=stage_links('https://example.com/staged')[0].source.kind)
            Path(sys.argv[2]).write_text(json.dumps(values,indent=2),encoding='utf-8');app.close()
        QTimer.singleShot(1400,verify)
    return qt.exec()
