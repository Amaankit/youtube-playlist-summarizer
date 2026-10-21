# YouTube Playlist Summarizer -- Design Spec

**Date:** 2026-10-21
**Status:** Approved

---

## 1. Purpose

A Python CLI tool that takes a YouTube playlist (or single video) URL and an intent description, fetches transcripts, and generates per-video markdown summaries using Gemini LLM. Summaries include inline code with explanations when the video contains code. A SQLite cache prevents redundant API calls on re-runs.

---

## 2. Core Features

- **Input:** YouTube playlist URL or single video URL + intent (e.g., "DSA", "System Design")
- **Transcript fetching:** `youtube-transcript-api` for captions. Videos without captions are skipped and reported.
- **Summarization:** Gemini API (`gemini-2.0-flash`) with intent-aware prompts. Two detail levels: brief (300-500 words) and detailed (800-1500 words).
- **Code extraction:** Inline code blocks in markdown, placed at the relevant explanation point, with language tags and explanations. Mirrors the video's teaching flow.
- **Caching:** SQLite database stores playlists, videos, transcripts, and summaries. Cache key is `(video_id, intent, detail_level)`. Transcripts are cached once per video regardless of intent.
- **Output:** Individual `.md` files per video in a folder named after the playlist, plus an `index.md` table of contents.
- **CLI:** Supports both argument mode and interactive mode.

---

## 3. Project Structure

```
youtube-playlist-summarizer/
├── pyproject.toml
├── .env.example
├── .gitignore
├── main.py
├── src/
│   └── yt_summarizer/
│       ├── __init__.py
│       ├── cli/
│       │   ├── __init__.py
│       │   └── app.py              # argparse + interactive prompts
│       ├── youtube/
│       │   ├── __init__.py
│       │   ├── playlist.py         # Fetch playlist metadata & video list
│       │   └── transcript.py       # Fetch transcripts
│       ├── summarizer/
│       │   ├── __init__.py
│       │   ├── gemini_client.py    # Gemini API wrapper
│       │   └── prompts.py          # Prompt templates
│       ├── cache/
│       │   ├── __init__.py
│       │   └── db.py               # SQLite operations
│       ├── output/
│       │   ├── __init__.py
│       │   └── markdown.py         # Markdown file generation
│       └── models/
│           ├── __init__.py
│           └── video.py            # Dataclasses
├── output/                         # Default output directory (gitignored)
└── tests/
```

---

## 4. Dependencies

| Package | Purpose |
|---------|---------|
| `youtube-transcript-api` | Fetch video transcripts/captions |
| `yt-dlp` | Extract playlist metadata (titles, IDs, order) |
| `google-genai` | Gemini API client |
| `python-dotenv` | Load `.env` for API key |
| `rich` | CLI progress bars, tables, styled output |

---

## 5. Data Models

```python
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
    detail_level: str       # "brief" or "detailed"
    content: str            # Markdown with inline code
```

---

## 6. SQLite Cache Schema

```sql
CREATE TABLE playlists (
    playlist_id TEXT PRIMARY KEY,
    title TEXT,
    intent TEXT,
    video_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE videos (
    video_id TEXT PRIMARY KEY,
    playlist_id TEXT,
    title TEXT,
    url TEXT,
    position INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id)
);

CREATE TABLE transcripts (
    video_id TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES videos(video_id)
);

CREATE TABLE summaries (
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
```

---

## 7. Processing Flow

```
User Input (URL + intent + detail level)
        |
        v
   CLI / Args       Parse input, detect playlist vs single video
        |
        v
   YouTube module    Extract video list (yt-dlp) + transcripts
        |
        v
   Cache check       Check SQLite -- skip already processed videos
        |
        v
   Summarizer        Send transcript + intent + detail to Gemini
        |                -> returns markdown with inline code
        v
   Output            Write per-video .md files + index.md
        |
        v
   Cache store       Store transcript + summary in SQLite
```

---

## 8. CLI Interface

### Argument mode

```bash
# Single video
python main.py --video "URL" --intent "DSA" --detail detailed

# Full playlist
python main.py --playlist "URL" --intent "System Design"

# Force regenerate (ignore cache)
python main.py --playlist "URL" --intent "DSA" --force

# Custom output directory
python main.py --playlist "URL" --intent "DSA" --output ./my-notes/
```

### Interactive mode (no args)

Prompts for: URL, intent, detail level, force flag.

### Flags

| Flag | Description | Default |
|------|-------------|---------|
| `--video` | Single video URL | - |
| `--playlist` | Playlist URL | - |
| `--intent` | What the content is about | Required |
| `--detail` | `brief` or `detailed` | `detailed` |
| `--force` | Bypass cache | `False` |
| `--output` | Output directory | `./output/<title>/` |

Auto-detection: if neither `--video` nor `--playlist` is specified, the tool inspects the URL to determine which it is.

---

## 9. Prompt Strategy

Two prompt templates based on detail level, both parameterized with `{intent}`, `{title}`, and `{transcript}`.

**Brief:** Key points, 300-500 words, code inline if present.

**Detailed:** Follows the video's teaching structure, 800-1500 words, all code inline with explanations and complexity analysis, ends with Key Takeaways.

**Model:** `gemini-2.0-flash` (1M token context, fast, cost-effective). Configurable.

**Rate limiting:** Simple retry with exponential backoff.

---

## 10. Output Format

```
output/
└── <sanitized-playlist-title>/
    ├── index.md                    # TOC with links and status
    ├── 01-<sanitized-title>.md
    ├── 02-<sanitized-title>.md
    └── ...
```

- `index.md`: Table with video number, title (linked), and status (Summarized / No transcript)
- Per-video `.md`: Metadata header (URL, playlist, intent, detail) + summary content with inline code blocks
- Standalone videos: `output/<video-title>/`

---

## 11. Error Handling

- **No transcript available:** Skip video, mark as "No transcript" in index.md, log warning
- **Gemini API failure:** Retry with backoff (3 attempts), then skip and report
- **Invalid URL:** Clear error message, exit
- **Rate limiting:** Respect Gemini rate limits with delays between calls
- **Network errors:** Retry with backoff, then fail gracefully

---

## 12. Out of Scope

- No audio/video downloading or Whisper transcription
- No web search integration in summaries
- No PDF generation (can be added later)
- No playlist-wide summarization (only per-video)
- No concurrent/parallel API calls (sequential to respect rate limits)

---

## Self-Audit

### Citation ledger

N/A -- greenfield project, no existing codebase files to cite. All design decisions derived from the brainstorming session with the user. Dependencies (`youtube-transcript-api`, `yt-dlp`, `google-genai`, `python-dotenv`, `rich`) are well-known Python packages; versions to be pinned at implementation time after checking PyPI for latest stable.

### Cold-start trace

Fresh install: user clones repo, runs `pip install .`, creates `.env` with `GEMINI_API_KEY`. First run: `python main.py --playlist "URL" --intent "DSA"`.

1. CLI parses args, detects playlist URL
2. `yt-dlp` extracts playlist metadata (title, video IDs, titles, order) -- no download
3. SQLite DB file `yt_summarizer.db` does not exist -- `db.py` creates it with the schema (all 4 tables)
4. `playlists` table: INSERT playlist row (playlist_id, title, intent, video_count)
5. For each video in order:
   a. `videos` table: INSERT video row (video_id, playlist_id, title, url, position)
   b. `transcripts` table: SELECT by video_id -- no row found (cache miss)
   c. `youtube-transcript-api` fetches transcript text
   d. `transcripts` table: INSERT transcript row
   e. `summaries` table: SELECT by (video_id, intent, detail_level) -- no row found (cache miss)
   f. Gemini API call with prompt template + transcript -- returns markdown
   g. `summaries` table: INSERT summary row (content, model, generated_at)
   h. Write `output/<playlist-title>/NN-<video-title>.md`
6. After all videos: write `output/<playlist-title>/index.md` with status table
7. Print summary to console (N summarized, M skipped, etc.)

Re-run with same args: step 5b finds cached transcript (skip fetch), step 5e finds cached summary (skip Gemini call), step 5h regenerates markdown from cached content. Net cost: zero API calls.

Re-run with `--force`: skips cache checks at 5b and 5e, re-fetches and re-generates everything.

### Type↔Schema diff

| Dataclass field | SQLite column | Notes |
|---|---|---|
| `Video.video_id` | `videos.video_id` (TEXT PK) | Match |
| `Video.title` | `videos.title` (TEXT) | Match |
| `Video.url` | `videos.url` (TEXT) | Match |
| `Video.position` | `videos.position` (INTEGER) | Match |
| `Video.playlist_id` | `videos.playlist_id` (TEXT FK, nullable) | Match |
| `Transcript.video_id` | `transcripts.video_id` (TEXT PK/FK) | Match |
| `Transcript.text` | `transcripts.text` (TEXT NOT NULL) | Match |
| `Transcript.language` | `transcripts.language` (TEXT) | Match |
| `Summary.video_id` | `summaries.video_id` (TEXT FK) | Match |
| `Summary.title` | -- | Not stored in summaries table; derived from videos.title via JOIN at read time |
| `Summary.intent` | `summaries.intent` (TEXT) | Match |
| `Summary.detail_level` | `summaries.detail_level` (TEXT) | Match |
| `Summary.content` | `summaries.content` (TEXT) | Match |
| -- | `summaries.model` (TEXT) | Not in dataclass; stored for audit, populated at write time |
| -- | `summaries.id` (INTEGER PK) | Surrogate key, not in dataclass |
| -- | `summaries.generated_at` (TIMESTAMP) | Metadata, not in dataclass |
| -- | `*.created_at` / `*.fetched_at` | Metadata timestamps, not in dataclasses |

No fossils. `Summary.title` is intentionally not stored in summaries (avoids duplication; joined from videos table). `summaries.model` and timestamp columns are write-only metadata not needed in the dataclass.

### Seam obligations

Out-of-scope items and their obligations on this component:

- **PDF generation (future):** No obligation. Markdown files are the contract; any future PDF tool reads `.md` files. No reserved fields needed.
- **Playlist-wide summarization (future):** No obligation. Per-video summaries are self-contained. A future feature would read summaries from SQLite or markdown files.
- **Concurrent API calls (future):** No obligation now. The sequential processing loop can be swapped for async without schema or interface changes.
- **Whisper/audio transcription (future):** No obligation. The `Transcript` model and `transcripts` table store text regardless of source. A future audio pipeline would INSERT into the same table.

No cross-plan seams (single standalone project).

### Matrix cross-check

N/A -- no conformance matrix or test battery defined at design stage. Tests will be specified in the implementation plan. The only invariant to test: cache UNIQUE constraint on `(video_id, intent, detail_level)` ensures no duplicate summaries.

### Scale & contention

N/A -- single-user CLI tool, sequential processing, no shared resources. SQLite handles single-writer fine. Largest playlists on YouTube are ~500 videos; the bottleneck is Gemini API rate limits, not local storage or compute. No growth-forever tables (bounded by number of videos the user processes).

### Open ambiguities

None -- all forks resolved during brainstorming:
- Transcript source: `youtube-transcript-api` only (no Whisper/audio)
- LLM: Gemini only (user has only Gemini API key)
- Cache: SQLite (user chose over JSON)
- Output: Individual markdown per video in a folder
- CLI: Both argument and interactive mode
- Detail levels: brief/detailed, adaptive via flag
- Code in summaries: inline at relevant explanation point

### Pre-review gate ledger

- **G1 LAW-ONCE:** Swept. Cache key `(video_id, intent, detail_level)` stated once in Section 6 schema (UNIQUE constraint), referenced in Section 2 and Section 7. No contradictory restatements found.
- **G2 RULING-CARRIER:** All decisions name their carrier. "Cache key" = UNIQUE constraint on summaries table. "Detail level" = `--detail` CLI flag + `detail_level` column. "Intent" = `--intent` CLI flag + `intent` column.
- **G3 PER-ADAPTER WALK:** Single adapter (SQLite). No analogy assertions needed.
- **G4 NUMBERS-ADVERSARIAL:** No ceilings or floors specified. Single-user CLI; Gemini rate limits are the external constraint (handled by retry+backoff, not by design).
- **G5 BELOW-THE-TRAIT:** No "by construction" claims made. Cache uniqueness enforced by SQLite UNIQUE constraint (below language boundary).
- **G6 FRESH-EYES:** Design reviewed section-by-section with user approval at each step during brainstorming. This assembled document is the first full write.
