"""Rounded native Qt widgets and code-drawn icons for the SSMD view."""
from __future__ import annotations
from PySide6.QtCore import QByteArray, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton,
                              QSizePolicy, QVBoxLayout, QWidget)
from themes import THEMES, mix, palette


PATHS = {
 'download':'<path d="M12 3v12m-5-5 5 5 5-5M4 15v5h16v-5"/>',
 'home':'<path d="m3 11 9-8 9 8M5 10v11h5v-7h4v7h5V10"/>',
 'queue':'<path d="M9 5h12M9 11h12M9 17h5m2 1 2 2 4-5"/><circle cx="3" cy="5" r="1"/><circle cx="3" cy="11" r="1"/><circle cx="3" cy="17" r="1"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
 'settings':'<polygon points="8.94,4.61 10.20,4.21 10.19,1.76 13.81,1.76 13.80,4.21 15.06,4.61 16.24,5.22 17.97,3.48 20.52,6.03 18.78,7.76 19.39,8.94 19.79,10.20 22.24,10.19 22.24,13.81 19.79,13.80 19.39,15.06 18.78,16.24 20.52,17.97 17.97,20.52 16.24,18.78 15.06,19.39 13.80,19.79 13.81,22.24 10.19,22.24 10.20,19.79 8.94,19.39 7.76,18.78 6.03,20.52 3.48,17.97 5.22,16.24 4.61,15.06 4.21,13.80 1.76,13.81 1.76,10.19 4.21,10.20 4.61,8.94 5.22,7.76 3.48,6.03 6.03,3.48 7.76,5.22"/><circle cx="12" cy="12" r="3.5"/>',
 'info':'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
 'link':'<path d="m10 14 4-4m-6 5-2 2a4 4 0 0 1-6-6l4-4a4 4 0 0 1 6 0m2 2 2-2a4 4 0 0 1 6 6l-4 4a4 4 0 0 1-6 0" transform="translate(2 -1)"/>',
 'paste':'<rect x="6" y="5" width="14" height="17" rx="2"/><path d="M9 5V2h7v3M3 16V3h3"/>',
 'plus':'<path d="M12 4v16M4 12h16"/>',
 'edit':'<path d="m4 17-1 4 4-1L21 6l-4-4zM14 5l5 5"/>',
 'trash':'<path d="M3 6h18M8 6V3h8v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
 'check':'<path d="m4 12 5 5L20 5"/>',
 'folder':'<path d="M3 6V3h6l3 3h9v15H3zM3 9h18"/>',
 'music':'<path d="M9 18V5l11-2v13M9 8l11-2"/><ellipse cx="5.5" cy="18.5" rx="3.5" ry="2.5"/><ellipse cx="16.5" cy="16.5" rx="3.5" ry="2.5"/>',
 'image':'<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 6-6 4 4 3-3 5 5"/>',
 'tag':'<path d="M3 3h8l10 10-8 8L3 11z"/><circle cx="7" cy="7" r="1"/>',
 'skip':'<path d="m5 4 12 8-12 8zM20 4v16"/>',
 'subtitles':'<rect x="2" y="4" width="20" height="16" rx="3"/><path d="M10 9H7v6h3m8-6h-3v6h3"/>',
 'close':'<path d="m6 6 12 12M6 18 18 6"/>',
 'chevron':'<path d="m6 9 6 6 6-6"/>',
 'refresh':'<path d="M20 8a9 9 0 0 0-15-3L2 8m0-6v6h6m-4 8a9 9 0 0 0 15 3l3-3m0 6v-6h-6"/>',
 'palette':'<circle cx="7" cy="11" r=".8"/><circle cx="10" cy="6" r=".8"/><circle cx="16" cy="7" r=".8"/><path d="M12 2a10 10 0 1 0 0 20h2c3 0 3-4 0-4-2 0-2-3 0-3h3c7 0 5-13-5-13z"/>',
}


def icon(name, color='#ffffff', size=24):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{PATHS.get(name,PATHS["info"])}</g></svg>'
    pix = QPixmap(size*2,size*2)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    QSvgRenderer(QByteArray(svg.encode())).render(painter)
    painter.end()
    pix.setDevicePixelRatio(2)
    return QIcon(pix)


def text_label(text='', role='', wrap=False):
    label = QLabel(text)
    label.setWordWrap(wrap)
    label.setProperty('role',role)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class Card(QFrame):
    def __init__(self, app, radius=17, parent=None):
        super().__init__(parent)
        self.app, self.radius = app, radius
        self.setObjectName('card')
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground,False)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(22,18,22,18)
        self.body.setSpacing(12)

    def paintEvent(self,event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5,.5,-.5,-.5)
        c = self.app.colors
        gradient = QLinearGradient(r.topLeft(),r.bottomRight())
        gradient.setColorAt(0,QColor(c['panel_high']))
        gradient.setColorAt(.55,QColor(c['panel']))
        gradient.setColorAt(1,QColor(mix(c['panel'],c['bg'],.28)))
        p.setBrush(gradient)
        border = QColor(c['border']); border.setAlpha(140)
        p.setPen(QPen(border,1))
        p.drawRoundedRect(r,self.radius,self.radius)


class Background(QWidget):
    def __init__(self,app):
        super().__init__()
        self.app = app
        self.wallpaper = QPixmap()

    def paintEvent(self,event):
        p=QPainter(self); c=self.app.colors
        p.fillRect(self.rect(),QColor(c['bg']))
        if not self.wallpaper.isNull():
            image=self.wallpaper.scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation)
            p.setOpacity(.18 if not c['light'] else .13)
            p.drawPixmap((self.width()-image.width())//2,(self.height()-image.height())//2,image)
            p.setOpacity(1)
        glow=QRadialGradient(QPointF(self.width()*.61,-60),self.width()*.65)
        color=QColor(c['glow']);color.setAlpha(24 if not c['light'] else 15)
        glow.setColorAt(0,color);color.setAlpha(0);glow.setColorAt(1,color)
        p.fillRect(self.rect(),glow)


class BrandIcon(QWidget):
    def __init__(self,app,size=56):
        super().__init__();self.app=app;self.setFixedSize(size,size)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.app.colors;r=QRectF(self.rect()).adjusted(1,1,-1,-1)
        grad=QLinearGradient(r.topLeft(),r.bottomRight())
        grad.setColorAt(0,c['glow']);grad.setColorAt(1,c['accent'])
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(grad);p.drawRoundedRect(r,16,16)
        pix=icon('download',c['on_accent'],34).pixmap(QSize(34,34))
        p.drawPixmap((self.width()-34)//2,(self.height()-34)//2,pix)


class Wave(QWidget):
    def __init__(self,app):
        super().__init__();self.app=app;self.setFixedSize(320,44)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path=QPainterPath(QPointF(0,36))
        path.cubicTo(35,34,47,7,78,24);path.cubicTo(108,48,118,34,139,13)
        path.cubicTo(178,-25,197,42,230,38);path.cubicTo(270,44,275,2,320,32)
        grad=QLinearGradient(0,0,320,0)
        color=QColor(self.app.colors['glow']);color.setAlpha(0);grad.setColorAt(0,color)
        color.setAlpha(175);grad.setColorAt(.5,color);color.setAlpha(0);grad.setColorAt(1,color)
        p.setPen(QPen(grad,1.2));p.drawPath(path)


class Check(QCheckBox):
    def __init__(self,text,app,checked=False):
        super().__init__(text);self.app=app;self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(32)

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=self.app.colors
        p.setOpacity(1 if self.isEnabled() else .45)
        box=QRectF(3,(self.height()-21)/2,21,21)
        fill=QColor(c['accent'] if self.isChecked() else c['field'])
        p.setBrush(fill);p.setPen(QPen(QColor(c['accent'] if self.isChecked() else c['icon'] if self.underMouse() else c['control_border']),1.2))
        p.drawRoundedRect(box,5,5)
        if self.isChecked():
            p.setPen(QPen(QColor(c['on_accent']),2.2,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline([QPointF(box.x()+5,box.y()+11),QPointF(box.x()+9,box.y()+15),QPointF(box.x()+17,box.y()+6)])
        if self.hasFocus():
            p.setBrush(Qt.BrushStyle.NoBrush);p.setPen(QPen(QColor(c['glow']),1.2));p.drawRoundedRect(box.adjusted(-1,-1,1,1),6,6)
        p.setPen(QColor(c['text']));p.setFont(self.font())
        p.drawText(self.rect().adjusted(34,0,0,0),Qt.AlignmentFlag.AlignVCenter|Qt.AlignmentFlag.AlignLeft,self.text())

    def hitButton(self,pos):
        return self.rect().contains(pos)


class Combo(QComboBox):
    def __init__(self,app,leading=None):
        super().__init__();self.app,self.leading=app,leading
        if leading:self.setStyleSheet('QComboBox { padding-left: 42px; }')

    def paintEvent(self,event):
        super().paintEvent(event)
        painter=QPainter(self)
        color=self.app.colors['text'] if self.isEnabled() else self.app.colors['muted']
        painter.drawPixmap(self.width()-28,(self.height()-16)//2,icon('chevron',color,16).pixmap(16,16))
        if self.leading:painter.drawPixmap(13,(self.height()-20)//2,icon(self.leading,color,20).pixmap(20,20))


class ThemeTile(QPushButton):
    chosen=Signal(str)
    def __init__(self,key,app):
        super().__init__();self.key,self.app=key,app
        self.setMinimumSize(170,133);self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
        self.setProperty('role','themeTile')
        self.setCheckable(True);self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(THEMES[key].name)
        self.setToolTip(THEMES[key].mood)
        self.clicked.connect(lambda:self.chosen.emit(key))

    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        c=palette(self.key,self.app.theme_colors if self.isChecked() else None);r=QRectF(self.rect()).adjusted(2,2,-2,-2)
        p.setBrush(QColor(self.app.colors['button'] if self.underMouse() else self.app.colors['field']));p.setPen(QPen(QColor(self.app.colors['accent'] if self.isChecked() or self.underMouse() else self.app.colors['border']),2 if self.isChecked() else 1))
        p.drawRoundedRect(r,12,12)
        preview=QRectF(r.x()+9,r.y()+9,r.width()-18,73)
        grad=QLinearGradient(preview.topLeft(),preview.bottomRight());grad.setColorAt(0,c['bg']);grad.setColorAt(1,mix(c['panel'],c['glow'],.15))
        p.setBrush(grad);p.setPen(Qt.PenStyle.NoPen);p.drawRoundedRect(preview,7,7)
        p.setBrush(QColor(c['panel']));p.drawRoundedRect(QRectF(preview.x()+6,preview.y()+6,25,61),4,4)
        p.setBrush(QColor(c['accent']));p.drawRoundedRect(QRectF(preview.x()+10,preview.y()+12,17,6),2,2)
        for y in (27,38,49):
            p.setBrush(QColor(c['muted']));p.drawRoundedRect(QRectF(preview.x()+11,preview.y()+y,15,2),1,1)
        for y,h in ((6,14),(25,23),(53,14)):
            p.setBrush(QColor(c['panel']));p.drawRoundedRect(QRectF(preview.x()+37,preview.y()+y,preview.width()-44,h),3,3)
        p.setBrush(QColor(c['accent']));p.drawRoundedRect(QRectF(preview.x()+43,preview.y()+57,36,6),2,2)
        p.setBrush(QColor(c['glow']));p.drawEllipse(QPointF(preview.right()-13,preview.y()+13),3,3)
        p.setPen(QColor(self.app.colors['text']));f=p.font();f.setBold(True);p.setFont(f)
        p.drawText(QRectF(r.x()+12,r.y()+89,r.width()-44,20),Qt.AlignmentFlag.AlignLeft,THEMES[self.key].name)
        if self.isChecked():
            p.drawPixmap(int(r.right()-29),int(r.y()+90),icon('check',self.app.colors['accent'],17).pixmap(17,17))
        if self.hasFocus():
            p.setPen(QPen(QColor(self.app.colors['glow']),1,Qt.PenStyle.DashLine));p.setBrush(Qt.BrushStyle.NoBrush);p.drawRoundedRect(r.adjusted(4,4,-4,-4),8,8)


def stylesheet(c):
    return f'''
    QWidget {{ color: {c['text']}; font-family: "Segoe UI", "Inter", sans-serif; font-size: 15px; background: transparent; }}
    QWidget[role="sidebar"] {{ border-right: 1px solid {c['border']}; background: {c['sidebar']}; }}
    QLabel[role="heading"] {{ font-size: 18px; font-weight: 700; }}
    QLabel[role="title"] {{ font-size: 25px; font-weight: 750; }}
    QLabel[role="muted"] {{ color: {c['muted']}; font-size: 13px; }}
    QLabel[role="hint"] {{ color: {c['muted']}; font-size: 13px; }}
    QLabel[role="empty-title"] {{ color: {c['muted']}; font-size: 16px; font-weight: 650; }}
    QLabel[role="empty-icon"] {{ border: 1px dashed {c['muted']}; border-radius: 12px; }}
    QLineEdit, QComboBox, QPlainTextEdit {{ background: {c['field']}; border: 1px solid {c['border']}; border-radius: 8px; padding: 10px 13px; selection-background-color: {c['selected']}; selection-color: {c['text']}; }}
    QLineEdit:focus, QComboBox:focus {{ border: 1px solid {c['glow']}; }}
    QLineEdit:disabled {{ color: {c['muted']}; }}
    QComboBox {{ min-height: 18px; padding-right: 32px; }}
    QComboBox::drop-down {{ border: none; width: 30px; }}
    QComboBox::down-arrow {{ image: none; width: 0; height: 0; }}
    QComboBox QAbstractItemView {{ background: {c['panel']}; color: {c['text']}; border: 1px solid {c['border']}; selection-background-color: {c['selected']}; padding: 5px; outline: none; }}
    QPushButton {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {c['button']},stop:1 {c['panel']}); border: 1px solid {c['border']}; border-radius: 8px; padding: 10px 15px; min-height: 17px; }}
    QPushButton:hover {{ background: {c['active']}; border-color: {c['glow']}; }}
    QPushButton:pressed {{ background: {c['selected']}; padding-top: 11px; padding-bottom: 9px; }}
    QPushButton:focus {{ border-color: {c['glow']}; }}
    QPushButton:disabled {{ color: {c['muted']}; background: {c['panel']}; border-color: {c['border']}; }}
    QPushButton[role="primary"] {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {c['accent_hover']},stop:1 {c['accent']}); border: 1px solid {c['accent']}; color: {c['on_accent']}; font-weight: 650; }}
    QPushButton[role="primary"]:hover {{ background: {c['accent_hover']}; }}
    QPushButton[role="primary"]:disabled {{ background: {c['button']}; color: {c['muted']}; border-color: {c['border']}; }}
    QPushButton[role="nav"] {{ text-align: left; border: none; border-left: 4px solid transparent; border-radius: 11px; padding: 14px 14px; background: transparent; font-weight: 600; color: {c['muted']}; }}
    QPushButton[role="nav"]:hover {{ background: {c['button']}; color: {c['text']}; }}
    QPushButton[role="nav"]:checked {{ border-left-color: {c['icon']}; background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {c['button']},stop:1 {c['selected']}); color: {c['icon']}; }}
    QPushButton[role="tab"] {{ padding: 8px 13px; min-height: 17px; }}
    QPushButton[role="tab"]:checked {{ background: {c['selected']}; border-color: {c['accent']}; }}
    QPushButton[role="themeTile"] {{ min-height: 133px; max-height: 133px; min-width: 170px; padding: 0; border: none; }}
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: transparent; width: 8px; margin: 5px 0; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 4px; min-height: 35px; }}
    QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{ background: none; }}
    QTableWidget, QTableView {{ border: 1px solid {c['border']}; border-radius: 9px; background: {c['field']}; gridline-color: {c['border']}; outline: none; selection-background-color: {c['selected']}; selection-color: {c['text']}; }}
    QHeaderView::section {{ background: {c['button']}; color: {c['text']}; border: none; border-bottom: 1px solid {c['border']}; border-right: 1px solid {c['border']}; padding: 10px 10px; font-weight: 600; font-size: 12px; }}
    QTableWidget::item, QTableView::item {{ padding: 8px; border: none; }}
    QProgressBar {{ background: {c['field']}; border: none; border-radius: 3px; height: 5px; max-height: 5px; }}
    QProgressBar::chunk {{ background: {c['accent']}; border-radius: 3px; }}
    QToolTip {{ background: {c['panel']}; color: {c['text']}; border: 1px solid {c['border']}; padding: 7px; border-radius: 5px; }}
    QDialog, QMessageBox {{ background: {c['bg']}; }}
    QPlainTextEdit {{ font-family: Consolas, monospace; font-size: 12px; }}
    '''
