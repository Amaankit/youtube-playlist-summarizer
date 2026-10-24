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
        "noplaylist": True,
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
