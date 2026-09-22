"""Unit tests for MetadataEditorService."""

import io
from pathlib import Path

import pytest
from PIL import Image

from backend.database.connection import DatabaseManager
from backend.domain.metadata_editor import (
    BookMetadataUpdateRequest,
    BulkMetadataUpdateRequest,
)
from backend.services.ingestion_service import IngestionService
from backend.services.metadata_editor_service import MetadataEditorService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_single_book_metadata_update(temp_library_dir: Path):
    """Verify that updating a book updates all normalized Calibre tables and metadata.opf."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    # 1. Ingest base book
    epub_path = temp_library_dir / "sample.epub"
    create_sample_epub(epub_path, title="Old Title", author="Old Author")
    book = await ingestion_service.ingest_file(epub_path)
    assert book.id is not None

    # 2. Update metadata
    update_req = BookMetadataUpdateRequest(
        title="Dune (Special Edition)",
        sort_title="Dune (Special Edition)",
        authors=["Frank Herbert"],
        publisher="Chilton Books",
        pubdate="1965",
        rating=5,
        tags=["Sci-Fi", "Classic", "Hugo Award"],
        series_name="Dune Chronicles",
        series_index=1.5,
        isbn="9780441172719",
        identifiers={"google": "123456", "goodreads": "789"},
        comments="<p>A masterpiece of science fiction set on Arrakis.</p>",
    )

    updated_book = await editor_service.update_book_metadata(book.id, update_req)

    # 3. Assert updated Book entity
    assert updated_book.title == "Dune (Special Edition)"
    assert updated_book.sort_title == "Dune (Special Edition)"
    assert updated_book.authors == ["Frank Herbert"]
    assert updated_book.publisher == "Chilton Books"
    assert updated_book.publication_year == 1965
    assert updated_book.series_name == "Dune Chronicles"
    assert updated_book.series_index == 1.5
    assert set(updated_book.tags) == {"Sci-Fi", "Classic", "Hugo Award"}
    assert updated_book.isbn == "9780441172719"
    assert updated_book.identifiers.get("google") == "123456"
    assert updated_book.description == "<p>A masterpiece of science fiction set on Arrakis.</p>"
    assert updated_book.custom_values.get("rating") == 5

    # 4. Assert metadata.opf XML content
    book_dir = temp_library_dir / updated_book.path
    opf_path = book_dir / "metadata.opf"
    assert opf_path.exists()
    opf_content = opf_path.read_text(encoding="utf-8")
    assert "Dune (Special Edition)" in opf_content
    assert "Frank Herbert" in opf_content
    assert "Chilton Books" in opf_content
    assert "Dune Chronicles" in opf_content
    assert "Hugo Award" in opf_content


@pytest.mark.asyncio
async def test_cover_image_saving(temp_library_dir: Path):
    """Verify that saving a new cover updates cover.jpg, has_cover flag, and OPF."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    epub_path = temp_library_dir / "sample_cover.epub"
    create_sample_epub(epub_path, title="Cover Test Book", author="Cover Author")
    book = await ingestion_service.ingest_file(epub_path)

    # Generate a small test image in memory
    img = Image.new("RGB", (120, 180), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    success = await editor_service.save_book_cover(book.id, png_bytes)
    assert success is True

    # Assert cover file is created as JPEG
    book_dir = temp_library_dir / book.path
    cover_file = book_dir / "cover.jpg"
    assert cover_file.exists()
    with Image.open(cover_file) as loaded_img:
        assert loaded_img.format == "JPEG"
        assert loaded_img.size == (120, 180)

    # Verify book record has_cover is True
    reloaded_book = await editor_service.get_book_metadata(book.id)
    assert reloaded_book.has_cover is True


@pytest.mark.asyncio
async def test_format_attachment_and_deletion(temp_library_dir: Path):
    """Verify attaching an extra format and deleting an existing format."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    epub_path = temp_library_dir / "format_test.epub"
    create_sample_epub(epub_path, title="Format Book", author="Format Author")
    book = await ingestion_service.ingest_file(epub_path)

    # 1. Attach a PDF format
    pdf_bytes = b"%PDF-1.4 sample pdf content for testing"
    add_resp = await editor_service.attach_format(
        book.id,
        format_name="PDF",
        filename_base="Format Book - Format Author",
        file_bytes=pdf_bytes,
    )
    assert add_resp.format == "PDF"
    assert "EPUB" in add_resp.formats
    assert "PDF" in add_resp.formats

    book_reloaded = await editor_service.get_book_metadata(book.id)
    fmt_names = {f.format for f in book_reloaded.formats}
    assert "EPUB" in fmt_names
    assert "PDF" in fmt_names

    # 2. Delete EPUB format
    del_resp = await editor_service.delete_format(book.id, format_name="EPUB")
    assert del_resp.deleted_format == "EPUB"
    assert del_resp.remaining_formats == ["PDF"]

    book_final = await editor_service.get_book_metadata(book.id)
    assert len(book_final.formats) == 1
    assert book_final.formats[0].format == "PDF"


@pytest.mark.asyncio
async def test_bulk_metadata_update(temp_library_dir: Path):
    """Verify batch updating tags, authors, and auto-incrementing series indices."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    # Create 3 books
    ids = []
    for i in range(1, 4):
        p = temp_library_dir / f"book_{i}.epub"
        create_sample_epub(p, title=f"Series Part {i}", author="Original Author")
        b = await ingestion_service.ingest_file(p)
        ids.append(b.id)

    bulk_req = BulkMetadataUpdateRequest(
        book_ids=ids,
        add_tags=["SharedBatchTag", "MustRead"],
        set_publisher="Tor Books",
        set_series="The Expanse",
        auto_increment_series=True,
        series_start_index=1.0,
        set_rating=4,
    )

    result = await editor_service.bulk_update_books(bulk_req)
    assert result.updated_count == 3
    assert len(result.failed_ids) == 0

    # Verify individual books
    for idx, b_id in enumerate(ids):
        b = await editor_service.get_book_metadata(b_id)
        assert "SharedBatchTag" in b.tags
        assert "MustRead" in b.tags
        assert b.publisher == "Tor Books"
        assert b.series_name == "The Expanse"
        assert b.series_index == 1.0 + idx
        assert b.custom_values.get("rating") == 4


@pytest.mark.asyncio
async def test_delete_single_book(temp_library_dir: Path):
    """Verify single book deletion removes DB records and disk files."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    # Ingest book
    p = temp_library_dir / "to_delete.epub"
    create_sample_epub(p, title="Book To Delete", author="Temporary Author")
    b = await ingestion_service.ingest_file(p)
    assert b.id is not None

    book_dir = temp_library_dir / b.path
    assert book_dir.exists()

    # Delete
    del_res = await editor_service.delete_book(b.id)
    assert del_res.book_id == b.id
    assert del_res.deleted_from_disk is True
    assert not book_dir.exists()

    # Assert get_book_metadata raises ValueError
    with pytest.raises(ValueError):
        await editor_service.get_book_metadata(b.id)


@pytest.mark.asyncio
async def test_bulk_delete_books(temp_library_dir: Path):
    """Verify bulk book deletion deletes multiple books."""
    from backend.domain.metadata_editor import BulkDeleteRequest

    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    ids = []
    for i in range(1, 4):
        p = temp_library_dir / f"bulk_del_{i}.epub"
        create_sample_epub(p, title=f"Bulk Delete {i}", author="Bulk Author")
        b = await ingestion_service.ingest_file(p)
        ids.append(b.id)

    res = await editor_service.bulk_delete_books(BulkDeleteRequest(book_ids=ids))
    assert res.total_requested == 3
    assert res.deleted_count == 3
    assert len(res.failed_ids) == 0

    for b_id in ids:
        with pytest.raises(ValueError):
            await editor_service.get_book_metadata(b_id)

