"""Unit tests for foundational layer: storage, config, and database manager."""

from pathlib import Path

import pytest

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Book, Library
from backend.services.storage_service import StorageService, sanitize_filename


def test_sanitize_filename():
    """Verify illegal Windows/POSIX characters are stripped/replaced."""
    raw = "What If?: Serious Scientific Answers to Absurd Questions"
    sanitized = sanitize_filename(raw)
    assert ":" not in sanitized
    assert "?" not in sanitized
    assert sanitized.startswith("What If")

    # Path traversal and pipe tests
    dangerous = "../../etc/passwd|con*aux"
    safe = sanitize_filename(dangerous)
    assert "/" not in safe
    assert "\\" not in safe
    assert "|" not in safe
    assert "*" not in safe


def test_storage_service_paths_and_opf(temp_library_dir: Path):
    """Verify Calibre directory layout and OPF file creation."""
    storage = StorageService(temp_library_dir)
    rel_dir = storage.get_book_relative_dir("William Gibson", "Neuromancer", 1984)
    assert rel_dir == "William Gibson/Neuromancer (1984)"

    book_dir = storage.get_book_absolute_dir(rel_dir)
    book = Book(
        title="Neuromancer",
        authors=["William Gibson"],
        publication_year=1984,
        publisher="Ace Books",
        isbn="9780441569595",
        tags=["Cyberpunk", "Sci-Fi"],
        series_name="Sprawl",
        series_index=1.0,
    )
    opf_file = storage.write_metadata_opf(book_dir, book)
    assert opf_file.exists()
    content = opf_file.read_text(encoding="utf-8")
    assert "Neuromancer" in content
    assert "William Gibson" in content
    assert "Sprawl" in content


def test_config_manager(tmp_path: Path):
    """Verify global config persistence and library registration."""
    config_dir = tmp_path / "test_config"
    cfg_mgr = ConfigManager(config_dir)

    lib = Library(
        id="lib-01",
        name="Sci-Fi Vault",
        path=str(tmp_path / "SciFi"),
        is_calibre_adopted=False,
    )
    cfg_mgr.register_library(lib, set_active=True)

    active_lib = cfg_mgr.get_active_library()
    assert active_lib is not None
    assert active_lib.id == "lib-01"
    assert active_lib.name == "Sci-Fi Vault"


@pytest.mark.asyncio
async def test_database_initialization(temp_library_dir: Path):
    """Verify Calibre schema + x_ extension tables + .vectors/ are initialized."""
    db_mgr = DatabaseManager(temp_library_dir)
    await db_mgr.initialize_database()

    # Verify .vectors folder created (Constitution Principle I)
    assert (temp_library_dir / ".vectors").is_dir()
    assert (temp_library_dir / "metadata.db").is_file()

    conn = await db_mgr.get_connection()
    async with conn.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
        rows = await cursor.fetchall()
        table_names = [row["name"] for row in rows]

    # Verify Calibre standard tables
    assert "books" in table_names
    assert "authors" in table_names
    assert "data" in table_names
    assert "identifiers" in table_names
    assert "tags" in table_names

    # Verify xBookLibrary extension tables
    assert "x_toc_nodes" in table_names
    assert "x_file_hashes" in table_names
    assert "x_ingestion_jobs" in table_names

    await conn.close()
