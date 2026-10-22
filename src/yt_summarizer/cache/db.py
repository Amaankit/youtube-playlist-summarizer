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
