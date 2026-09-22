"""Unit tests for Bulk Metadata Update and Series Auto-Incrementation (Feature 015 User Story 4)."""

from pathlib import Path

import pytest

from backend.database.connection import DatabaseManager
from backend.domain.metadata_editor import BulkMetadataUpdateRequest
from backend.services.ingestion_service import IngestionService
from backend.services.metadata_editor_service import MetadataEditorService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_bulk_metadata_tags_and_fields(temp_library_dir: Path):
    """Verify that bulk updating modifies only target fields and preserves others."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    # Ingest 2 sample books with distinct tags
    book_ids = []
    p1 = temp_library_dir / "bulk1.epub"
    create_sample_epub(p1, title="Book Alpha", author="Author Alpha")
    b1 = await ingestion_service.ingest_file(p1)
    book_ids.append(b1.id)

    p2 = temp_library_dir / "bulk2.epub"
    create_sample_epub(p2, title="Book Beta", author="Author Beta")
    b2 = await ingestion_service.ingest_file(p2)
    book_ids.append(b2.id)

    # Execute bulk update adding tag and setting publisher
    bulk_req = BulkMetadataUpdateRequest(
        book_ids=book_ids,
        add_tags=["FeaturedCollection", "HardSciFi"],
        set_publisher="Ace Books",
        set_rating=5,
    )

    res = await editor_service.bulk_update_books(bulk_req)
    assert res.updated_count == 2
    assert len(res.failed_ids) == 0

    for b_id in book_ids:
        reloaded = await editor_service.get_book_metadata(b_id)
        assert "FeaturedCollection" in reloaded.tags
        assert "HardSciFi" in reloaded.tags
        assert reloaded.publisher == "Ace Books"
        assert reloaded.custom_values.get("rating") == 5


@pytest.mark.asyncio
async def test_bulk_metadata_series_auto_increment(temp_library_dir: Path):
    """Verify series auto-incrementation sequentially numbers books."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    ingestion_service = IngestionService(temp_library_dir)
    editor_service = MetadataEditorService(temp_library_dir)

    book_ids = []
    for i in range(1, 4):
        p = temp_library_dir / f"series_{i}.epub"
        create_sample_epub(p, title=f"Part {i}", author="Trilogy Author")
        b = await ingestion_service.ingest_file(p)
        book_ids.append(b.id)

    bulk_req = BulkMetadataUpdateRequest(
        book_ids=book_ids,
        set_series="The Mars Trilogy",
        auto_increment_series=True,
        series_start_index=1.0,
    )

    res = await editor_service.bulk_update_books(bulk_req)
    assert res.updated_count == 3

    for idx, b_id in enumerate(book_ids):
        b = await editor_service.get_book_metadata(b_id)
        assert b.series_name == "The Mars Trilogy"
        assert b.series_index == float(1 + idx)
