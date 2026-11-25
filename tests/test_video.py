import pytest
from PyQt6 import QtCore, QtGui, QtWidgets
from unittest.mock import MagicMock, patch

from beeref.video import YouTubeVideoItem, get_youtube_video_id


@pytest.mark.parametrize('url,expected', [
    ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://youtu.be/dQw4w9WgXcQ?t=42', 'dQw4w9WgXcQ'),
    ('https://m.youtube.com/shorts/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://www.youtube.com/embed/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
    ('https://example.com/watch?v=dQw4w9WgXcQ', None),
    ('not a URL', None),
])
def test_get_youtube_video_id(url, expected):
    assert get_youtube_video_id(url) == expected


def test_video_item_keeps_url_and_does_not_load_thumbnail_until_clicked(qapp):
    url = 'https://youtu.be/dQw4w9WgXcQ'
    item = YouTubeVideoItem(url)
    assert item.TYPE == 'video'
    assert item.video_id == 'dQw4w9WgXcQ'
    assert item.get_extra_save_data() == {'url': url}
    assert item._thumbnail is None
    assert item._thumbnail_state == 'empty'


def test_video_item_paints_placeholder(qapp):
    item = YouTubeVideoItem('https://youtu.be/dQw4w9WgXcQ')
    image = QtGui.QImage(500, 300, QtGui.QImage.Format.Format_ARGB32)
    image.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(image)
    item.paint(painter, QtWidgets.QStyleOptionGraphicsItem(), None)
    painter.end()
    assert image.pixelColor(20, 20).alpha() > 0


@patch('PyQt6.QtGui.QClipboard.mimeData')
@patch('PyQt6.QtGui.QClipboard.image')
@patch('PyQt6.QtGui.QClipboard.text')
def test_pasting_youtube_url_adds_lazy_video_card(
        text_mock, image_mock, mimedata_mock, view):
    text_mock.return_value = 'https://youtu.be/dQw4w9WgXcQ'
    image_mock.return_value = QtGui.QImage()
    mimedata_mock.return_value = QtCore.QMimeData()

    view.on_action_paste()

    videos = list(view.scene.items_by_type('video'))
    assert len(videos) == 1
    assert videos[0].url == 'https://youtu.be/dQw4w9WgXcQ'
    assert videos[0]._thumbnail is None


def test_dropping_youtube_url_adds_lazy_video_card(view):
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    mime_data = QtCore.QMimeData()
    mime_data.setUrls([QtCore.QUrl(url)])
    event = MagicMock()
    event.mimeData.return_value = mime_data
    event.position.return_value = QtCore.QPointF(30, 40)

    view.dropEvent(event)

    videos = list(view.scene.items_by_type('video'))
    assert len(videos) == 1
    assert videos[0].url == url
    event.acceptProposedAction.assert_called_once_with()
