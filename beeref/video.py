# This file is part of SeaRef, derived from BeeRef.
#
# SeaRef is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SeaRef is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SeaRef.  If not, see <https://www.gnu.org/licenses/>.

"""Lazy YouTube link cards for the reference board."""

import logging
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt

from beeref.items import BeeItemMixin, register_item


logger = logging.getLogger(__name__)
VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')
THUMBNAIL_WIDTH = 480
THUMBNAIL_HEIGHT = 270
MAX_THUMBNAIL_BYTES = 2 * 1024 * 1024


def get_youtube_video_id(url):
    """Return the YouTube video ID for supported watch/share URLs."""

    try:
        parts = urlsplit(url.strip())
    except (AttributeError, ValueError):
        return None

    host = (parts.hostname or '').lower()
    if parts.scheme not in ('http', 'https'):
        return None

    if host == 'youtu.be':
        candidate = parts.path.strip('/').split('/', 1)[0]
    elif host == 'youtube.com' or host.endswith('.youtube.com'):
        if parts.path.rstrip('/') == '/watch':
            candidate = parse_qs(parts.query).get('v', [''])[0]
        else:
            segments = [part for part in parts.path.split('/') if part]
            candidate = ''
            if len(segments) >= 2 and segments[0] in (
                    'embed', 'shorts', 'live', 'v'):
                candidate = segments[1]
    else:
        return None

    if VIDEO_ID_RE.fullmatch(candidate):
        return candidate
    return None


class ThumbnailLoader(QtCore.QThread):
    loaded = QtCore.pyqtSignal(bytes)
    failed = QtCore.pyqtSignal(str)

    def __init__(self, video_id, parent=None):
        super().__init__(parent)
        self.video_id = video_id

    def run(self):
        # hqdefault is broadly available and small enough for a reference
        # board; avoid downloading full-size video or max-resolution art.
        thumbnail_url = (
            f'https://i.ytimg.com/vi/{self.video_id}/hqdefault.jpg')
        req = Request(
            thumbnail_url,
            headers={'User-Agent': 'SeaRef reference board'})
        try:
            with urlopen(req, timeout=8) as response:
                image_data = response.read(MAX_THUMBNAIL_BYTES + 1)
            if len(image_data) > MAX_THUMBNAIL_BYTES:
                raise ValueError('Thumbnail is larger than 2 MiB')
            image = QtGui.QImage.fromData(image_data)
            if image.isNull() or image.width() < 160:
                raise ValueError('YouTube did not provide a usable thumbnail')
            self.loaded.emit(image_data)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            logger.info('Could not load YouTube thumbnail: %s', exc)
            self.failed.emit(str(exc))


@register_item
class YouTubeVideoItem(BeeItemMixin, QtWidgets.QGraphicsObject):
    """A lightweight video card that fetches a thumbnail only on click."""

    TYPE = 'video'
    CARD_RECT = QtCore.QRectF(0, 0, THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT)

    def __init__(self, url, **kwargs):
        super().__init__()
        self.url = url.strip()
        self.video_id = get_youtube_video_id(self.url) or ''
        self.save_id = None
        self.is_image = False
        self.is_video = True
        self.is_editable = False
        self._thumbnail = None
        self._thumbnail_loader = None
        self._thumbnail_state = 'empty'
        self._thumbnail_error = ''
        self.init_selectable()

    @classmethod
    def create_from_data(cls, **kwargs):
        data = kwargs.get('data', {})
        return cls(data.get('url', ''))

    def boundingRect(self):
        return QtCore.QRectF(self.CARD_RECT)

    def paint(self, painter, option, widget):
        painter.save()
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor('#17202a'))
        painter.drawRoundedRect(self.CARD_RECT, 10, 10)

        if self._thumbnail is not None:
            source = QtCore.QRectF(
                (self._thumbnail.width() - THUMBNAIL_WIDTH) / 2,
                (self._thumbnail.height() - THUMBNAIL_HEIGHT) / 2,
                THUMBNAIL_WIDTH,
                THUMBNAIL_HEIGHT)
            painter.drawPixmap(self.CARD_RECT, self._thumbnail, source)
            self._paint_play_button(painter)
            painter.fillRect(
                QtCore.QRectF(0, THUMBNAIL_HEIGHT - 34,
                              THUMBNAIL_WIDTH, 34),
                QtGui.QColor(0, 0, 0, 170))
            label = 'Double-click to watch on YouTube'
        elif self._thumbnail_state == 'loading':
            label = 'Loading YouTube thumbnail…'
        elif self._thumbnail_state == 'failed':
            label = 'Thumbnail unavailable — click to retry'
        else:
            label = 'Click to load YouTube thumbnail'

        if self._thumbnail is None:
            painter.setPen(QtGui.QColor('#f3f6f8'))
            painter.drawText(
                self.CARD_RECT.adjusted(18, 18, -18, -18),
                Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
                f'YouTube video\n{self.video_id or self.url}\n\n{label}')
        else:
            painter.setPen(QtGui.QColor('#ffffff'))
            painter.drawText(
                QtCore.QRectF(12, THUMBNAIL_HEIGHT - 34,
                              THUMBNAIL_WIDTH - 24, 34),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                label)

        self.paint_selectable(painter, option, widget)
        painter.restore()

    def _paint_play_button(self, painter):
        center = self.CARD_RECT.center()
        button_rect = QtCore.QRectF(center.x() - 34, center.y() - 24, 68, 48)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 180))
        painter.drawRoundedRect(button_rect, 12, 12)
        path = QtGui.QPainterPath()
        path.moveTo(center.x() - 7, center.y() - 13)
        path.lineTo(center.x() + 14, center.y())
        path.lineTo(center.x() - 7, center.y() + 13)
        path.closeSubpath()
        painter.setBrush(QtGui.QColor('#ffffff'))
        painter.drawPath(path)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if (event.button() == Qt.MouseButton.LeftButton
                and self._thumbnail is None
                and self._thumbnail_state != 'loading'):
            self.load_thumbnail()

    def mouseDoubleClickEvent(self, event):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.url))
        event.accept()

    def load_thumbnail(self):
        if not self.video_id or self._thumbnail_state == 'loading':
            return
        self._thumbnail_state = 'loading'
        self._thumbnail_error = ''
        self.update()

        app = QtWidgets.QApplication.instance()
        self._thumbnail_loader = ThumbnailLoader(self.video_id, app)
        self._thumbnail_loader.loaded.connect(self.on_thumbnail_loaded)
        self._thumbnail_loader.failed.connect(self.on_thumbnail_failed)
        self._thumbnail_loader.finished.connect(
            self.on_thumbnail_loader_finished)
        self._thumbnail_loader.finished.connect(
            self._thumbnail_loader.deleteLater)
        self._thumbnail_loader.start()

    @QtCore.pyqtSlot(bytes)
    def on_thumbnail_loaded(self, image_data):
        image = QtGui.QImage.fromData(image_data)
        if image.isNull():
            self.on_thumbnail_failed('Downloaded thumbnail was invalid')
            return
        self._thumbnail = QtGui.QPixmap.fromImage(image).scaled(
            THUMBNAIL_WIDTH,
            THUMBNAIL_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        self._thumbnail_state = 'ready'
        self.update()

    @QtCore.pyqtSlot(str)
    def on_thumbnail_failed(self, message):
        self._thumbnail_error = message
        self._thumbnail_state = 'failed'
        self.update()

    @QtCore.pyqtSlot()
    def on_thumbnail_loader_finished(self):
        self._thumbnail_loader = None

    def get_extra_save_data(self):
        # Keep .bee files small; fetched thumbnail pixels are intentionally
        # cached only for the current session and can be fetched again later.
        return {'url': self.url}

    def create_copy(self):
        item = YouTubeVideoItem(self.url)
        item.setPos(self.pos())
        item.setZValue(self.zValue())
        item.setScale(self.scale())
        item.setRotation(self.rotation())
        if self.flip() == -1:
            item.do_flip()
        return item

    def copy_to_clipboard(self, clipboard):
        clipboard.setText(self.url)

    def __str__(self):
        return f'YouTube video {self.video_id}'
