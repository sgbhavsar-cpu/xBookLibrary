"""Integration test for adopting an existing Calibre library in-place."""

from pathlib import Path

import pytest

from backend.config import ConfigManager
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_mock_calibre_library


@pytest.mark.asyncio
async def test_adopt_existing_calibre_library(tmp_path: Path):
    """Test full workflow of adopting an existing Calibre library in-place."""
    calibre_dir = tmp_path / "MyCalibreBooks"
    create_mock_calibre_library(calibre_dir)

    cfg_mgr = ConfigManager(tmp_path / "config")
    lib_mgr = LibraryManager(config_manager=cfg_mgr)

    adopted_lib = await lib_mgr.adopt_calibre_library(
        library_path=calibre_dir,
        name="Imported Calibre Collection",
        set_active=True,
    )

    assert adopted_lib.id is not None
    assert adopted_lib.name == "Imported Calibre Collection"
    assert adopted_lib.is_calibre_adopted is True
    assert adopted_lib.book_count == 2
    assert (calibre_dir / ".vectors").is_dir()

    # Verify active library from config
    active = cfg_mgr.get_active_library()
    assert active is not None
    assert active.id == adopted_lib.id

    # Verify querying books from the adopted library
    books = await lib_mgr.get_books_for_library(adopted_lib.id)
    assert len(books) == 2
    titles = [b.title for b in books]
    assert "Foundation" in titles
    assert "Neuromancer" in titles
