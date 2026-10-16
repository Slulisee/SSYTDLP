"""Bounded, shared metadata-thumbnail cache; network work never runs on the UI thread."""
from collections import OrderedDict
from io import BytesIO
import queue
import threading
from urllib.request import Request, urlopen

from PIL import Image
from PySide6.QtCore import QObject, QRectF, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget

from engine import validate_url
from ui_widgets import icon


class ThumbnailCache(QObject):
    ready = Signal(str)
    result = Signal(str, bytes)

    def __init__(self, parent=None, limit=256):
        super().__init__(parent)
        self.limit=limit;self.cache=OrderedDict();self.pending=set()
        self.jobs=queue.Queue(maxsize=64);self.stopped=threading.Event();self.started=False
        self.result.connect(self.complete)

    def get(self, url):
        if not url:return None
        if url in self.cache:
            self.cache.move_to_end(url)
            return self.cache[url]
        if url in self.pending or self.stopped.is_set():return None
        try:validate_url(url)
        except ValueError:return None
        if self.jobs.full():return None
        self.pending.add(url);self.jobs.put_nowait(url)
        if not self.started:
            self.started=True
            for _ in range(4):threading.Thread(target=self.worker,daemon=True).start()
        return None

    def worker(self):
        while not self.stopped.is_set():
            try:url=self.jobs.get(timeout=.3)
            except queue.Empty:continue
            data=b''
            try:
                with urlopen(Request(url,headers={'User-Agent':'SSYTDLP/2.0'}),timeout=8) as response:
                    # Redirects must also resolve to an HTTP(S) resource.
                    validate_url(response.geturl())
                    raw=response.read(4_000_001)
                if len(raw)>4_000_000:raise ValueError('Thumbnail too large')
                with Image.open(BytesIO(raw)) as image:
                    if image.width*image.height>20_000_000:raise ValueError('Thumbnail too large')
                    image.thumbnail((360,220))
                    output=BytesIO();image.convert('RGBA').save(output,format='PNG');data=output.getvalue()
            except Exception:pass
            if not self.stopped.is_set():
                try:self.result.emit(url,data)
                except RuntimeError:return
            self.jobs.task_done()

    def complete(self,url,data):
        if self.stopped.is_set():return
        pixmap=QPixmap()
        if data:pixmap.loadFromData(data)
        self.pending.discard(url);self.cache[url]=pixmap if not pixmap.isNull() else None
        self.cache.move_to_end(url)
        while len(self.cache)>self.limit:self.cache.popitem(last=False)
        self.ready.emit(url)

    def close(self):
        self.stopped.set()


class ThumbnailCell(QWidget):
    """Paint/request only when visible, rather than fetching an entire playlist."""
    def __init__(self,app,url='',fallback='image',parent=None):
        super().__init__(parent)
        self.app=app;self.url=url;self.fallback=fallback
        app.thumbnails.ready.connect(self.thumbnail_ready)

    def set_url(self,url):
        self.url=url;self.update()

    def thumbnail_ready(self,url):
        if url==self.url:self.update()

    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pixmap=self.app.thumbnails.get(self.url)
        if pixmap is None:
            fallback=icon(self.fallback,self.app.colors['muted'],25).pixmap(25,25)
            painter.drawPixmap((self.width()-25)//2,(self.height()-25)//2,fallback);return
        area=self.rect().adjusted(5,5,-5,-5)
        image=pixmap.scaled(area.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        x=(self.width()-image.width())//2;y=(self.height()-image.height())//2
        clip=QPainterPath();clip.addRoundedRect(QRectF(x,y,image.width(),image.height()),6,6)
        painter.setClipPath(clip);painter.drawPixmap(x,y,image)
