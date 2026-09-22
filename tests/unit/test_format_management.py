"""Unit tests for Multi-Format Attachment and Deletion (Feature 015 User Story 3)."""

from pathlib import Path

import pytest

from backend.database.connection import DatabaseManager
from backend.services.ingestion_service import IngestionService
from backend.services.metadata_editor_service import MetadataEditorService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_attach_and_delete_format_lifecycle(temp_library_dir: Path):
    """Test attaching new formats and deleting obsolete formats."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    # Ingest base EPUB
    epub_path = temp_library_dir / "base.epub"
    create_sample_epub(epub_path, title="Format Master", author="Format Tester")
    book = await ingestion_service.ingest_file(epub_path)
    assert book.id is not None
    assert len(book.formats) == 1
    assert book.formats[0].format == "EPUB"

    # 1. Attach PDF
    pdf_bytes = b"%PDF-1.4 synthetic pdf"
    add_res = await editor_service.attach_format(
        book.id,
        format_name="PDF",
        filename_base="Format Master - Format Tester",
        file_bytes=pdf_bytes,
    )
    assert add_res.format == "PDF"
    assert "EPUB" in add_res.formats
    assert "PDF" in add_res.formats

    # Verify physical file exists
    pdf_path = temp_library_dir / book.path / "Format Master - Format Tester.pdf"
    assert pdf_path.exists()
    assert pdf_path.read_bytes() == pdf_bytes

    # 2. Attach CBZ
    cbz_bytes = b"PK\x03\x04synthetic cbz"
    add_res2 = await editor_service.attach_format(
        book.id,
        format_name="CBZ",
        filename_base="Format Master - Format Tester",
        file_bytes=cbz_bytes,
    )
    assert add_res2.format == "CBZ"
    assert set(add_res2.formats) == {"EPUB", "PDF", "CBZ"}

    # 3. Delete EPUB
    del_res = await editor_service.delete_format(book.id, format_name="EPUB")
    assert del_res.deleted_format == "EPUB"
    assert set(del_res.remaining_formats) == {"PDF", "CBZ"}

    # 4. Attempt to delete non-existent format raises ValueError
    with pytest.raises(ValueError, match="not found"):
        await editor_service.delete_format(book.id, format_name="MOBI")
