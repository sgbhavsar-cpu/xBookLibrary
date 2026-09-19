"""Contract tests for multi-library registration, listing, and switching API."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.services.ingestion_service import IngestionService
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Sets isolated config directory."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_multi_library_api_isolation(tmp_path: Path, isolated_env: Path):
    """Verifies library registration, dynamic switching, and database query isolation."""
    lib_a_path = tmp_path / "LibraryA"
    lib_b_path = tmp_path / "LibraryB"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Initially empty
        res = await client.get("/api/libraries")
        assert res.status_code == 200
        assert res.json() == []

        # 2. Create Library A
        create_a = await client.post(
            "/api/libraries",
            json={
                "name": "SciFi Vault",
                "path": str(lib_a_path),
                "adopt_existing_calibre": False,
                "set_active": True,
            },
        )
        assert create_a.status_code == 201
        lib_a = create_a.json()
        lib_a_id = lib_a["id"]
        assert lib_a["name"] == "SciFi Vault"

        # Check active
        active_res = await client.get("/api/libraries/active")
        assert active_res.status_code == 200
        assert active_res.json()["id"] == lib_a_id

        # Ingest a book into Library A
        book_a_file = tmp_path / "dune.epub"
        create_sample_epub(book_a_file, title="Dune", author="Frank Herbert")
        ingest_a = IngestionService(lib_a_path)
        await ingest_a.ingest_file(book_a_file)

        # 3. Create Library B
        create_b = await client.post(
            "/api/libraries",
            json={
                "name": "Tech Books",
                "path": str(lib_b_path),
                "adopt_existing_calibre": False,
                "set_active": True,
            },
        )
        assert create_b.status_code == 201
        lib_b = create_b.json()
        lib_b_id = lib_b["id"]
        assert lib_b["name"] == "Tech Books"

        # Check active switched to B
        active_b_res = await client.get("/api/libraries/active")
        assert active_b_res.json()["id"] == lib_b_id

        # Ingest a different book into Library B
        book_b_file = tmp_path / "cleancode.epub"
        create_sample_epub(book_b_file, title="Clean Code", author="Robert C. Martin")
        ingest_b = IngestionService(lib_b_path)
        await ingest_b.ingest_file(book_b_file)

        # 4. Verify Library B queries only show Clean Code
        books_b_res = await client.get("/api/books")
        assert books_b_res.status_code == 200
        books_b_data = books_b_res.json()
        assert books_b_data["total"] == 1
        assert books_b_data["items"][0]["title"] == "Clean Code"

        # 5. Switch back to Library A
        switch_res = await client.post(f"/api/libraries/{lib_a_id}/switch")
        assert switch_res.status_code == 200
        assert switch_res.json()["id"] == lib_a_id

        # 6. Verify Library A queries only show Dune (strict isolation)
        books_a_res = await client.get("/api/books")
        assert books_a_res.status_code == 200
        books_a_data = books_a_res.json()
        assert books_a_data["total"] == 1
        assert books_a_data["items"][0]["title"] == "Dune"

        # 7. List libraries returns both
        all_libs = await client.get("/api/libraries")
        assert len(all_libs.json()) == 2
