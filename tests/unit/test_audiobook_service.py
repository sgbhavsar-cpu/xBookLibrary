"""Unit tests for AudiobookService."""

import json
from pathlib import Path
import pytest
import aiosqlite

from backend.domain.audiobook import AudioListeningProgressUpdateRequest
from backend.domain.custom_columns import CustomColumnCreateRequest, CustomColumnDatatype
from backend.domain.entities import Library
from backend.services.audiobook_service import AudiobookService
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager
from tests.unit.parsers.test_audio_parser import create_minimal_mp3


@pytest.fixture
async def sample_library(tmp_path: Path):
    lib_path = tmp_path / "AudioLib"
    lib_path.mkdir(parents=True, exist_ok=True)
    db_path = lib_path / "metadata.db"

    from backend.database.schema import CALIBRE_SCHEMA_DDL
    async with aiosqlite.connect(db_path) as conn:
        await conn.executescript(CALIBRE_SCHEMA_DDL)

        # Insert sample author and book
        await conn.execute("INSERT INTO authors (id, name, sort) VALUES (1, 'Arthur Conan Doyle', 'Doyle, Arthur Conan')")
        book_rel_path = "Arthur Conan Doyle/The Hound of the Baskervilles (2023)"
        book_dir = lib_path / book_rel_path
        book_dir.mkdir(parents=True, exist_ok=True)

        audio_file = book_dir / "The Hound of the Baskervilles - Arthur Conan Doyle.mp3"
        create_minimal_mp3(audio_file, title="The Hound of the Baskervilles", author="Arthur Conan Doyle", narrator="Stephen Fry")

        await conn.execute(
            "INSERT INTO books (id, title, sort, path, has_cover) VALUES (1, 'The Hound of the Baskervilles', 'Hound of the Baskervilles, The', ?, 1)",
            (book_rel_path,),
        )
        await conn.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) VALUES (1, 'MP3', ?, 'The Hound of the Baskervilles - Arthur Conan Doyle')",
            (audio_file.stat().st_size,),
        )
        await conn.commit()

    lib = Library(
        id="test-audio-lib",
        name="Test Audio Lib",
        path=str(lib_path),
        created_at=None,
    )

    class MockLibraryManager(LibraryManager):
        def __init__(self):
            self.libs = {"test-audio-lib": lib}

        def get_library(self, lib_id: str):
            return self.libs.get(lib_id)

        def get_database_manager(self, lib_id: str):
            from backend.database.connection import DatabaseManager
            return DatabaseManager(lib_path)

    lib_mgr = MockLibraryManager()
    return lib_mgr, audio_file


@pytest.mark.asyncio
async def test_get_audiobook_metadata_and_cache(sample_library):
    lib_mgr, audio_file = sample_library
    service = AudiobookService(lib_mgr)

    meta = await service.get_audiobook_metadata("test-audio-lib", 1)
    assert meta is not None
    assert meta.book_id == 1
    assert meta.format == "MP3"
    assert meta.narrator == "Stephen Fry"
    assert len(meta.chapters) == 2
    assert meta.chapters[0].title == "Prologue"
    assert meta.chapters[1].title == "Chapter 1"

    # Second call should fetch from cache
    meta_cached = await service.get_audiobook_metadata("test-audio-lib", 1)
    assert meta_cached is not None
    assert meta_cached.book_id == 1
    assert meta_cached.narrator == "Stephen Fry"


def test_parse_range_header():
    service = AudiobookService(None)

    # Full file when None
    start, end, length = service.parse_range_header(None, 1000)
    assert (start, end, length) == (0, 999, 1000)

    # Valid range
    start, end, length = service.parse_range_header("bytes=0-499", 1000)
    assert (start, end, length) == (0, 499, 500)

    # Open-ended range
    start, end, length = service.parse_range_header("bytes=500-", 1000)
    assert (start, end, length) == (500, 999, 500)

    # Clamped bounds
    start, end, length = service.parse_range_header("bytes=900-1500", 1000)
    assert (start, end, length) == (900, 999, 100)


@pytest.mark.asyncio
async def test_file_chunk_generator(tmp_path: Path):
    service = AudiobookService(None)
    f = tmp_path / "test.bin"
    content = b"0123456789" * 10
    f.write_bytes(content)

    chunks = []
    async for chunk in service.file_chunk_generator(f, start=10, content_length=25, chunk_size=10):
        chunks.append(chunk)

    result = b"".join(chunks)
    assert result == content[10:35]
    assert len(result) == 25


@pytest.mark.asyncio
async def test_listening_progress_sync_read_status(sample_library):
    lib_mgr, _ = sample_library
    custom_service = CustomColumnsService(lib_mgr)

    # Create #read_status column
    col = CustomColumnCreateRequest(
        label="read_status",
        name="Read Status",
        datatype=CustomColumnDatatype.ENUMERATION,
        display={"enum_values": ["unread", "reading", "completed"]},
    )
    await custom_service.create_custom_column("test-audio-lib", col)

    service = AudiobookService(lib_mgr, custom_columns_service=custom_service)

    # 1. Initial save at 50%
    req = AudioListeningProgressUpdateRequest(
        current_time=150.0,
        current_chapter_index=1,
        progress_percent=50.0,
        playback_speed=1.25,
    )
    progress = await service.save_listening_progress("test-audio-lib", 1, req)
    assert progress.progress_percent == 50.0
    assert not progress.is_finished

    # Verify custom column set to 'reading'
    val = await custom_service.get_book_custom_values("test-audio-lib", 1)
    assert val.values.get("read_status") == "reading"

    # Verify get_listening_progress
    retrieved = await service.get_listening_progress("test-audio-lib", 1)
    assert retrieved is not None
    assert retrieved.current_time == 150.0
    assert retrieved.current_chapter_index == 1
    assert retrieved.playback_speed == 1.25

    # 2. Save at 99% -> triggers completed
    req2 = AudioListeningProgressUpdateRequest(
        current_time=298.0,
        current_chapter_index=1,
        progress_percent=99.0,
    )
    progress2 = await service.save_listening_progress("test-audio-lib", 1, req2)
    assert progress2.is_finished

    val2 = await custom_service.get_book_custom_values("test-audio-lib", 1)
    assert val2.values.get("read_status") == "completed"
