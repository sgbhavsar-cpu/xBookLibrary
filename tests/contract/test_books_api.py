"""Contract tests for books REST API endpoints."""

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub, create_sample_pdf


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolates config directory to temporary path."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_health_check():
    """Verify system health check responds 200."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "xBookLibrary"


@pytest.mark.asyncio
async def test_books_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies book upload, retrieval, cover streaming, and format merging via REST API."""
    # 1. Setup isolated library
    lib_dir = tmp_path / "APITestLibrary"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="API Test Library", set_active=True)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 2. Check empty library
        res_empty = await client.get("/api/books")
        assert res_empty.status_code == 200
        empty_data = res_empty.json()
        assert empty_data["total"] == 0
        assert empty_data["items"] == []

        # 3. Generate synthetic EPUB
        epub_file = tmp_path / "dune_novel.epub"
        create_sample_epub(
            epub_file,
            title="Dune Messiah",
            author="Frank Herbert",
        )

        # 4. Upload EPUB
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("dune_novel.epub", f, "application/epub+zip")},
            )
        assert upload_res.status_code == 202
        books_uploaded = upload_res.json()
        assert len(books_uploaded) == 1
        book = books_uploaded[0]
        book_id = book["id"]
        assert book["title"] == "Dune Messiah"
        assert book["authors"][0] == "Frank Herbert"
        assert len(book["formats"]) == 1
        assert book["formats"][0]["format"] == "EPUB"

        # 5. Detail retrieval
        detail_res = await client.get(f"/api/books/{book_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["id"] == book_id
        assert detail_data["title"] == "Dune Messiah"

        # 6. Cover streaming
        cover_res = await client.get(f"/api/books/{book_id}/cover")
        assert cover_res.status_code == 200
        assert "image/jpeg" in cover_res.headers["content-type"]
        assert len(cover_res.content) > 0

        # 7. Multi-format upload (PDF with same title/author)
        pdf_file = tmp_path / "dune_messiah.pdf"
        create_sample_pdf(
            pdf_file,
            title="Dune Messiah",
            author="Frank Herbert",
        )
        with open(pdf_file, "rb") as f:
            upload_pdf_res = await client.post(
                "/api/books/upload",
                files={"files": ("dune_messiah.pdf", f, "application/pdf")},
            )
        assert upload_pdf_res.status_code == 202
        merged_books = upload_pdf_res.json()
        assert len(merged_books) == 1
        merged = merged_books[0]
        assert merged["id"] == book_id
        assert len(merged["formats"]) == 2
        format_names = {fmt["format"] for fmt in merged["formats"]}
        assert "EPUB" in format_names
        assert "PDF" in format_names

        # 8. Listing query
        list_res = await client.get("/api/books?query=Dune")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["id"] == book_id

        # 9. Book deletion via API
        del_res = await client.delete(f"/api/books/{book_id}")
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["book_id"] == book_id
        assert del_data["status"] == "deleted"

        # Verify book no longer exists
        not_found_res = await client.get(f"/api/books/{book_id}")
        assert not_found_res.status_code == 404

