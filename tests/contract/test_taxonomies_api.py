"""Contract tests for AI classification and taxonomies REST API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolates config directory to temporary path."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_classification_and_taxonomies_api_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies book classification, taxonomy tree management, and bookshelves via REST API."""
    # 1. Setup isolated library and ingest initial book
    lib_dir = tmp_path / "TaxonomyAPILib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Taxonomy API Lib", set_active=True)

    epub_file = tmp_path / "quantum.epub"
    create_sample_epub(epub_file, title="Quantum Computing Essentials", author="David D.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Ingest book
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("quantum.epub", f, "application/epub+zip")},
            )
            assert upload_res.status_code == 202
            book = upload_res.json()[0]
            book_id = book["id"]

        # 2. Trigger Book Classification
        mock_llm_response = {
            "bisac_code": "COM021000",
            "bisac_heading": "COMPUTERS / Computer Science",
            "ddc_code": "004.0151",
            "confidence": 0.94,
            "suggested_tags": ["Quantum Computing", "Algorithms"],
            "reasoning": "Covers qubits and quantum complexity.",
        }

        with patch(
            "backend.services.classification_service.ClassificationService._call_llm_classifier",
            new_callable=AsyncMock,
        ) as mock_call:
            mock_call.return_value = mock_llm_response

            classify_res = await client.post(f"/api/books/{book_id}/classify")
            assert classify_res.status_code == 200
            cls_data = classify_res.json()
            assert cls_data["bisac_code"] == "COM021000"
            assert cls_data["ddc_code"] == "004.0151"
            assert cls_data["applied"] is True

        # 3. Custom Taxonomy Tree Management
        # Check initial empty list
        empty_tax = await client.get("/api/taxonomies")
        assert empty_tax.status_code == 200
        assert empty_tax.json() == []

        # Create root category
        cat1_res = await client.post(
            "/api/taxonomies",
            json={"name": "Science & Tech", "description": "Technical domains"},
        )
        assert cat1_res.status_code == 201
        cat1 = cat1_res.json()
        assert cat1["name"] == "Science & Tech"
        assert cat1["path"] == "/Science & Tech"

        # Create child category
        cat2_res = await client.post(
            "/api/taxonomies",
            json={
                "name": "Physics",
                "parent_id": cat1["id"],
                "description": "Physical sciences",
            },
        )
        assert cat2_res.status_code == 201
        cat2 = cat2_res.json()
        assert cat2["path"] == "/Science & Tech/Physics"

        # Get tree
        tree_res = await client.get("/api/taxonomies")
        assert tree_res.status_code == 200
        tree = tree_res.json()
        assert len(tree) == 1
        assert tree[0]["name"] == "Science & Tech"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["name"] == "Physics"

        # 4. Virtual Bookshelves Management
        shelf_res = await client.post(
            "/api/bookshelves",
            json={"name": "Favorites", "description": "Top books", "icon": "star"},
        )
        assert shelf_res.status_code == 201
        shelf = shelf_res.json()
        shelf_id = shelf["id"]

        # Add book to shelf
        add_res = await client.post(
            f"/api/bookshelves/{shelf_id}/books",
            json={"book_ids": [book_id]},
        )
        assert add_res.status_code == 200

        # List bookshelves (assert book_count == 1)
        list_shelves = await client.get("/api/bookshelves")
        assert list_shelves.status_code == 200
        shelves = list_shelves.json()
        assert len(shelves) == 1
        assert shelves[0]["name"] == "Favorites"
        assert shelves[0]["book_count"] == 1

        # Get books on bookshelf
        shelf_books_res = await client.get(f"/api/bookshelves/{shelf_id}/books")
        assert shelf_books_res.status_code == 200
        shelf_books = shelf_books_res.json()
        assert len(shelf_books) == 1
        assert shelf_books[0]["id"] == book_id
        assert shelf_books[0]["title"] == "Quantum Computing Essentials"

        # Delete category
        del_cat = await client.delete(f"/api/taxonomies/{cat2['id']}")
        assert del_cat.status_code == 204
