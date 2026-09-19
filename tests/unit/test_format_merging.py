"""Unit tests for IngestionService deduplication and multi-format merging."""

from pathlib import Path

import pytest

from backend.database.connection import DatabaseManager
from backend.services.ingestion_service import IngestionService
from tests.fixtures.generators import create_sample_epub, create_sample_pdf


@pytest.mark.asyncio
async def test_multi_format_merging(temp_library_dir: Path):
    """Verify that importing an EPUB and PDF of the same book merges under 1 book record."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)

    # 1. Ingest EPUB version of Dune
    epub_path = temp_library_dir / "_temp_dune.epub"
    create_sample_epub(epub_path, title="Dune", author="Frank Herbert")

    book1 = await ingestion_service.ingest_file(epub_path)
    assert book1.id is not None
    assert book1.title == "Dune"
    assert "Frank Herbert" in book1.authors
    assert len(book1.formats) == 1
    assert book1.formats[0].format == "EPUB"

    # 2. Ingest PDF version of Dune (same title and author)
    pdf_path = temp_library_dir / "_temp_dune.pdf"
    create_sample_pdf(pdf_path, title="Dune", author="Frank Herbert")

    book2 = await ingestion_service.ingest_file(pdf_path)

    # Verify merged under same book ID
    assert book2.id == book1.id
    assert book2.title == "Dune"
    assert len(book2.formats) == 2

    format_names = {f.format for f in book2.formats}
    assert "EPUB" in format_names
    assert "PDF" in format_names

    # Verify both physical files exist in the same Calibre book directory
    book_dir = temp_library_dir / book2.path
    assert (book_dir / "cover.jpg").exists()
    assert (book_dir / "metadata.opf").exists()
    assert any(f.name.endswith(".epub") for f in book_dir.iterdir())
    assert any(f.name.endswith(".pdf") for f in book_dir.iterdir())


@pytest.mark.asyncio
async def test_byte_identical_deduplication(temp_library_dir: Path):
    """Verify that uploading the exact same file twice does not create duplicates."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)

    epub_path = temp_library_dir / "_temp_duplicate.epub"
    create_sample_epub(epub_path, title="Neuromancer", author="William Gibson")

    book_first = await ingestion_service.ingest_file(epub_path)
    # Ingest the exact same file a second time
    book_second = await ingestion_service.ingest_file(epub_path)

    assert book_first.id == book_second.id
    assert len(book_second.formats) == 1
