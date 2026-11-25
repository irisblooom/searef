from beeref.fileio.sql import SQLiteIO
from beeref.video import YouTubeVideoItem


def test_video_link_round_trips_without_embedding_thumbnail(view, tmpfile):
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    item = YouTubeVideoItem(url)
    view.scene.addItem(item)

    writer = SQLiteIO(tmpfile, view.scene, create_new=True)
    writer.write()
    assert writer.fetchone('SELECT COUNT(*) FROM sqlar')[0] == 0

    view.scene.clear()
    reader = SQLiteIO(tmpfile, view.scene, readonly=True)
    reader.read()
    view.scene.add_queued_items()

    videos = list(view.scene.items_by_type('video'))
    assert len(videos) == 1
    assert videos[0].url == url
    assert videos[0]._thumbnail is None
