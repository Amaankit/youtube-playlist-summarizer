import logging
from youtube_transcript_api import YouTubeTranscriptApi
from yt_summarizer.models.video import Transcript

log = logging.getLogger(__name__)


def fetch_transcript(video_id: str, languages: list[str] | None = None) -> Transcript | None:
    if languages is None:
        languages = ["en", "hi", "en-IN"]
    api = YouTubeTranscriptApi()
    # Try requested languages first
    try:
        fetched = api.fetch(video_id, languages=languages)
        text = " ".join(snippet.text for snippet in fetched)
        return Transcript(video_id=video_id, text=text, language=languages[0])
    except Exception:
        pass
    # Fallback: grab whatever transcript is available
    try:
        transcript_list = api.list(video_id)
        for t in transcript_list:
            fetched = t.fetch()
            text = " ".join(snippet.text for snippet in fetched)
            return Transcript(video_id=video_id, text=text, language=t.language_code)
    except Exception as e:
        log.warning("Could not fetch transcript for %s: %s", video_id, e)
        return None
