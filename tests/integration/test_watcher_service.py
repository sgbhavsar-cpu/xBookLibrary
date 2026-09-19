"""Integration tests for WatcherService and Jobs API."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.entities import IngestionStatus
from backend.main import app
from backend.services.library_manager import LibraryManager
from backend.services.watcher_service import WatcherService
from tests.fixtures.generators import create_sample_epub, create_sample_pdf


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets isolated config directory."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_watcher_intake_and_jobs(tmp_path: Path, isolated_env: Path):
    """Verifies intake folder scanning, automated ingestion, and jobs API."""
    lib_dir = tmp_path / "WatcherLibrary"
    intake_dir = tmp_path / "IntakeFolder"
    intake_dir.mkdir(parents=True, exist_ok=True)

    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Watcher Lib", set_active=True)

    # 1. Place 2 valid books and 1 invalid book in intake
    epub_path = intake_dir / "scifi_epic.epub"
    create_sample_epub(epub_path, title="Dune", author="Frank Herbert")

    pdf_path = intake_dir / "ai_paper.pdf"
    create_sample_pdf(pdf_path, title="Attention Is All You Need", author="Vaswani")

    corrupted_path = intake_dir / "broken.epub"
    corrupted_path.write_bytes(b"NOT A REAL EPUB OR ZIP ARCHIVE")

    # 2. Run WatcherService scan_once
    watcher = WatcherService(lib_dir, intake_dir, library_id="lib-123")
    jobs = await watcher.scan_once()

    assert len(jobs) == 3

    completed_jobs = [j for j in jobs if j.status == IngestionStatus.COMPLETED]
    failed_jobs = [j for j in jobs if j.status == IngestionStatus.FAILED]

    assert len(completed_jobs) == 2
    assert len(failed_jobs) == 1
    assert failed_jobs[0].error_message is not None

    # 3. Test Jobs API endpoints via HTTP client
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # List jobs
        list_res = await client.get("/api/jobs")
        assert list_res.status_code == 200
        jobs_list = list_res.json()
        assert len(jobs_list) == 3

        # Get specific completed job
        first_job_id = completed_jobs[0].id
        job_res = await client.get(f"/api/jobs/{first_job_id}")
        assert job_res.status_code == 200
        job_data = job_res.json()
        assert job_data["id"] == first_job_id
        assert job_data["status"] == "COMPLETED"
        assert job_data["book_id"] is not None

        # Verify books exist in library catalog
        books_res = await client.get("/api/books")
        assert books_res.status_code == 200
        books_data = books_res.json()
        assert books_data["total"] == 2
