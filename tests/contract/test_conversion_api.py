import asyncio
import sqlite3
from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_mock_calibre_library


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.fixture
async def active_conversion_library(tmp_path: Path, isolated_env: Path):
    calibre_dir = tmp_path / "ConvLib"
    create_mock_calibre_library(calibre_dir)

    # Add TXT format to book 1
    book1_dir = calibre_dir / "Isaac Asimov" / "Foundation (1951)"
    txt_file = book1_dir / "Foundation - Isaac Asimov.txt"
    txt_file.write_text("Hari Seldon was an ordinary man.", encoding="utf-8")

    conn = sqlite3.connect(calibre_dir / "metadata.db")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS publishers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, sort TEXT);
    CREATE TABLE IF NOT EXISTS books_publishers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, publisher INTEGER NOT NULL, UNIQUE(book, publisher));
    CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL UNIQUE, text TEXT);
    CREATE TABLE IF NOT EXISTS x_toc_nodes (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER NOT NULL, parent_id INTEGER, title TEXT NOT NULL, level INTEGER DEFAULT 0, page_number INTEGER, anchor_href TEXT, order_index INTEGER DEFAULT 0);
    """)
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (1, 'TXT', ?, 'Foundation - Isaac Asimov')",
        (txt_file.stat().st_size,)
    )
    conn.commit()
    conn.close()

    lib_mgr = LibraryManager()
    lib = await lib_mgr.adopt_calibre_library(calibre_dir, name="Conversion Test Library", set_active=True)
    return lib


@pytest.mark.asyncio
async def test_conversion_api_lifecycle(active_conversion_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit conversion request
        res = await client.post(
            "/api/convert",
            json={
                "book_id": 1,
                "source_format": "TXT",
                "target_format": "EPUB",
            },
        )
        assert res.status_code == 202
        job_data = res.json()
        assert "id" in job_data
        assert job_data["status"] == "pending"
        job_id = job_data["id"]

        # Wait briefly for background execution
        await asyncio.sleep(0.3)

        # Check job status
        res_job = await client.get(f"/api/convert/jobs/{job_id}")
        assert res_job.status_code == 200
        poll_data = res_job.json()
        assert poll_data["id"] == job_id
        assert poll_data["status"] in ("processing", "completed")

        # List jobs
        res_list = await client.get("/api/convert/jobs", params={"book_id": 1})
        assert res_list.status_code == 200
        jobs_list = res_list.json()
        assert len(jobs_list) >= 1
        assert any(j["id"] == job_id for j in jobs_list)


@pytest.mark.asyncio
async def test_conversion_api_invalid_book(active_conversion_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/convert",
            json={
                "book_id": 999999,
                "target_format": "EPUB",
            },
        )
        assert res.status_code == 400
