from yt_summarizer.models.video import Video, Transcript, Summary


def test_video_creation():
    video = Video(
        video_id="abc123",
        title="Binary Search",
        url="https://youtube.com/watch?v=abc123",
        position=1,
        playlist_id="PLxyz",
    )
    assert video.video_id == "abc123"
    assert video.title == "Binary Search"
    assert video.position == 1
    assert video.playlist_id == "PLxyz"


def test_video_standalone():
    video = Video(
        video_id="abc123",
        title="Binary Search",
        url="https://youtube.com/watch?v=abc123",
        position=0,
        playlist_id=None,
    )
    assert video.playlist_id is None


def test_transcript_creation():
    transcript = Transcript(
        video_id="abc123",
        text="Hello world this is a transcript",
        language="en",
    )
    assert transcript.video_id == "abc123"
    assert transcript.text == "Hello world this is a transcript"
    assert transcript.language == "en"


def test_summary_creation():
    summary = Summary(
        video_id="abc123",
        title="Binary Search",
        intent="DSA",
        detail_level="detailed",
        content="# Binary Search\n\nThis video covers...",
    )
    assert summary.video_id == "abc123"
    assert summary.intent == "DSA"
    assert summary.detail_level == "detailed"
    assert summary.content.startswith("# Binary Search")
