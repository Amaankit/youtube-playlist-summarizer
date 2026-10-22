from unittest.mock import patch, MagicMock
from yt_summarizer.youtube.playlist import extract_playlist, extract_single_video, detect_url_type
from yt_summarizer.youtube.transcript import fetch_transcript


def test_detect_playlist_url():
    url = "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    assert detect_url_type(url) == "playlist"


def test_detect_video_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert detect_url_type(url) == "video"


def test_detect_video_url_with_playlist():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
    assert detect_url_type(url) == "video"


def test_detect_short_url():
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert detect_url_type(url) == "video"


def test_detect_invalid_url():
    url = "https://google.com"
    assert detect_url_type(url) == "unknown"


@patch("yt_summarizer.youtube.playlist.yt_dlp.YoutubeDL")
def test_extract_playlist(mock_ydl_class):
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {
        "id": "PLxyz",
        "title": "DSA Course",
        "entries": [
            {"id": "v1", "title": "Arrays", "webpage_url": "https://youtube.com/watch?v=v1"},
            {"id": "v2", "title": "Linked Lists", "webpage_url": "https://youtube.com/watch?v=v2"},
        ],
    }
    playlist_id, title, videos = extract_playlist(
        "https://youtube.com/playlist?list=PLxyz"
    )
    assert playlist_id == "PLxyz"
    assert title == "DSA Course"
    assert len(videos) == 2
    assert videos[0].video_id == "v1"
    assert videos[0].position == 1
    assert videos[1].video_id == "v2"
    assert videos[1].position == 2


@patch("yt_summarizer.youtube.playlist.yt_dlp.YoutubeDL")
def test_extract_single_video(mock_ydl_class):
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl_class.return_value.__exit__ = MagicMock(return_value=False)
    mock_ydl.extract_info.return_value = {
        "id": "v1",
        "title": "Binary Search",
        "webpage_url": "https://youtube.com/watch?v=v1",
    }
    video = extract_single_video("https://youtube.com/watch?v=v1")
    assert video.video_id == "v1"
    assert video.title == "Binary Search"
    assert video.position == 0
    assert video.playlist_id is None


@patch("yt_summarizer.youtube.transcript.YouTubeTranscriptApi")
def test_fetch_transcript_success(mock_api_class):
    mock_api = MagicMock()
    mock_api_class.return_value = mock_api
    mock_snippet = MagicMock()
    mock_snippet.text = "Hello"
    mock_snippet2 = MagicMock()
    mock_snippet2.text = "World"
    mock_api.fetch.return_value = [mock_snippet, mock_snippet2]
    result = fetch_transcript("v1")
    assert result is not None
    assert result.video_id == "v1"
    assert result.text == "Hello World"
    assert result.language == "en"


@patch("yt_summarizer.youtube.transcript.YouTubeTranscriptApi")
def test_fetch_transcript_not_available(mock_api_class):
    mock_api = MagicMock()
    mock_api_class.return_value = mock_api
    mock_api.fetch.side_effect = Exception("No transcript available")
    result = fetch_transcript("v1")
    assert result is None
