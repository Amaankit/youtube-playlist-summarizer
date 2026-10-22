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
