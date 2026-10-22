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
