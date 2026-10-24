# YouTube Playlist Summarizer

A Python CLI tool that fetches YouTube video/playlist transcripts and generates per-video markdown summaries using Google Gemini LLM. Includes SQLite caching to avoid redundant API calls on re-runs.

## Features

- Summarize a **single video** or an **entire playlist**
- **Intent-aware** summaries (e.g., DSA, System Design, e-commerce)
- **Two detail levels**: brief (300-500 words) or detailed (800-1500 words)
- **Inline code extraction** with explanations when videos contain code
- **SQLite caching** -- transcripts and summaries are cached; re-runs are instant
- **CLI + Interactive mode** -- pass arguments or get prompted step by step
- **Rich CLI output** -- progress bars, colored status, styled prompts

## Prerequisites

- Python 3.10+
- [Gemini API key](https://aistudio.google.com/apikey)

## Setup

```bash
# Clone the repo
git clone https://github.com/Amaankit/youtube-playlist-summarizer.git
cd youtube-playlist-summarizer

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Add your Gemini API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Usage

### Single Video

```bash
python main.py --video "https://www.youtube.com/watch?v=VIDEO_ID" --intent "DSA" --detail detailed
```

### Full Playlist

```bash
python main.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --intent "System Design"
```

### Interactive Mode

```bash
python main.py
```

### All Options

| Flag | Description | Default |
|------|-------------|---------|
| `--video` | Single video URL | - |
| `--playlist` | Playlist URL | - |
| `--intent` | What the content is about (e.g., DSA, System Design) | Required |
| `--detail` | `brief` or `detailed` | `detailed` |
| `--force` | Bypass cache, regenerate everything | `False` |
| `--output` | Custom output directory | `./output/<title>/` |

## Output

Summaries are saved as markdown files:

```
output/
└── playlist-title/
    ├── index.md              # Table of contents with status
    ├── 01-video-title.md     # Per-video summary with inline code
    ├── 02-video-title.md
    └── ...
```

## Running Tests

```bash
source .venv/bin/activate
python -m pytest tests/ -v
```

## Project Structure

```
src/yt_summarizer/
├── cli/app.py              # CLI argument parsing + interactive prompts
├── youtube/
│   ├── playlist.py          # Playlist metadata extraction (yt-dlp)
│   └── transcript.py        # Transcript fetching (youtube-transcript-api)
├── summarizer/
│   ├── gemini_client.py     # Gemini API client with retry
│   └── prompts.py           # Brief/detailed prompt templates
├── cache/db.py              # SQLite caching layer
├── output/markdown.py       # Markdown file generation
└── models/video.py          # Video, Transcript, Summary dataclasses
```

## License

MIT
