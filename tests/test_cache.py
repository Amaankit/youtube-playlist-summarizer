import os
import pytest
from yt_summarizer.cache.db import CacheDB
from yt_summarizer.models.video import Video, Transcript, Summary


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    cache = CacheDB(db_path)
    yield cache
    cache.close()


def test_create_tables(db):
    tables = db.list_tables()
    assert "playlists" in tables
    assert "videos" in tables
    assert "transcripts" in tables
    assert "summaries" in tables


def test_save_and_get_video(db):
    video = Video(
        video_id="abc123",
        title="Binary Search",
        url="https://youtube.com/watch?v=abc123",
        position=1,
        playlist_id=None,
    )
    db.save_video(video)
    result = db.get_video("abc123")
    assert result is not None
    assert result.video_id == "abc123"
    assert result.title == "Binary Search"


def test_save_and_get_transcript(db):
    video = Video("v1", "Test", "https://youtube.com/watch?v=v1", 0, None)
    db.save_video(video)
    transcript = Transcript(video_id="v1", text="Hello world", language="en")
    db.save_transcript(transcript)
    result = db.get_transcript("v1")
    assert result is not None
    assert result.text == "Hello world"
    assert result.language == "en"


def test_get_transcript_cache_miss(db):
    result = db.get_transcript("nonexistent")
    assert result is None


def test_save_and_get_summary(db):
    video = Video("v1", "Test", "https://youtube.com/watch?v=v1", 0, None)
    db.save_video(video)
    transcript = Transcript(video_id="v1", text="Hello", language="en")
    db.save_transcript(transcript)
    summary = Summary(
        video_id="v1",
        title="Test",
        intent="DSA",
        detail_level="detailed",
        content="# Summary content",
    )
    db.save_summary(summary, model="gemini-2.0-flash")
    result = db.get_summary("v1", "DSA", "detailed")
    assert result is not None
    assert result.content == "# Summary content"
    assert result.intent == "DSA"


def test_get_summary_cache_miss(db):
    result = db.get_summary("v1", "DSA", "detailed")
    assert result is None


def test_summary_different_intent_is_separate(db):
    video = Video("v1", "Test", "https://youtube.com/watch?v=v1", 0, None)
    db.save_video(video)
    db.save_transcript(Transcript("v1", "text", "en"))
    db.save_summary(
        Summary("v1", "Test", "DSA", "detailed", "DSA summary"),
        model="gemini-2.0-flash",
    )
    db.save_summary(
        Summary("v1", "Test", "System Design", "detailed", "SD summary"),
        model="gemini-2.0-flash",
    )
    dsa = db.get_summary("v1", "DSA", "detailed")
    sd = db.get_summary("v1", "System Design", "detailed")
    assert dsa.content == "DSA summary"
    assert sd.content == "SD summary"


def test_save_playlist(db):
    db.save_playlist("PL123", "My Playlist", "DSA", 10)
    row = db.get_playlist("PL123")
    assert row is not None
    assert row["title"] == "My Playlist"
    assert row["video_count"] == 10
