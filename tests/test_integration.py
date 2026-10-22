import os
from unittest.mock import patch, MagicMock
import pytest
from yt_summarizer.cli.app import process_videos
from yt_summarizer.cache.db import CacheDB
from yt_summarizer.models.video import Video, Transcript, Summary


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test.db")
    cache = CacheDB(db_path)
    yield cache
    cache.close()


@patch("yt_summarizer.cli.app.fetch_transcript")
def test_full_pipeline_with_cache(mock_fetch, db, tmp_path):
    mock_fetch.return_value = Transcript("v1", "transcript text here", "en")

    mock_summarizer = MagicMock()
    mock_summarizer.model = "gemini-2.0-flash"
    mock_summarizer.generate.return_value = "# Arrays\n\nThis is a summary of arrays."

    videos = [
        Video("v1", "Arrays Basics", "https://youtube.com/watch?v=v1", 1, None),
    ]
    output_dir = str(tmp_path / "output")

    # First run -- generates summary
    results = process_videos(videos, "DSA", "detailed", False, output_dir, "DSA Course", db, mock_summarizer)
    assert results["v1"] == "summarized"
    assert mock_summarizer.generate.call_count == 1
    assert os.path.exists(os.path.join(output_dir, "01-arrays-basics.md"))

    # Second run -- uses cache, no Gemini call
    mock_summarizer.generate.reset_mock()
    results2 = process_videos(videos, "DSA", "detailed", False, output_dir, "DSA Course", db, mock_summarizer)
    assert results2["v1"] == "summarized"
    assert mock_summarizer.generate.call_count == 0


@patch("yt_summarizer.cli.app.fetch_transcript")
def test_pipeline_no_transcript(mock_fetch, db, tmp_path):
    mock_fetch.return_value = None

    mock_summarizer = MagicMock()
    videos = [
        Video("v1", "No Captions Video", "https://youtube.com/watch?v=v1", 1, None),
    ]
    output_dir = str(tmp_path / "output")

    results = process_videos(videos, "DSA", "detailed", False, output_dir, None, db, mock_summarizer)
    assert results["v1"] == "no_transcript"
    mock_summarizer.generate.assert_not_called()


@patch("yt_summarizer.cli.app.fetch_transcript")
def test_force_regenerate(mock_fetch, db, tmp_path):
    mock_fetch.return_value = Transcript("v1", "transcript text", "en")

    mock_summarizer = MagicMock()
    mock_summarizer.model = "gemini-2.0-flash"
    mock_summarizer.generate.return_value = "# Summary v1"

    videos = [Video("v1", "Test", "https://youtube.com/watch?v=v1", 1, None)]
    output_dir = str(tmp_path / "output")

    # First run
    process_videos(videos, "DSA", "detailed", False, output_dir, None, db, mock_summarizer)
    assert mock_summarizer.generate.call_count == 1

    # Force run -- should call Gemini again
    mock_summarizer.generate.return_value = "# Summary v2"
    process_videos(videos, "DSA", "detailed", True, output_dir, None, db, mock_summarizer)
    assert mock_summarizer.generate.call_count == 2
