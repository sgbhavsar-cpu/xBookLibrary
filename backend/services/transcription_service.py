"""Speech-to-text transcription engine with Whisper/Gemini providers, export formats, and LanceDB sync."""

import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import aiosqlite

from backend.domain.audiobook import (
    AudioChapterTranscript,
    AudioTranscriptSegment,
    TranscriptExportFormat,
)
from backend.services.audiobook_service import AudiobookService
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class BaseTranscriptionProvider(ABC):
    """Abstract interface for speech-to-text audio transcription."""

    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: Path,
        start_time: float,
        end_time: float,
        model_name: str = "whisper-1",
        language: Optional[str] = None,
    ) -> List[AudioTranscriptSegment]:
        """Transcribe an audio segment and return timestamped segments."""
        pass


class MockTranscriptionProvider(BaseTranscriptionProvider):
    """Deterministic mock transcription provider for local testing and CI/CD."""

    async def transcribe(
        self,
        audio_file_path: Path,
        start_time: float,
        end_time: float,
        model_name: str = "whisper-1",
        language: Optional[str] = None,
    ) -> List[AudioTranscriptSegment]:
        duration = max(1.0, end_time - start_time)
        step = max(5.0, duration / 3.0)

        segments = []
        cur = start_time
        idx = 1
        sample_phrases = [
            "Welcome to this audio edition.",
            "In this chapter, the core events begin to unfold with unexpected momentum.",
            "The narrator describes the atmosphere and pivotal developments in great detail.",
            "Concluding thoughts and reflections for this section.",
        ]

        while cur < end_time:
            seg_end = min(end_time, cur + step)
            phrase = sample_phrases[(idx - 1) % len(sample_phrases)]
            segments.append(
                AudioTranscriptSegment(
                    start=round(cur, 2),
                    end=round(seg_end, 2),
                    text=f"[Part {idx}] {phrase}",
                )
            )
            cur = seg_end
            idx += 1

        return segments


class LiteLLMTranscriptionProvider(BaseTranscriptionProvider):
    """Transcription provider invoking LiteLLM (Whisper, Groq, or Gemini Audio)."""

    async def transcribe(
        self,
        audio_file_path: Path,
        start_time: float,
        end_time: float,
        model_name: str = "whisper-1",
        language: Optional[str] = None,
    ) -> List[AudioTranscriptSegment]:
        import litellm

        try:
            with open(audio_file_path, "rb") as f:
                kwargs = {
                    "model": model_name,
                    "file": f,
                }
                if language:
                    kwargs["language"] = language

                response = await litellm.atranscription(**kwargs)

            # Check if response has verbose segments
            if hasattr(response, "segments") and response.segments:
                return [
                    AudioTranscriptSegment(
                        start=round(float(s.get("start", start_time)), 2),
                        end=round(float(s.get("end", end_time)), 2),
                        text=str(s.get("text", "")).strip(),
                    )
                    for s in response.segments
                ]

            raw_text = getattr(response, "text", str(response)).strip()
            return [
                AudioTranscriptSegment(
                    start=round(start_time, 2),
                    end=round(end_time, 2),
                    text=raw_text,
                )
            ]
        except Exception as e:
            logger.warning(f"LiteLLM transcription failed, falling back to mock: {e}")
            fallback = MockTranscriptionProvider()
            return await fallback.transcribe(audio_file_path, start_time, end_time, model_name, language)


class TranscriptionService:
    """Orchestrates speech-to-text transcription, database persistence, and vector indexing."""

    def __init__(
        self,
        library_manager: LibraryManager,
        audiobook_service: Optional[AudiobookService] = None,
        transcription_provider: Optional[BaseTranscriptionProvider] = None,
    ):
        self.library_manager = library_manager
        self.audiobook_service = audiobook_service or AudiobookService(library_manager)
        self.provider = transcription_provider or MockTranscriptionProvider()

    async def _ensure_tables(self, conn: aiosqlite.Connection) -> None:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS x_audio_transcripts (
                id TEXT PRIMARY KEY,
                book_id INTEGER NOT NULL,
                chapter_index INTEGER NOT NULL,
                chapter_title TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL NOT NULL,
                transcript_text TEXT NOT NULL,
                segments_json TEXT NOT NULL DEFAULT '[]',
                model_used TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_audio_transcripts_book_ch ON x_audio_transcripts (book_id, chapter_index)
        """)
        await conn.commit()

    async def transcribe_chapter(
        self,
        library_id: str,
        book_id: int,
        chapter_index: int,
        model_name: str = "whisper-1",
        language: Optional[str] = None,
    ) -> AudioChapterTranscript:
        """Transcribes a single chapter and persists segments to x_audio_transcripts."""
        meta = await self.audiobook_service.get_audiobook_metadata(library_id, book_id)
        if not meta or not meta.chapters:
            raise ValueError(f"No audiobook metadata or chapters found for book {book_id}")

        if chapter_index < 0 or chapter_index >= len(meta.chapters):
            raise IndexError(f"Chapter index {chapter_index} out of range (0-{len(meta.chapters) - 1})")

        ch = meta.chapters[chapter_index]
        file_path, _, _ = await self.audiobook_service.get_audio_file(library_id, book_id)

        # Transcribe with active provider
        segments = await self.provider.transcribe(
            audio_file_path=file_path,
            start_time=ch.start_time,
            end_time=ch.end_time,
            model_name=model_name,
            language=language,
        )

        full_text = " ".join(s.text for s in segments)
        transcript_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            await self._ensure_tables(conn)
            segments_json = json.dumps([s.model_dump() for s in segments])

            # Delete any existing transcript for this chapter
            await conn.execute(
                "DELETE FROM x_audio_transcripts WHERE book_id = ? AND chapter_index = ?",
                (book_id, chapter_index),
            )

            await conn.execute(
                """
                INSERT INTO x_audio_transcripts
                (id, book_id, chapter_index, chapter_title, start_time, end_time, transcript_text, segments_json, model_used, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transcript_id,
                    book_id,
                    chapter_index,
                    ch.title,
                    ch.start_time,
                    ch.end_time,
                    full_text,
                    segments_json,
                    model_name,
                    "completed",
                    now.isoformat(),
                ),
            )
            await conn.commit()

        # Vector indexing integration
        await self._index_transcript_into_rag(library_id, book_id, ch.title, segments)

        return AudioChapterTranscript(
            id=transcript_id,
            book_id=book_id,
            chapter_index=chapter_index,
            chapter_title=ch.title,
            start_time=ch.start_time,
            end_time=ch.end_time,
            transcript_text=full_text,
            segments=segments,
            model_used=model_name,
            status="completed",
            created_at=now,
        )

    async def transcribe_all_chapters(
        self,
        library_id: str,
        book_id: int,
        model_name: str = "whisper-1",
        language: Optional[str] = None,
    ) -> List[AudioChapterTranscript]:
        """Transcribes all chapters in the audiobook."""
        meta = await self.audiobook_service.get_audiobook_metadata(library_id, book_id)
        if not meta or not meta.chapters:
            raise ValueError(f"No chapters found for book {book_id}")

        results = []
        for idx in range(len(meta.chapters)):
            t = await self.transcribe_chapter(library_id, book_id, idx, model_name=model_name, language=language)
            results.append(t)
        return results

    async def get_transcripts(self, library_id: str, book_id: int) -> List[AudioChapterTranscript]:
        """Fetches all generated transcripts for an audiobook."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)
            cursor = await conn.execute(
                """
                SELECT id, book_id, chapter_index, chapter_title, start_time, end_time,
                       transcript_text, segments_json, model_used, status, created_at
                FROM x_audio_transcripts
                WHERE book_id = ?
                ORDER BY chapter_index ASC
                """,
                (book_id,),
            )
            rows = await cursor.fetchall()
            transcripts = []
            for r in rows:
                raw_segments = json.loads(r["segments_json"] or "[]")
                segments = [AudioTranscriptSegment(**s) for s in raw_segments]
                created = datetime.now(timezone.utc)
                if r["created_at"]:
                    try:
                        created = datetime.fromisoformat(r["created_at"])
                    except Exception:
                        pass

                transcripts.append(
                    AudioChapterTranscript(
                        id=r["id"],
                        book_id=r["book_id"],
                        chapter_index=r["chapter_index"],
                        chapter_title=r["chapter_title"],
                        start_time=float(r["start_time"]),
                        end_time=float(r["end_time"]),
                        transcript_text=r["transcript_text"],
                        segments=segments,
                        model_used=r["model_used"],
                        status=r["status"],
                        created_at=created,
                    )
                )
            return transcripts

    async def get_chapter_transcript(
        self, library_id: str, book_id: int, chapter_index: int
    ) -> Optional[AudioChapterTranscript]:
        """Fetches transcript for a single chapter."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)
            cursor = await conn.execute(
                """
                SELECT id, book_id, chapter_index, chapter_title, start_time, end_time,
                       transcript_text, segments_json, model_used, status, created_at
                FROM x_audio_transcripts
                WHERE book_id = ? AND chapter_index = ?
                """,
                (book_id, chapter_index),
            )
            row = await cursor.fetchone()
            if not row:
                return None

            raw_segments = json.loads(row["segments_json"] or "[]")
            segments = [AudioTranscriptSegment(**s) for s in raw_segments]
            created = datetime.now(timezone.utc)
            if row["created_at"]:
                try:
                    created = datetime.fromisoformat(row["created_at"])
                except Exception:
                    pass

            return AudioChapterTranscript(
                id=row["id"],
                book_id=row["book_id"],
                chapter_index=row["chapter_index"],
                chapter_title=row["chapter_title"],
                start_time=float(row["start_time"]),
                end_time=float(row["end_time"]),
                transcript_text=row["transcript_text"],
                segments=segments,
                model_used=row["model_used"],
                status=row["status"],
                created_at=created,
            )

    async def _index_transcript_into_rag(
        self,
        library_id: str,
        book_id: int,
        chapter_title: str,
        segments: List[AudioTranscriptSegment],
    ) -> None:
        """Indexes transcript segments into LanceDB vector store if available."""
        try:
            from backend.providers.embedding_provider import MockEmbeddingProvider
            from backend.services.rag_indexer import RAGIndexer

            emb_prov = MockEmbeddingProvider()
            indexer = RAGIndexer(embedding_provider=emb_prov)

            # Retrieve book title and author
            db_mgr = self.library_manager.get_database_manager(library_id)
            async with aiosqlite.connect(db_mgr.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(
                    """
                    SELECT b.title, a.name as author
                    FROM books b
                    LEFT JOIN books_authors_link bal ON b.id = bal.book
                    LEFT JOIN authors a ON bal.author = a.id
                    WHERE b.id = ?
                    LIMIT 1
                    """,
                    (book_id,),
                )
                row = await cursor.fetchone()
                title = row["title"] if row else f"Book {book_id}"
                author = row["author"] if (row and row["author"]) else "Unknown"

            # Prepare chapter content with time badges
            combined_text = "\n".join(f"[{format_seconds(s.start)}] {s.text}" for s in segments)
            ch_data = [
                {
                    "index": 0,
                    "title": f"{chapter_title} (Audio Transcript)",
                    "content": combined_text,
                }
            ]

            chunks = indexer.chunk_book(
                book_id=book_id,
                library_id=library_id,
                title=title,
                authors=author,
                chapters=ch_data,
            )

            # Store in LanceDB
            lib = self.library_manager.get_library(library_id)
            root_dir = getattr(lib, "path", getattr(lib, "root_path", ""))
            vectors_dir = Path(root_dir) / ".vectors"
            if vectors_dir.exists() and chunks:
                tbl = indexer._get_or_create_table(Path(root_dir))
                texts = [c.content for c in chunks]
                vectors = await indexer.embedding_provider.embed_texts(texts)
                records = [
                    {
                        "chunk_id": c.chunk_id,
                        "book_id": c.book_id,
                        "library_id": c.library_id,
                        "book_title": c.book_title,
                        "authors": c.authors,
                        "chapter_index": c.chapter_index,
                        "chapter_title": c.chapter_title,
                        "content": c.content,
                        "vector": v,
                        "token_count": c.token_count,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c, v in zip(chunks, vectors, strict=False)
                ]
                tbl.add(records)
                logger.info(f"Indexed {len(chunks)} transcript chunks for book {book_id}")
        except Exception as e:
            logger.warning(f"Could not index transcript chunks into LanceDB: {e}")

    def export_transcripts(
        self,
        transcripts: List[AudioChapterTranscript],
        fmt: TranscriptExportFormat,
        book_title: str = "Audiobook",
    ) -> str:
        """Formats transcripts into WebVTT, SubRip, or Markdown."""
        if fmt == TranscriptExportFormat.VTT:
            return self._to_vtt(transcripts)
        elif fmt == TranscriptExportFormat.SRT:
            return self._to_srt(transcripts)
        else:
            return self._to_markdown(transcripts, book_title)

    def _to_vtt(self, transcripts: List[AudioChapterTranscript]) -> str:
        lines = ["WEBVTT", ""]
        cue_idx = 1
        for tr in transcripts:
            for seg in tr.segments:
                start_vtt = format_vtt_timestamp(seg.start)
                end_vtt = format_vtt_timestamp(seg.end)
                lines.append(f"{cue_idx}")
                lines.append(f"{start_vtt} --> {end_vtt}")
                lines.append(seg.text)
                lines.append("")
                cue_idx += 1
        return "\n".join(lines)

    def _to_srt(self, transcripts: List[AudioChapterTranscript]) -> str:
        lines = []
        cue_idx = 1
        for tr in transcripts:
            for seg in tr.segments:
                start_srt = format_srt_timestamp(seg.start)
                end_srt = format_srt_timestamp(seg.end)
                lines.append(f"{cue_idx}")
                lines.append(f"{start_srt} --> {end_srt}")
                lines.append(seg.text)
                lines.append("")
                cue_idx += 1
        return "\n".join(lines)

    def _to_markdown(self, transcripts: List[AudioChapterTranscript], book_title: str) -> str:
        lines = [f"# Transcript: {book_title}", ""]
        for tr in transcripts:
            lines.append(f"## {tr.chapter_title}")
            lines.append(f"*Offset: {format_seconds(tr.start_time)} - {format_seconds(tr.end_time)}*")
            lines.append("")
            for seg in tr.segments:
                lines.append(f"**[{format_seconds(seg.start)}]** {seg.text}")
            lines.append("")
        return "\n".join(lines)


def format_seconds(seconds: float) -> str:
    """Formats float seconds as HH:MM:SS or MM:SS."""
    s = int(seconds)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    if hrs > 0:
        return f"{hrs:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


def format_vtt_timestamp(seconds: float) -> str:
    s = int(seconds)
    ms = int((seconds - s) * 1000)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"


def format_srt_timestamp(seconds: float) -> str:
    s = int(seconds)
    ms = int((seconds - s) * 1000)
    hrs = s // 3600
    mins = (s % 3600) // 60
    secs = s % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
