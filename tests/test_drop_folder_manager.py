"""Tests for DropFolderWatcherManager, drop folder deletion, and post-ingestion workflows."""

import asyncio
from pathlib import Path
import pytest

from backend.config import AppConfig, ConfigManager, Library, UserPreferences
from backend.database.connection import DatabaseManager
from backend.domain.entities import IngestionStatus
from backend.services.watcher_service import WatcherService
from backend.services.watcher_manager import DropFolderWatcherManager


@pytest.mark.asyncio
async def test_watcher_deletes_source_after_successful_import(tmp_path: Path):
    # Setup test library
    lib_dir = tmp_path / "TestLib"
    lib_dir.mkdir()
    db_mgr = DatabaseManager(lib_dir)
    await db_mgr.initialize_database()

    drop_dir = tmp_path / "DropFolder"
    drop_dir.mkdir()

    # Create dummy text book
    book_file = drop_dir / "Test Dropped Book.txt"
    book_file.write_text("Title: Dropped Book\nAuthor: John Drop\n\nChapter 1\nThis is a sample book dropped in folder.", encoding="utf-8")
    assert book_file.exists()

    # Run WatcherService with delete_source_after_import=True
    watcher = WatcherService(
        library_path=lib_dir,
        import_dir=drop_dir,
        library_id="test-lib",
        delete_source_after_import=True,
    )

    jobs = await watcher.scan_once()
    assert len(jobs) == 1
    assert jobs[0].status == IngestionStatus.COMPLETED

    # Verify source file was removed from the drop folder
    assert not book_file.exists(), "Source file should have been deleted from drop folder after successful import"


@pytest.mark.asyncio
async def test_watcher_retains_source_when_configured_false(tmp_path: Path):
    # Setup test library
    lib_dir = tmp_path / "TestLibRetain"
    lib_dir.mkdir()
    db_mgr = DatabaseManager(lib_dir)
    await db_mgr.initialize_database()

    drop_dir = tmp_path / "DropFolderRetain"
    drop_dir.mkdir()

    book_file = drop_dir / "Retained Book.txt"
    book_file.write_text("Title: Retained Book\nAuthor: Jane Retain\n\nChapter 1\nFile should remain in drop folder.", encoding="utf-8")
    assert book_file.exists()

    watcher = WatcherService(
        library_path=lib_dir,
        import_dir=drop_dir,
        library_id="test-lib-retain",
        delete_source_after_import=False,
    )

    jobs = await watcher.scan_once()
    assert len(jobs) == 1
    assert jobs[0].status == IngestionStatus.COMPLETED

    # Verify file is retained
    assert book_file.exists(), "Source file should be kept when delete_source_after_import=False"


@pytest.mark.asyncio
async def test_watcher_manager_lifecycle(tmp_path: Path):
    # Isolated config directory
    cfg_dir = tmp_path / "cfg"
    cfg_mgr = ConfigManager(config_dir=cfg_dir)

    lib_dir = tmp_path / "MgrLib"
    lib_dir.mkdir()
    db_mgr = DatabaseManager(lib_dir)
    await db_mgr.initialize_database()

    drop_dir = tmp_path / "MgrDrop"
    drop_dir.mkdir()

    app_cfg = AppConfig(
        active_library_id="lib-1",
        libraries=[Library(id="lib-1", name="Manager Library", path=str(lib_dir))],
        preferences=UserPreferences(
            auto_import_folder=str(drop_dir),
            auto_import_enabled=True,
            delete_source_after_import=True,
        ),
    )
    cfg_mgr.save(app_cfg)

    # Instantiate manager with custom config mgr
    manager = DropFolderWatcherManager()
    
    # Monkey-patch config manager in manager
    import backend.services.watcher_manager
    original_cfg_mgr = backend.services.watcher_manager.ConfigManager
    backend.services.watcher_manager.ConfigManager = lambda: cfg_mgr

    try:
        await manager.sync_with_config()
        assert manager.is_running is True

        # Stop via sync when disabled
        app_cfg.preferences.auto_import_enabled = False
        cfg_mgr.save(app_cfg)
        await manager.sync_with_config()
        assert manager.is_running is False
    finally:
        await manager.stop()
        backend.services.watcher_manager.ConfigManager = original_cfg_mgr
