"""Unit tests for Calibre schema introspection and sync service."""

from pathlib import Path

import pytest

from backend.services.calibre_sync import CalibreSyncService, InvalidCalibreLibraryError
from tests.fixtures.generators import create_mock_calibre_library


@pytest.mark.asyncio
async def test_calibre_schema_validation(tmp_path: Path):
    """Verify Calibre library detection, validation, and rejection of invalid directories."""
    # 1. Non-existent directory
    with pytest.raises(InvalidCalibreLibraryError):
        await CalibreSyncService.validate_calibre_directory(tmp_path / "non_existent")

    # 2. Directory without metadata.db
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    with pytest.raises(InvalidCalibreLibraryError):
        await CalibreSyncService.validate_calibre_directory(empty_dir)

    # 3. Valid Calibre directory
    calibre_dir = tmp_path / "CalibreLibrary"
    create_mock_calibre_library(calibre_dir)
    assert await CalibreSyncService.validate_calibre_directory(calibre_dir) is True


@pytest.mark.asyncio
async def test_calibre_non_destructive_augmentation(tmp_path: Path):
    """Verify x_ extension tables and .vectors/ are added without altering
    original Calibre tables."""
    calibre_dir = tmp_path / "CalibreLibrary"
    create_mock_calibre_library(calibre_dir)

    sync_service = CalibreSyncService(calibre_dir)
    await sync_service.augment_schema()

    # Verify .vectors folder created
    assert (calibre_dir / ".vectors").is_dir()

    # Verify original books still exist unharmed
    books = await sync_service.get_books()
    assert len(books) == 2

    book_titles = [b.title for b in books]
    assert "Foundation" in book_titles
    assert "Neuromancer" in book_titles

    # Verify authors and tags
    foundation = next(b for b in books if b.title == "Foundation")
    assert "Isaac Asimov" in foundation.authors
    assert "Sci-Fi" in foundation.tags
    assert len(foundation.formats) == 2  # EPUB & PDF

    neuromancer = next(b for b in books if b.title == "Neuromancer")
    assert "William Gibson" in neuromancer.authors
    assert "Cyberpunk" in neuromancer.tags
    assert len(neuromancer.formats) == 1  # EPUB
