"""Unit tests for TranscriptionService."""

from pathlib import Path
import pytest
import aiosqlite

from backend.domain.audiobook import TranscriptExportFormat
from backend.domain.entities import Library
from backend.services.audiobook_service import AudiobookService
from backend.services.transcription_service import (
    MockTranscriptionProvider,
    TranscriptionService,
    format_seconds,
    format_srt_timestamp,
    format_vtt_timestamp,
)
from tests.unit.parsers.test_audio_parser import create_minimal_mp3


@pytest.fixture
async def sample_audio_library(tmp_path: Path):
    lib_path = tmp_path / "AudioLibTranscribe"
    lib_path.mkdir(parents=True, exist_ok=True)
    db_path = lib_path / "metadata.db"

    from backend.database.schema import CALIBRE_SCHEMA_DDL
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript(CALIBRE_SCHEMA_DDL)

        # Insert sample author and book
        await conn.execute("INSERT INTO authors (id, name, sort) VALUES (1, 'Arthur Conan Doyle', 'Doyle, Arthur Conan')")
        book_rel_path = "Arthur Conan Doyle/A Study in Scarlet (2024)"
        book_dir = lib_path / book_rel_path
        book_dir.mkdir(parents=True, exist_ok=True)

        audio_file = book_dir / "A Study in Scarlet - Arthur Conan Doyle.mp3"
        create_minimal_mp3(audio_file, title="A Study in Scarlet", author="Arthur Conan Doyle", narrator="Stephen Fry")

        await conn.execute(
            "INSERT INTO books (id, title, sort, path, has_cover) VALUES (1, 'A Study in Scarlet', 'Study in Scarlet, A', ?, 1)",
            (book_rel_path,),
        )
        await conn.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) VALUES (1, 'MP3', ?, 'A Study in Scarlet - Arthur Conan Doyle')",
            (audio_file.stat().st_size,),
        )
        await conn.commit()

    lib = Library(
        id="test-transcribe-lib",
        name="Test Transcribe Lib",
        path=str(lib_path),
        created_at=None,
    )

    class MockLibraryManager:
        def __init__(self):
            self.libs = {"test-transcribe-lib": lib}

        def get_library(self, lib_id: str):
            return self.libs.get(lib_id)

        def get_database_manager(self, lib_id: str):
            from backend.database.connection import DatabaseManager
            return DatabaseManager(lib_path)

    return MockLibraryManager()


@pytest.mark.asyncio
async def test_transcribe_chapter_and_get(sample_audio_library):
    lib_mgr = sample_audio_library
    service = TranscriptionService(
        library_manager=lib_mgr,
        transcription_provider=MockTranscriptionProvider(),
    )

    # Transcribe Chapter 0
    t = await service.transcribe_chapter("test-transcribe-lib", 1, chapter_index=0)
    assert t is not None
    assert t.book_id == 1
    assert t.chapter_index == 0
    assert len(t.segments) > 0
    assert "Prologue" in t.chapter_title or "Audiobook" in t.chapter_title
    assert t.status == "completed"

    # Fetch chapter transcript
    single = await service.get_chapter_transcript("test-transcribe-lib", 1, chapter_index=0)
    assert single is not None
    assert single.id == t.id
    assert single.transcript_text == t.transcript_text


@pytest.mark.asyncio
async def test_transcribe_all_chapters(sample_audio_library):
    lib_mgr = sample_audio_library
    service = TranscriptionService(
        library_manager=lib_mgr,
        transcription_provider=MockTranscriptionProvider(),
    )

    all_trans = await service.transcribe_all_chapters("test-transcribe-lib", 1)
    assert len(all_trans) == 2

    # Fetch list
    all_fetched = await service.get_transcripts("test-transcribe-lib", 1)
    assert len(all_fetched) == 2


@pytest.mark.asyncio
async def test_transcribe_invalid_chapter_index_raises(sample_audio_library):
    lib_mgr = sample_audio_library
    service = TranscriptionService(
        library_manager=lib_mgr,
        transcription_provider=MockTranscriptionProvider(),
    )

    with pytest.raises(IndexError, match="out of range"):
        await service.transcribe_chapter("test-transcribe-lib", 1, chapter_index=99)


@pytest.mark.asyncio
async def test_export_transcripts(sample_audio_library):
    lib_mgr = sample_audio_library
    service = TranscriptionService(
        library_manager=lib_mgr,
        transcription_provider=MockTranscriptionProvider(),
    )

    trans = await service.transcribe_all_chapters("test-transcribe-lib", 1)

    # 1. Export WebVTT
    vtt = service.export_transcripts(trans, TranscriptExportFormat.VTT)
    assert vtt.startswith("WEBVTT")
    assert "-->" in vtt

    # 2. Export SRT
    srt = service.export_transcripts(trans, TranscriptExportFormat.SRT)
    assert "1" in srt
    assert "-->" in srt

    # 3. Export Markdown
    md = service.export_transcripts(trans, TranscriptExportFormat.MD, book_title="A Study in Scarlet")
    assert "# Transcript: A Study in Scarlet" in md
    assert "**[" in md


def test_time_formatting_helpers():
    assert format_seconds(65.0) == "01:05"
    assert format_seconds(3665.0) == "01:01:05"
    assert format_vtt_timestamp(65.123) == "00:01:05.123"
    assert format_srt_timestamp(65.123) == "00:01:05,123"
