"""Contract tests for Feature 015 Metadata Editor,
Online Metadata, and Format Management REST APIs."""

import io
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

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
async def test_metadata_api_full_lifecycle(tmp_path: Path, isolated_env: Path):
    """Tests PUT metadata, POST cover, format management, and bulk updates via REST API."""
    lib_dir = tmp_path / "MetadataApiTestLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Metadata Test Library", set_active=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Ingest base EPUB
        epub_file = tmp_path / "base_book.epub"
        create_sample_epub(epub_file, title="Initial Title", author="Initial Author")
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("base_book.epub", f, "application/epub+zip")},
            )
        assert upload_res.status_code == 202
        books = upload_res.json()
        assert len(books) == 1
        book_id = books[0]["id"]

        # 2. PUT /api/books/{book_id}/metadata
        put_payload = {
            "title": "Hyperion (Remastered)",
            "sort_title": "Hyperion (Remastered)",
            "authors": ["Dan Simmons"],
            "publisher": "Doubleday",
            "pubdate": "1989",
            "rating": 5,
            "tags": ["Space Opera", "Hugo Winner", "Sci-Fi"],
            "series_name": "Hyperion Cantos",
            "series_index": 1.0,
            "isbn": "9780553283686",
            "identifiers": {"goodreads": "77566", "google": "xyz123"},
            "comments": "The Shrike awaits on the planet Hyperion.",
        }

        put_res = await client.put(f"/api/books/{book_id}/metadata", json=put_payload)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert updated["title"] == "Hyperion (Remastered)"
        assert updated["authors"] == ["Dan Simmons"]
        assert updated["publisher"] == "Doubleday"
        assert updated["publication_year"] == 1989
        assert updated["series_name"] == "Hyperion Cantos"
        assert updated["series_index"] == 1.0
        assert set(updated["tags"]) == {"Space Opera", "Hugo Winner", "Sci-Fi"}
        assert updated["isbn"] == "9780553283686"
        assert updated["description"] == "The Shrike awaits on the planet Hyperion."

        # 3. POST /api/books/{book_id}/cover
        img = Image.new("RGB", (150, 220), color=(30, 60, 90))
        img_buf = io.BytesIO()
        img.save(img_buf, format="JPEG")
        img_bytes = img_buf.getvalue()

        cover_res = await client.post(
            f"/api/books/{book_id}/cover",
            files={"cover": ("cover.jpg", img_bytes, "image/jpeg")},
        )
        assert cover_res.status_code == 200
        assert cover_res.json()["has_cover"] is True

        # 4. POST /api/books/{book_id}/formats
        pdf_bytes = b"%PDF-1.4 synthetic PDF content"
        fmt_res = await client.post(
            f"/api/books/{book_id}/formats",
            files={"file": ("Hyperion - Dan Simmons.pdf", pdf_bytes, "application/pdf")},
        )
        assert fmt_res.status_code == 201
        fmt_data = fmt_res.json()
        assert fmt_data["format"] == "PDF"
        assert "EPUB" in fmt_data["formats"]
        assert "PDF" in fmt_data["formats"]

        # 5. DELETE /api/books/{book_id}/formats/EPUB
        del_res = await client.delete(f"/api/books/{book_id}/formats/EPUB")
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["deleted_format"] == "EPUB"
        assert del_data["remaining_formats"] == ["PDF"]

        # 6. POST /api/books/bulk-update
        # Upload another book
        epub_file2 = tmp_path / "second_book.epub"
        create_sample_epub(epub_file2, title="Fall of Hyperion", author="Dan Simmons")
        with open(epub_file2, "rb") as f:
            up2 = await client.post(
                "/api/books/upload",
                files={"files": ("second_book.epub", f, "application/epub+zip")},
            )
        book_id_2 = up2.json()[0]["id"]

        bulk_payload = {
            "book_ids": [book_id, book_id_2],
            "add_tags": ["CantosUniverse"],
            "set_series": "Hyperion Cantos",
            "auto_increment_series": True,
            "series_start_index": 1.0,
        }
        bulk_res = await client.post("/api/books/bulk-update", json=bulk_payload)
        assert bulk_res.status_code == 200
        bulk_data = bulk_res.json()
        assert bulk_data["updated_count"] == 2
        assert len(bulk_data["failed_ids"]) == 0
