"""Contract tests for Feature 014 Audiobook Hub & Whisper Transcription API endpoints."""

import asyncio
from pathlib import Path
import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Library
from backend.main import app
from tests.unit.parsers.test_audio_parser import create_minimal_mp3


@pytest.fixture
def mock_audio_contract_library(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_dir = tmp_path / "ContractAudioLib"
    lib_dir.mkdir(parents=True)

    db_mgr = DatabaseManager(lib_dir)
    asyncio.run(db_mgr.initialize_database())

    book_folder = lib_dir / "Conan Doyle" / "The Hound of the Baskervilles (2024)"
    book_folder.mkdir(parents=True)
    audio_file = book_folder / "The Hound of the Baskervilles - Conan Doyle.mp3"
    create_minimal_mp3(audio_file, title="The Hound of the Baskervilles", author="Conan Doyle", narrator="Stephen Fry")

    async def seed():
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            cursor = await conn.execute(
                "INSERT INTO books (title, author_sort, path) VALUES ('The Hound of the Baskervilles', 'Conan Doyle', 'Conan Doyle/The Hound of the Baskervilles (2024)')"
            )
            book_id = cursor.lastrowid
            await conn.execute(
                "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'MP3', ?, 'The Hound of the Baskervilles - Conan Doyle')",
                (book_id, audio_file.stat().st_size),
            )
            await conn.commit()
            return book_id

    book_id = asyncio.run(seed())

    cfg_mgr = ConfigManager(cfg_dir)
    lib = Library(
        id="lib-contract-audio",
        name="Contract Audio Lib",
        path=str(lib_dir),
    )
    cfg_mgr.register_library(lib, set_active=True)

    return "lib-contract-audio", book_id, lib_dir, audio_file


@pytest.mark.asyncio
async def test_audio_metadata_contract(mock_audio_contract_library):
    lib_id, book_id, _, _ = mock_audio_contract_library

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/metadata")
        assert resp.status_code == 200
        data = resp.json()
        assert data["book_id"] == book_id
        assert data["format"] == "MP3"
        assert data["narrator"] == "Stephen Fry"
        assert len(data["chapters"]) >= 1


@pytest.mark.asyncio
async def test_audio_streaming_contract(mock_audio_contract_library):
    lib_id, book_id, _, audio_file = mock_audio_contract_library

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Full stream
        resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/stream")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "audio/mpeg"
        assert resp.headers["accept-ranges"] == "bytes"
        assert len(resp.content) == audio_file.stat().st_size

        # 2. Partial range stream
        range_header = {"Range": "bytes=0-499"}
        resp_range = await client.get(
            f"/api/libraries/{lib_id}/books/{book_id}/audio/stream",
            headers=range_header,
        )
        assert resp_range.status_code == 206
        assert resp_range.headers["content-range"].startswith("bytes 0-499/")
        assert resp_range.headers["content-length"] == "500"
        assert len(resp_range.content) == 500


@pytest.mark.asyncio
async def test_audio_listening_progress_contract(mock_audio_contract_library):
    lib_id, book_id, _, _ = mock_audio_contract_library

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Save progress
        payload = {
            "current_time": 120.5,
            "current_chapter_index": 1,
            "progress_percent": 45.0,
            "playback_speed": 1.5,
        }
        post_resp = await client.post(
            f"/api/libraries/{lib_id}/books/{book_id}/audio/progress",
            json=payload,
        )
        assert post_resp.status_code == 200
        saved = post_resp.json()
        assert saved["current_time"] == 120.5
        assert saved["current_chapter_index"] == 1
        assert saved["progress_percent"] == 45.0
        assert saved["playback_speed"] == 1.5

        # 2. Get progress
        get_resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/progress")
        assert get_resp.status_code == 200
        retrieved = get_resp.json()
        assert retrieved["current_time"] == 120.5
        assert retrieved["current_chapter_index"] == 1


@pytest.mark.asyncio
async def test_audio_transcription_and_export_contract(mock_audio_contract_library):
    lib_id, book_id, _, _ = mock_audio_contract_library

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Trigger transcription
        req_payload = {
            "book_id": book_id,
            "chapter_index": 0,
            "model_name": "whisper-1",
        }
        trans_resp = await client.post(
            f"/api/libraries/{lib_id}/books/{book_id}/audio/transcribe",
            json=req_payload,
        )
        assert trans_resp.status_code == 200
        transcripts = trans_resp.json()
        assert len(transcripts) == 1
        assert transcripts[0]["chapter_index"] == 0
        assert len(transcripts[0]["segments"]) > 0

        # 2. List transcripts
        list_resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/transcripts")
        assert list_resp.status_code == 200
        all_tr = list_resp.json()
        assert len(all_tr) >= 1

        # 3. Get single chapter transcript
        single_resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/transcripts/0")
        assert single_resp.status_code == 200
        assert single_resp.json()["chapter_index"] == 0

        # 4. Export WebVTT
        vtt_resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/transcripts/export?format=vtt")
        assert vtt_resp.status_code == 200
        assert "WEBVTT" in vtt_resp.text
        assert "-->" in vtt_resp.text

        # 5. Export Markdown
        md_resp = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/audio/transcripts/export?format=md")
        assert md_resp.status_code == 200
        assert "# Transcript:" in md_resp.text
