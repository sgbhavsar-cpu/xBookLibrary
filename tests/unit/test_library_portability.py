"""Unit tests for Calibre library portability, relative paths, and cover streaming."""

import shutil
from pathlib import Path
import pytest
from PIL import Image

from backend.parsers.epub_parser import EpubParser
from backend.services.calibre_sync import CalibreSyncService
from backend.services.ingestion_service import IngestionService
from backend.services.library_manager import LibraryManager
from backend.services.storage_service import StorageService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_library_relocation_portability(tmp_path: Path):
    """Verifies that a library can be moved to a new path with all relative paths remaining intact."""
    initial_dir = tmp_path / "OriginalLibrary"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(initial_dir, name="Portable Library", set_active=False)

    # Ingest a sample book
    sample_file = tmp_path / "sample_book.epub"
    create_sample_epub(sample_file, title="Foundation", author="Isaac Asimov")

    ingestion = IngestionService(initial_dir)
    book = await ingestion.ingest_file(sample_file)

    assert book.id is not None
    assert book.title == "Foundation"
    assert book.authors == ["Isaac Asimov"]

    # Verify initial relative path
    storage_initial = StorageService(initial_dir)
    rel_book_dir = storage_initial.resolve_book_path(book.path)
    assert (rel_book_dir / "cover.jpg").exists()
    assert (rel_book_dir / "metadata.opf").exists()

    # Move/relocate the entire library folder
    relocated_dir = tmp_path / "RelocatedLibrary"
    shutil.move(str(initial_dir), str(relocated_dir))

    # Re-open the relocated library via CalibreSyncService and StorageService
    sync_relocated = CalibreSyncService(relocated_dir)
    books_relocated = await sync_relocated.get_books()

    assert len(books_relocated) == 1
    relocated_book = books_relocated[0]
    assert relocated_book.title == "Foundation"

    # Verify relative path resolution works on the new location
    storage_relocated = StorageService(relocated_dir)
    new_book_dir = storage_relocated.resolve_book_path(relocated_book.path)
    assert new_book_dir.exists()
    assert (new_book_dir / "cover.jpg").exists()
    assert (new_book_dir / "metadata.opf").exists()

    # Verify format resolution
    format_path = storage_relocated.resolve_format_path(
        relocated_book.path,
        relocated_book.formats[0].format,
        relocated_book.formats[0].name,
    )
    assert format_path.exists()
    assert format_path.suffix.lower() == ".epub"


def test_storage_service_path_sanitization():
    """Verifies that invalid filename and path characters are safely sanitized."""
    from backend.services.storage_service import sanitize_filename

    unsafe = 'What: An "Amazing" / Book? * [v1.0] <Special> | Edition'
    safe = sanitize_filename(unsafe)
    assert ":" not in safe
    assert '"' not in safe
    assert "/" not in safe
    assert "?" not in safe
    assert "*" not in safe
    assert "<" not in safe
    assert ">" not in safe
    assert "|" not in safe
    assert safe == "What An Amazing Book [v1.0] Special Edition"
