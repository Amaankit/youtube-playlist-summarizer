# YouTube Playlist Summarizer

A Python CLI tool that fetches YouTube video/playlist transcripts and generates per-video markdown summaries using LLMs (Groq or Gemini). Includes SQLite caching to avoid redundant API calls on re-runs.

## Features

- Summarize a **single video** or an **entire playlist**
- **Multiple LLM providers**: Groq (default, 14,400 req/day free) and Gemini
- **Multi-language transcripts**: auto-detects Hindi, English, and falls back to any available language
- **Intent-aware** summaries (e.g., DSA, System Design, e-commerce)
- **Two detail levels**: brief (300-500 words) or detailed (800-1500 words)
- **Inline code extraction** with explanations when videos contain code
- **SQLite caching** -- transcripts and summaries are cached; re-runs are instant
- **CLI + Interactive mode** -- pass arguments or get prompted step by step
- **Rich CLI output** -- progress bars, colored status, styled prompts

## Prerequisites

- Python 3.10+
- API key from one of:
  - [Groq](https://console.groq.com/keys) (recommended -- free, 14,400 requests/day, no credit card)
  - [Gemini](https://aistudio.google.com/apikey) (free but only 20 requests/day)

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

# Add your API key(s)
cp .env.example .env
# Edit .env and add GROQ_API_KEY and/or GEMINI_API_KEY
```

### YouTube Cookies (if IP-blocked)

If YouTube blocks transcript requests (common after many requests), export your browser cookies:

1. Install [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) in Chrome
2. Go to youtube.com (logged in)
3. Export cookies and save as `cookies.txt` in the project root
4. The tool auto-detects and uses it

## Usage

### Single Video

```bash
python main.py --video "https://www.youtube.com/watch?v=VIDEO_ID" --intent "DSA"
```

### Full Playlist

```bash
python main.py --playlist "https://www.youtube.com/playlist?list=PLAYLIST_ID" --intent "System Design"
```

### Interactive Mode

```bash
python main.py
```

### Choose Provider

```bash
# Groq (default -- fast, high free-tier limit)
python main.py --playlist "URL" --intent "DSA" --provider groq

# Gemini
python main.py --playlist "URL" --intent "DSA" --provider gemini
```

### All Options

| Flag | Description | Default |
|------|-------------|---------|
| `--video` | Single video URL | - |
| `--playlist` | Playlist URL | - |
| `--intent` | What the content is about (e.g., DSA, System Design) | Required |
| `--detail` | `brief` or `detailed` | `detailed` |
| `--provider` | `groq` or `gemini` | `groq` |
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
│   ├── groq_client.py       # Groq API client (llama-3.3-70b-versatile)
│   ├── gemini_client.py     # Gemini API client (gemini-3.8-flash)
│   └── prompts.py           # Brief/detailed prompt templates
├── cache/db.py              # SQLite caching layer
├── output/markdown.py       # Markdown file generation
└── models/video.py          # Video, Transcript, Summary dataclasses
```

## License

MIT
