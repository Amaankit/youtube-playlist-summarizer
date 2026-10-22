import os
from yt_summarizer.output.markdown import (
    sanitize_filename,
    write_video_markdown,
    write_index_markdown,
)
from yt_summarizer.models.video import Video, Summary


def test_sanitize_filename():
    assert sanitize_filename("Hello World!") == "hello-world"
    assert sanitize_filename("DSA: Arrays & Strings") == "dsa-arrays-strings"
    assert sanitize_filename("  Spaces  ") == "spaces"
    assert sanitize_filename("C++ Tutorial #1") == "c-tutorial-1"


def test_write_video_markdown(tmp_path):
    output_dir = str(tmp_path / "output")
    video = Video("v1", "Binary Search", "https://youtube.com/watch?v=v1", 1, "PL1")
    summary = Summary("v1", "Binary Search", "DSA", "detailed", "# Binary Search\n\nContent here")

    filepath = write_video_markdown(video, summary, output_dir, "My Playlist")
    assert os.path.exists(filepath)
    content = open(filepath).read()
    assert "Binary Search" in content
    assert "https://youtube.com/watch?v=v1" in content
    assert "DSA" in content
    assert "Content here" in content
    assert filepath.endswith("01-binary-search.md")


def test_write_index_markdown(tmp_path):
    output_dir = str(tmp_path / "output")
    os.makedirs(output_dir, exist_ok=True)
    videos = [
        Video("v1", "Arrays", "https://youtube.com/watch?v=v1", 1, "PL1"),
        Video("v2", "Linked Lists", "https://youtube.com/watch?v=v2", 2, "PL1"),
        Video("v3", "Trees", "https://youtube.com/watch?v=v3", 3, "PL1"),
    ]
    results = {
        "v1": "summarized",
        "v2": "summarized",
        "v3": "no_transcript",
    }

    filepath = write_index_markdown(
        output_dir=output_dir,
        playlist_title="DSA Course",
        intent="DSA",
        videos=videos,
        results=results,
    )
    assert os.path.exists(filepath)
    content = open(filepath).read()
    assert "DSA Course" in content
    assert "Arrays" in content
    assert "Linked Lists" in content
    assert "No transcript" in content
