# YouTube Playlist Summarizer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that fetches YouTube playlist/video transcripts and generates per-video markdown summaries using Gemini LLM, with SQLite caching.

**Architecture:** Modular Python package (`yt_summarizer`) with six subpackages: `cli` (argument parsing + interactive mode), `youtube` (playlist metadata + transcript fetching), `summarizer` (Gemini client + prompt templates), `cache` (SQLite persistence), `output` (markdown generation), `models` (dataclasses). `main.py` orchestrates the pipeline.

**Tech Stack:** Python 3.10+, youtube-transcript-api 1.2.4, yt-dlp 2026.8.19, google-genai 2.32.0, python-dotenv, rich, pytest

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `main.py`
- Create: `src/yt_summarizer/__init__.py`
- Create: `src/yt_summarizer/cli/__init__.py`
- Create: `src/yt_summarizer/youtube/__init__.py`
- Create: `src/yt_summarizer/summarizer/__init__.py`
- Create: `src/yt_summarizer/cache/__init__.py`
- Create: `src/yt_summarizer/output/__init__.py`
- Create: `src/yt_summarizer/models/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "yt-summarizer"
version = "0.1.0"
description = "YouTube playlist/video transcript summarizer using Gemini LLM"
requires-python = ">=3.10"
dependencies = [
    "youtube-transcript-api>=1.2.4",
    "yt-dlp>=2026.8.19",
    "google-genai>=2.32.0",
    "python-dotenv>=1.0.0",
    "rich>=13.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
]

[project.scripts]
yt-summarizer = "yt_summarizer.cli.app:main"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create `.env.example`**

```
GEMINI_API_KEY=your_gemini_api_key_here
```

- [ ] **Step 3: Create `.gitignore`**

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.env
*.db
output/
.venv/
.pytest_cache/
```

- [ ] **Step 4: Create `main.py`**

```python
from yt_summarizer.cli.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Create all `__init__.py` files**

Create empty `__init__.py` in each package directory:
- `src/yt_summarizer/__init__.py`
- `src/yt_summarizer/cli/__init__.py`
- `src/yt_summarizer/youtube/__init__.py`
- `src/yt_summarizer/summarizer/__init__.py`
- `src/yt_summarizer/cache/__init__.py`
- `src/yt_summarizer/output/__init__.py`
- `src/yt_summarizer/models/__init__.py`
- `tests/__init__.py`

- [ ] **Step 6: Install in dev mode and verify**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed yt-summarizer with all dependencies

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .env.example .gitignore main.py src/ tests/
git commit -m "scaffold: project structure with dependencies"
```

---

### Task 2: Data Models + SQLite Cache

**Files:**
- Create: `src/yt_summarizer/models/video.py`
- Create: `src/yt_summarizer/cache/db.py`
- Create: `tests/test_models.py`
- Create: `tests/test_cache.py`

- [ ] **Step 1: Write tests for data models**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'yt_summarizer.models.video'`

- [ ] **Step 3: Implement data models**

Create `src/yt_summarizer/models/video.py`:

```python
from dataclasses import dataclass


@dataclass
class Video:
    video_id: str
    title: str
    url: str
    position: int
    playlist_id: str | None


@dataclass
class Transcript:
    video_id: str
    text: str
    language: str


@dataclass
class Summary:
    video_id: str
    title: str
    intent: str
    detail_level: str
    content: str
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_models.py -v`
Expected: 4 passed

- [ ] **Step 5: Write tests for SQLite cache**

Create `tests/test_cache.py`:

```python
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
```

- [ ] **Step 6: Run cache tests to verify they fail**

Run: `pytest tests/test_cache.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'yt_summarizer.cache.db'`

- [ ] **Step 7: Implement SQLite cache**

Create `src/yt_summarizer/cache/db.py`:

```python
import sqlite3
from yt_summarizer.models.video import Video, Transcript, Summary


class CacheDB:
    def __init__(self, db_path: str = "yt_summarizer.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_id TEXT PRIMARY KEY,
                title TEXT,
                intent TEXT,
                video_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                playlist_id TEXT,
                title TEXT,
                url TEXT,
                position INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)
            );

            CREATE TABLE IF NOT EXISTS transcripts (
                video_id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            );

            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                intent TEXT NOT NULL,
                detail_level TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                UNIQUE(video_id, intent, detail_level)
            );
        """)
        self.conn.commit()

    def list_tables(self) -> list[str]:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        return [row["name"] for row in cursor.fetchall()]

    def save_playlist(self, playlist_id: str, title: str, intent: str, video_count: int):
        self.conn.execute(
            """INSERT OR REPLACE INTO playlists (playlist_id, title, intent, video_count, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (playlist_id, title, intent, video_count),
        )
        self.conn.commit()

    def get_playlist(self, playlist_id: str) -> sqlite3.Row | None:
        cursor = self.conn.execute(
            "SELECT * FROM playlists WHERE playlist_id = ?", (playlist_id,)
        )
        return cursor.fetchone()

    def save_video(self, video: Video):
        self.conn.execute(
            """INSERT OR REPLACE INTO videos (video_id, playlist_id, title, url, position)
               VALUES (?, ?, ?, ?, ?)""",
            (video.video_id, video.playlist_id, video.title, video.url, video.position),
        )
        self.conn.commit()

    def get_video(self, video_id: str) -> Video | None:
        cursor = self.conn.execute(
            "SELECT * FROM videos WHERE video_id = ?", (video_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Video(
            video_id=row["video_id"],
            title=row["title"],
            url=row["url"],
            position=row["position"],
            playlist_id=row["playlist_id"],
        )

    def save_transcript(self, transcript: Transcript):
        self.conn.execute(
            """INSERT OR REPLACE INTO transcripts (video_id, text, language)
               VALUES (?, ?, ?)""",
            (transcript.video_id, transcript.text, transcript.language),
        )
        self.conn.commit()

    def get_transcript(self, video_id: str) -> Transcript | None:
        cursor = self.conn.execute(
            "SELECT * FROM transcripts WHERE video_id = ?", (video_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Transcript(
            video_id=row["video_id"],
            text=row["text"],
            language=row["language"],
        )

    def save_summary(self, summary: Summary, model: str):
        self.conn.execute(
            """INSERT OR REPLACE INTO summaries (video_id, intent, detail_level, content, model)
               VALUES (?, ?, ?, ?, ?)""",
            (summary.video_id, summary.intent, summary.detail_level, summary.content, model),
        )
        self.conn.commit()

    def get_summary(self, video_id: str, intent: str, detail_level: str) -> Summary | None:
        cursor = self.conn.execute(
            """SELECT s.*, v.title FROM summaries s
               JOIN videos v ON s.video_id = v.video_id
               WHERE s.video_id = ? AND s.intent = ? AND s.detail_level = ?""",
            (video_id, intent, detail_level),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Summary(
            video_id=row["video_id"],
            title=row["title"],
            intent=row["intent"],
            detail_level=row["detail_level"],
            content=row["content"],
        )

    def close(self):
        self.conn.close()
```

- [ ] **Step 8: Run all tests**

Run: `pytest tests/test_models.py tests/test_cache.py -v`
Expected: All passed

- [ ] **Step 9: Commit**

```bash
git add src/yt_summarizer/models/video.py src/yt_summarizer/cache/db.py tests/test_models.py tests/test_cache.py
git commit -m "feat: data models and SQLite cache layer"
```

---

### Task 3: YouTube Playlist & Transcript Fetching

**Files:**
- Create: `src/yt_summarizer/youtube/playlist.py`
- Create: `src/yt_summarizer/youtube/transcript.py`
- Create: `tests/test_youtube.py`

- [ ] **Step 1: Write tests for playlist extraction**

Create `tests/test_youtube.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from yt_summarizer.youtube.playlist import extract_playlist, extract_single_video, detect_url_type
from yt_summarizer.youtube.transcript import fetch_transcript
from yt_summarizer.models.video import Video


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_youtube.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement playlist extraction**

Create `src/yt_summarizer/youtube/playlist.py`:

```python
from urllib.parse import urlparse, parse_qs
import yt_dlp
from yt_summarizer.models.video import Video


def detect_url_type(url: str) -> str:
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if hostname in ("youtu.be",):
        return "video"
    if "youtube.com" not in hostname and "youtu.be" not in hostname:
        return "unknown"
    params = parse_qs(parsed.query)
    if parsed.path == "/playlist" and "list" in params:
        return "playlist"
    if "v" in params or parsed.path.startswith("/shorts/"):
        return "video"
    return "unknown"


def extract_playlist(url: str) -> tuple[str, str, list[Video]]:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    playlist_id = info["id"]
    title = info.get("title", "Untitled Playlist")
    entries = info.get("entries", [])

    videos = []
    for i, entry in enumerate(entries, start=1):
        if entry is None:
            continue
        video_id = entry["id"]
        videos.append(
            Video(
                video_id=video_id,
                title=entry.get("title", "Untitled"),
                url=entry.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"),
                position=i,
                playlist_id=playlist_id,
            )
        )
    return playlist_id, title, videos


def extract_single_video(url: str) -> Video:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    video_id = info["id"]
    return Video(
        video_id=video_id,
        title=info.get("title", "Untitled"),
        url=info.get("webpage_url", f"https://www.youtube.com/watch?v={video_id}"),
        position=0,
        playlist_id=None,
    )
```

- [ ] **Step 4: Implement transcript fetching**

Create `src/yt_summarizer/youtube/transcript.py`:

```python
import logging
from youtube_transcript_api import YouTubeTranscriptApi
from yt_summarizer.models.video import Transcript

log = logging.getLogger(__name__)


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> Transcript | None:
    if languages is None:
        languages = ["en"]
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=languages)
        text = " ".join(snippet.text for snippet in fetched)
        return Transcript(video_id=video_id, text=text, language=languages[0])
    except Exception as e:
        log.warning("Could not fetch transcript for %s: %s", video_id, e)
        return None
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_youtube.py -v`
Expected: All passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_summarizer/youtube/ tests/test_youtube.py
git commit -m "feat: YouTube playlist extraction and transcript fetching"
```

---

### Task 4: Gemini Summarizer

**Files:**
- Create: `src/yt_summarizer/summarizer/prompts.py`
- Create: `src/yt_summarizer/summarizer/gemini_client.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: Write tests**

Create `tests/test_summarizer.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from yt_summarizer.summarizer.prompts import build_prompt
from yt_summarizer.summarizer.gemini_client import GeminiSummarizer


def test_build_prompt_brief():
    prompt = build_prompt(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="brief",
    )
    assert "Binary Search" in prompt
    assert "DSA" in prompt
    assert "This video explains binary search..." in prompt
    assert "300-500 words" in prompt


def test_build_prompt_detailed():
    prompt = build_prompt(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="detailed",
    )
    assert "Binary Search" in prompt
    assert "DSA" in prompt
    assert "800-1500 words" in prompt
    assert "Key Takeaways" in prompt


@patch("yt_summarizer.summarizer.gemini_client.genai")
def test_gemini_summarizer_generate(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_response = MagicMock()
    mock_response.text = "# Binary Search\n\nThis is a summary..."
    mock_client.models.generate_content.return_value = mock_response

    summarizer = GeminiSummarizer(api_key="fake-key")
    result = summarizer.generate(
        title="Binary Search",
        intent="DSA",
        transcript="This video explains binary search...",
        detail_level="detailed",
    )
    assert result == "# Binary Search\n\nThis is a summary..."
    mock_client.models.generate_content.assert_called_once()


@patch("yt_summarizer.summarizer.gemini_client.genai")
def test_gemini_summarizer_returns_none_on_failure(mock_genai):
    mock_client = MagicMock()
    mock_genai.Client.return_value = mock_client
    mock_client.models.generate_content.side_effect = Exception("API error")

    summarizer = GeminiSummarizer(api_key="fake-key")
    result = summarizer.generate(
        title="Binary Search",
        intent="DSA",
        transcript="text",
        detail_level="brief",
    )
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_summarizer.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement prompt templates**

Create `src/yt_summarizer/summarizer/prompts.py`:

```python
BRIEF_TEMPLATE = """You are summarizing a YouTube video transcript.

Context: This video is part of a {intent} series.
Video Title: {title}

Instructions:
- Summarize the key points in 300-500 words
- If the video contains code, include it inline as markdown code blocks with the language specified
- Pair each code block with a brief explanation of what it does
- Use markdown formatting with headers for sections

Transcript:
{transcript}"""

DETAILED_TEMPLATE = """You are creating a detailed study note from a YouTube video transcript.

Context: This video is part of a {intent} series.
Video Title: {title}

Instructions:
- Follow the video's teaching structure and flow
- Cover all concepts explained in the video thoroughly (800-1500 words)
- If the video contains code, include ALL code inline as markdown code blocks with the language specified, placed exactly where the concept is explained — just like the video teaches it
- For each code block, explain the logic, approach, and complexity (time/space) if applicable
- Use markdown headers, bullet points, and bold for key terms
- End with a "Key Takeaways" section

Transcript:
{transcript}"""


def build_prompt(title: str, intent: str, transcript: str, detail_level: str) -> str:
    template = DETAILED_TEMPLATE if detail_level == "detailed" else BRIEF_TEMPLATE
    return template.format(title=title, intent=intent, transcript=transcript)
```

- [ ] **Step 4: Implement Gemini client**

Create `src/yt_summarizer/summarizer/gemini_client.py`:

```python
import logging
import time
from google import genai

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3


class GeminiSummarizer:
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(
        self, title: str, intent: str, transcript: str, detail_level: str
    ) -> str | None:
        from yt_summarizer.summarizer.prompts import build_prompt

        prompt = build_prompt(title, intent, transcript, detail_level)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.models.generate_content(
                    model=self.model, contents=prompt
                )
                return response.text
            except Exception as e:
                log.warning(
                    "Gemini API attempt %d/%d failed for '%s': %s",
                    attempt + 1,
                    MAX_RETRIES,
                    title,
                    e,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** (attempt + 1))

        log.error("All %d attempts failed for '%s'", MAX_RETRIES, title)
        return None
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_summarizer.py -v`
Expected: All passed

- [ ] **Step 6: Commit**

```bash
git add src/yt_summarizer/summarizer/ tests/test_summarizer.py
git commit -m "feat: Gemini summarizer with prompt templates and retry logic"
```

---

### Task 5: Markdown Output Generator

**Files:**
- Create: `src/yt_summarizer/output/markdown.py`
- Create: `tests/test_output.py`

- [ ] **Step 1: Write tests**

Create `tests/test_output.py`:

```python
import os
import pytest
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_output.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement markdown output**

Create `src/yt_summarizer/output/markdown.py`:

```python
import os
import re
from datetime import date
from yt_summarizer.models.video import Video, Summary


def sanitize_filename(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = name.strip("-")
    return name


def write_video_markdown(
    video: Video, summary: Summary, output_dir: str, playlist_title: str | None = None
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{video.position:02d}-{sanitize_filename(video.title)}.md"
    filepath = os.path.join(output_dir, filename)

    lines = [
        f"# {video.title}",
        "",
        f"**Video:** {video.url}  ",
    ]
    if playlist_title:
        lines.append(f"**Playlist:** {playlist_title}  ")
    lines.extend(
        [
            f"**Intent:** {summary.intent}  ",
            f"**Detail:** {summary.detail_level.capitalize()}  ",
            "",
            "---",
            "",
            summary.content,
            "",
        ]
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


def write_index_markdown(
    output_dir: str,
    playlist_title: str,
    intent: str,
    videos: list[Video],
    results: dict[str, str],
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "index.md")

    summarized = sum(1 for s in results.values() if s == "summarized")
    skipped = sum(1 for s in results.values() if s != "summarized")

    lines = [
        f"# {playlist_title}",
        "",
        f"**Intent:** {intent}  ",
        f"**Videos:** {len(videos)}  ",
        f"**Summarized:** {summarized}  ",
        f"**Skipped:** {skipped}  ",
        f"**Generated:** {date.today().isoformat()}  ",
        "",
        "## Videos",
        "",
        "| # | Title | Status |",
        "|---|-------|--------|",
    ]

    for video in videos:
        status = results.get(video.video_id, "unknown")
        fname = f"{video.position:02d}-{sanitize_filename(video.title)}.md"
        if status == "summarized":
            lines.append(f"| {video.position} | [{video.title}](./{fname}) | Summarized |")
        else:
            lines.append(f"| {video.position} | {video.title} | No transcript |")

    lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_output.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/yt_summarizer/output/ tests/test_output.py
git commit -m "feat: markdown output generator with index and per-video files"
```

---

### Task 6: CLI Interface

**Files:**
- Create: `src/yt_summarizer/cli/app.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write tests**

Create `tests/test_cli.py`:

```python
import pytest
from unittest.mock import patch
from yt_summarizer.cli.app import parse_args


def test_parse_args_playlist():
    args = parse_args(["--playlist", "https://youtube.com/playlist?list=PL1", "--intent", "DSA"])
    assert args.playlist == "https://youtube.com/playlist?list=PL1"
    assert args.intent == "DSA"
    assert args.detail == "detailed"
    assert args.force is False
    assert args.video is None


def test_parse_args_video():
    args = parse_args(["--video", "https://youtube.com/watch?v=abc", "--intent", "DSA"])
    assert args.video == "https://youtube.com/watch?v=abc"
    assert args.intent == "DSA"


def test_parse_args_detail_brief():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--detail", "brief"])
    assert args.detail == "brief"


def test_parse_args_force():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--force"])
    assert args.force is True


def test_parse_args_output():
    args = parse_args(["--video", "URL", "--intent", "DSA", "--output", "./my-notes"])
    assert args.output == "./my-notes"


def test_parse_args_no_args_returns_none():
    args = parse_args([])
    assert args.playlist is None
    assert args.video is None
    assert args.intent is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement CLI**

Create `src/yt_summarizer/cli/app.py`:

```python
import argparse
import sys
import os
import logging

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, Confirm

from yt_summarizer.youtube.playlist import detect_url_type, extract_playlist, extract_single_video
from yt_summarizer.youtube.transcript import fetch_transcript
from yt_summarizer.summarizer.gemini_client import GeminiSummarizer
from yt_summarizer.cache.db import CacheDB
from yt_summarizer.output.markdown import sanitize_filename, write_video_markdown, write_index_markdown
from yt_summarizer.models.video import Summary

console = Console()
log = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="YouTube Playlist Summarizer - Generate markdown summaries from YouTube videos using Gemini"
    )
    parser.add_argument("--video", help="Single YouTube video URL")
    parser.add_argument("--playlist", help="YouTube playlist URL")
    parser.add_argument("--intent", help="What the content is about (e.g., DSA, System Design)")
    parser.add_argument("--detail", choices=["brief", "detailed"], default="detailed",
                        help="Summary detail level (default: detailed)")
    parser.add_argument("--force", action="store_true", help="Force regeneration, bypass cache")
    parser.add_argument("--output", help="Output directory (default: ./output/<title>/)")
    return parser.parse_args(argv)


def interactive_prompt() -> dict:
    console.print("\n[bold cyan]YouTube Playlist Summarizer[/bold cyan]")
    console.print("[dim]─────────────────────────────────[/dim]\n")

    url = Prompt.ask("[bold]Enter YouTube URL[/bold]")
    intent = Prompt.ask("[bold]What is this playlist/video about?[/bold] (e.g., DSA, System Design)")
    detail = Prompt.ask("[bold]Detail level[/bold]", choices=["brief", "detailed"], default="detailed")
    force = Confirm.ask("[bold]Force regenerate cached summaries?[/bold]", default=False)

    return {"url": url, "intent": intent, "detail": detail, "force": force}


def process_videos(videos, intent, detail, force, output_dir, playlist_title, db, summarizer):
    results = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing videos...", total=len(videos))

        for video in videos:
            db.save_video(video)

            # Check transcript cache
            transcript = None if force else db.get_transcript(video.video_id)
            if transcript is None:
                transcript = fetch_transcript(video.video_id)
                if transcript is not None:
                    db.save_transcript(transcript)

            if transcript is None:
                results[video.video_id] = "no_transcript"
                progress.update(task, advance=1, description=f"[yellow]Skipped:[/yellow] {video.title}")
                continue

            # Check summary cache
            cached_summary = None if force else db.get_summary(video.video_id, intent, detail)
            if cached_summary is not None:
                write_video_markdown(video, cached_summary, output_dir, playlist_title)
                results[video.video_id] = "summarized"
                progress.update(task, advance=1, description=f"[green]Cached:[/green] {video.title}")
                continue

            # Generate summary via Gemini
            content = summarizer.generate(
                title=video.title,
                intent=intent,
                transcript=transcript.text,
                detail_level=detail,
            )
            if content is None:
                results[video.video_id] = "failed"
                progress.update(task, advance=1, description=f"[red]Failed:[/red] {video.title}")
                continue

            summary = Summary(
                video_id=video.video_id,
                title=video.title,
                intent=intent,
                detail_level=detail,
                content=content,
            )
            db.save_summary(summary, model=summarizer.model)
            write_video_markdown(video, summary, output_dir, playlist_title)
            results[video.video_id] = "summarized"
            progress.update(task, advance=1, description=f"[green]Done:[/green] {video.title}")

    return results


def main():
    load_dotenv()
    logging.basicConfig(level=logging.WARNING)

    args = parse_args()

    # Interactive mode if no URL provided
    if args.video is None and args.playlist is None and args.intent is None:
        inputs = interactive_prompt()
        url = inputs["url"]
        intent = inputs["intent"]
        detail = inputs["detail"]
        force = inputs["force"]
    else:
        url = args.video or args.playlist
        intent = args.intent
        detail = args.detail
        force = args.force

        if url is None:
            console.print("[red]Error: Provide --video or --playlist URL[/red]")
            sys.exit(1)
        if intent is None:
            console.print("[red]Error: --intent is required[/red]")
            sys.exit(1)

    # Detect URL type
    url_type = detect_url_type(url)
    if args.video:
        url_type = "video"
    elif args.playlist:
        url_type = "playlist"

    if url_type == "unknown":
        console.print("[red]Error: Could not detect URL type. Use --video or --playlist flag.[/red]")
        sys.exit(1)

    # Check API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        console.print("[red]Error: GEMINI_API_KEY not set. Add it to .env file.[/red]")
        sys.exit(1)

    db = CacheDB()
    summarizer = GeminiSummarizer(api_key=api_key)

    if url_type == "playlist":
        console.print(f"\n[bold]Fetching playlist info...[/bold]")
        playlist_id, playlist_title, videos = extract_playlist(url)
        console.print(f"[green]Found {len(videos)} videos in \"{playlist_title}\"[/green]\n")

        db.save_playlist(playlist_id, playlist_title, intent, len(videos))

        output_dir = args.output or os.path.join("output", sanitize_filename(playlist_title))
        results = process_videos(videos, intent, detail, force, output_dir, playlist_title, db, summarizer)

        write_index_markdown(output_dir, playlist_title, intent, videos, results)

    else:
        console.print(f"\n[bold]Fetching video info...[/bold]")
        video = extract_single_video(url)
        console.print(f"[green]Video: \"{video.title}\"[/green]\n")

        output_dir = args.output or os.path.join("output", sanitize_filename(video.title))
        results = process_videos([video], intent, detail, force, output_dir, None, db, summarizer)

    # Print final summary
    summarized = sum(1 for s in results.values() if s == "summarized")
    skipped = sum(1 for s in results.values() if s != "summarized")
    console.print(f"\n[bold green]Done![/bold green] {summarized} summarized, {skipped} skipped")
    console.print(f"[dim]Output: {output_dir}/[/dim]")

    db.close()
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_cli.py -v`
Expected: All passed

- [ ] **Step 5: Commit**

```bash
git add src/yt_summarizer/cli/app.py tests/test_cli.py
git commit -m "feat: CLI with argument parsing and interactive mode"
```

---

### Task 7: Integration Smoke Test

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration test (mocked external calls)**

Create `tests/test_integration.py`:

```python
import os
import pytest
from unittest.mock import patch, MagicMock
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
        Video("v1", "Arrays Basics", "https://youtube.com/watch?v=v1", 1, "PL1"),
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
```

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: integration tests for full pipeline with caching"
```

---

### Task 8: Final Wiring & Manual Test

- [ ] **Step 1: Update `main.py`**

Verify `main.py` has:

```python
from yt_summarizer.cli.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `.env` file with real key**

```bash
cp .env.example .env
# Edit .env and add your real GEMINI_API_KEY
```

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Manual smoke test with a real single video**

Run: `python main.py --video "https://www.youtube.com/watch?v=MqYLmIQ3Fvw" --intent "DSA" --detail brief`
Expected: Generates markdown file in `output/` directory

- [ ] **Step 5: Manual smoke test with interactive mode**

Run: `python main.py`
Expected: Interactive prompts appear and work correctly

- [ ] **Step 6: Final commit**

```bash
git add -A
git commit -m "feat: complete YouTube playlist summarizer v0.1.0"
```
