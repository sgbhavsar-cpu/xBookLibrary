"""Audiobook streaming, metadata management, and listening progress synchronization."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Optional, Tuple

import aiosqlite

from backend.domain.audiobook import (
    AudioChapter,
    AudiobookMetadata,
    AudioListeningProgress,
    AudioListeningProgressUpdateRequest,
)
from backend.parsers.audio_parser import AudiobookParser
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class AudiobookService:
    """Service handling audio extraction, range-based streaming, and listening tracking."""

    def __init__(
        self,
        library_manager: LibraryManager,
        custom_columns_service: Optional[CustomColumnsService] = None,
    ):
        self.library_manager = library_manager
        self.custom_columns_service = custom_columns_service or CustomColumnsService(library_manager)
        self.audio_parser = AudiobookParser()

    async def _ensure_tables(self, conn: aiosqlite.Connection) -> None:
        """Ensures that the audiobook extension tables are created."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS x_audiobook_metadata (
                book_id INTEGER PRIMARY KEY,
                format TEXT NOT NULL,
                duration_seconds REAL NOT NULL DEFAULT 0.0,
                bitrate INTEGER,
                sample_rate INTEGER,
                channels INTEGER,
                narrator TEXT,
                chapters_json TEXT NOT NULL DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_audiobook_metadata_format ON x_audiobook_metadata (format)
        """)
        await conn.commit()

    async def get_audio_file(
        self, library_id: str, book_id: int, format_name: Optional[str] = None
    ) -> Tuple[Path, str, int]:
        """Locates the physical audio file on disk for a book.

        Returns (file_path, mime_type, file_size).
        """
        db_mgr = self.library_manager.get_database_manager(library_id)
        lib = self.library_manager.get_library(library_id)
        if not lib:
            raise ValueError(f"Library '{library_id}' not found")

        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            query = """
                SELECT b.path, d.format, d.name
                FROM books b
                JOIN data d ON b.id = d.book
                WHERE b.id = ? AND UPPER(d.format) IN ('M4B', 'MP3')
            """
            params = [book_id]
            if format_name:
                query += " AND UPPER(d.format) = UPPER(?)"
                params.append(format_name)

            query += " LIMIT 1"
            cursor = await conn.execute(query, tuple(params))
            row = await cursor.fetchone()
            if not row:
                raise FileNotFoundError(f"No audio file (M4B/MP3) found for book id {book_id}")

            book_rel_path = row["path"]
            fmt = row["format"].upper()
            file_name = row["name"] + "." + row["format"].lower()

            root_dir = getattr(lib, "path", getattr(lib, "root_path", ""))
            full_path = Path(root_dir) / book_rel_path / file_name
            if not full_path.exists():
                # Try finding any matching extension in directory
                dir_path = Path(root_dir) / book_rel_path
                candidates = list(dir_path.glob(f"*.{row['format'].lower()}"))
                if candidates:
                    full_path = candidates[0]
                else:
                    raise FileNotFoundError(f"Audio file missing on disk: {full_path}")

            mime_type = "audio/mp4" if fmt == "M4B" else "audio/mpeg"
            file_size = full_path.stat().st_size
            return full_path, mime_type, file_size

    async def get_audiobook_metadata(
        self, library_id: str, book_id: int
    ) -> Optional[AudiobookMetadata]:
        """Retrieves or parses technical metadata and chapter cues for an audiobook."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            # 1. Check existing record
            cursor = await conn.execute(
                """
                SELECT book_id, format, duration_seconds, bitrate, sample_rate, channels, narrator, chapters_json
                FROM x_audiobook_metadata
                WHERE book_id = ?
                """,
                (book_id,),
            )
            row = await cursor.fetchone()
            if row:
                raw_chapters = json.loads(row["chapters_json"] or "[]")
                chapters = [AudioChapter(**c) for c in raw_chapters]
                return AudiobookMetadata(
                    book_id=row["book_id"],
                    format=row["format"],
                    duration_seconds=float(row["duration_seconds"]),
                    bitrate=row["bitrate"],
                    sample_rate=row["sample_rate"],
                    channels=row["channels"],
                    narrator=row["narrator"],
                    chapters=chapters,
                )

        # 2. Not cached: extract from disk file
        try:
            file_path, _, _ = await self.get_audio_file(library_id, book_id)
        except FileNotFoundError:
            return None

        payload = self.audio_parser.parse(file_path)
        ext = file_path.suffix.lower()
        fmt = "M4B" if ext in (".m4b", ".mp4") else "MP3"

        # Extract mutagen info for bitrate, sample_rate, channels
        bitrate = None
        sample_rate = None
        channels = None
        duration = 0.0

        try:
            if fmt == "M4B":
                from mutagen.mp4 import MP4
                aud = MP4(file_path)
                duration = float(getattr(aud.info, "length", 0.0))
                bitrate = getattr(aud.info, "bitrate", None)
                sample_rate = getattr(aud.info, "sample_rate", None)
                channels = getattr(aud.info, "channels", None)
            else:
                from mutagen.mp3 import MP3
                aud = MP3(file_path)
                duration = float(getattr(aud.info, "length", 0.0))
                bitrate = getattr(aud.info, "bitrate", None)
                sample_rate = getattr(aud.info, "sample_rate", None)
                channels = getattr(aud.info, "channels", None)
        except Exception as err:
            logger.warning(f"Could not read detailed audio info: {err}")

        # Extract narrator from tags
        narrator = None
        for tag in payload.tags:
            if tag.startswith("Narrator: "):
                narrator = tag.replace("Narrator: ", "").strip()
                break

        # Convert TocItem entries to AudioChapter
        chapters: list[AudioChapter] = []
        for idx, item in enumerate(payload.table_of_contents):
            start_sec = 0.0
            if item.anchor_href and item.anchor_href.startswith("t="):
                try:
                    start_sec = float(item.anchor_href[2:])
                except ValueError:
                    start_sec = 0.0

            chapters.append(
                AudioChapter(
                    index=idx,
                    title=item.title,
                    start_time=start_sec,
                    end_time=duration,  # will refine next
                    duration=0.0,
                )
            )

        # Fix end_time and duration for contiguous chapters
        for i in range(len(chapters)):
            if i + 1 < len(chapters):
                chapters[i].end_time = chapters[i + 1].start_time
            else:
                chapters[i].end_time = duration
            chapters[i].duration = max(0.0, chapters[i].end_time - chapters[i].start_time)

        # Cache to database
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            chapters_json = json.dumps([c.model_dump() for c in chapters])
            await conn.execute(
                """
                INSERT OR REPLACE INTO x_audiobook_metadata
                (book_id, format, duration_seconds, bitrate, sample_rate, channels, narrator, chapters_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (book_id, fmt, duration, bitrate, sample_rate, channels, narrator, chapters_json),
            )
            await conn.commit()

        return AudiobookMetadata(
            book_id=book_id,
            format=fmt,
            duration_seconds=duration,
            bitrate=bitrate,
            sample_rate=sample_rate,
            channels=channels,
            narrator=narrator,
            chapters=chapters,
        )

    def parse_range_header(
        self, range_header: Optional[str], file_size: int
    ) -> Tuple[int, int, int]:
        """Parses 'Range: bytes=start-end'. Returns (start, end, content_length)."""
        if not range_header or not range_header.startswith("bytes="):
            return 0, file_size - 1, file_size

        range_val = range_header.replace("bytes=", "").strip()
        parts = range_val.split("-")
        start_str, end_str = parts[0], parts[1] if len(parts) > 1 else ""

        start = int(start_str) if start_str else 0
        end = int(end_str) if end_str else file_size - 1

        if start >= file_size:
            start = file_size - 1
        if end >= file_size:
            end = file_size - 1
        if end < start:
            end = start

        content_length = end - start + 1
        return start, end, content_length

    async def file_chunk_generator(
        self, file_path: Path, start: int, content_length: int, chunk_size: int = 65536
    ) -> AsyncGenerator[bytes, None]:
        """Asynchronously streams chunks from a file starting at offset `start`."""
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = content_length
            while remaining > 0:
                to_read = min(chunk_size, remaining)
                chunk = f.read(to_read)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    async def get_listening_progress(
        self, library_id: str, book_id: int
    ) -> Optional[AudioListeningProgress]:
        """Retrieves saved listening progress for an audiobook."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT id, book_id, format, location, progress_percent, total_seconds, last_read_at
                FROM x_reading_progress
                WHERE book_id = ? AND UPPER(format) IN ('M4B', 'MP3')
                ORDER BY last_read_at DESC LIMIT 1
                """,
                (book_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None

            location_raw = row["location"]
            current_time = 0.0
            chapter_idx = 0
            speed = 1.0

            try:
                data = json.loads(location_raw)
                current_time = float(data.get("current_time", 0.0))
                chapter_idx = int(data.get("current_chapter_index", 0))
                speed = float(data.get("playback_speed", 1.0))
            except Exception:
                if location_raw.startswith("t="):
                    try:
                        current_time = float(location_raw[2:])
                    except ValueError:
                        pass

            percent = float(row["progress_percent"])
            is_finished = percent >= 98.0

            last_read = datetime.now(timezone.utc)
            if row["last_read_at"]:
                try:
                    last_read = datetime.fromisoformat(row["last_read_at"])
                except Exception:
                    pass

            return AudioListeningProgress(
                book_id=book_id,
                format=row["format"],
                current_time=current_time,
                current_chapter_index=chapter_idx,
                progress_percent=percent,
                playback_speed=speed,
                is_finished=is_finished,
                last_listened_at=last_read,
            )

    async def save_listening_progress(
        self, library_id: str, book_id: int, req: AudioListeningProgressUpdateRequest
    ) -> AudioListeningProgress:
        """Saves listening position and synchronizes Calibre #read_status."""
        db_mgr = self.library_manager.get_database_manager(library_id)

        meta = await self.get_audiobook_metadata(library_id, book_id)
        fmt = meta.format if meta else "M4B"
        duration = meta.duration_seconds if meta else 0.0

        if req.progress_percent is not None:
            percent = float(req.progress_percent)
        elif duration > 0:
            percent = min(100.0, max(0.0, (req.current_time / duration) * 100.0))
        else:
            percent = 0.0

        is_finished = percent >= 98.0
        now_str = datetime.now(timezone.utc).isoformat()

        location_data = {
            "current_time": req.current_time,
            "current_chapter_index": req.current_chapter_index or 0,
            "playback_speed": req.playback_speed or 1.0,
        }
        location_str = json.dumps(location_data)

        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT id, total_seconds FROM x_reading_progress
                WHERE book_id = ? AND UPPER(format) = UPPER(?)
                """,
                (book_id, fmt),
            )
            existing = await cursor.fetchone()

            if existing:
                await conn.execute(
                    """
                    UPDATE x_reading_progress
                    SET location = ?, progress_percent = ?, total_seconds = total_seconds + 5, last_read_at = ?
                    WHERE id = ?
                    """,
                    (location_str, percent, now_str, existing["id"]),
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO x_reading_progress
                    (book_id, format, location, progress_percent, total_seconds, last_read_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (book_id, fmt, location_str, percent, 5, now_str),
                )
            await conn.commit()

        # Calibre custom columns sync
        try:
            custom_cols = await self.custom_columns_service.get_custom_columns(library_id)
            read_status_col = next((c for c in custom_cols if c.label == "read_status"), None)
            if read_status_col:
                status_val = "completed" if is_finished else ("reading" if percent > 0 else "unread")
                await self.custom_columns_service.set_book_custom_values(
                    library_id, book_id, {"read_status": status_val}
                )
        except Exception as e:
            logger.warning(f"Could not auto-sync #read_status for audiobook: {e}")

        return AudioListeningProgress(
            book_id=book_id,
            format=fmt,
            current_time=req.current_time,
            current_chapter_index=req.current_chapter_index or 0,
            progress_percent=percent,
            playback_speed=req.playback_speed or 1.0,
            is_finished=is_finished,
            last_listened_at=datetime.now(timezone.utc),
        )
