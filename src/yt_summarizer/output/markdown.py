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
