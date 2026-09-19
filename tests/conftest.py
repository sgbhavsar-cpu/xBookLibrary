"""Pytest configuration and shared test fixtures."""

from pathlib import Path

import pytest

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager


@pytest.fixture
def temp_library_dir(tmp_path: Path) -> Path:
    """Creates a clean temporary library root directory."""
    lib_dir = tmp_path / "TestLibrary"
    lib_dir.mkdir(parents=True, exist_ok=True)
    return lib_dir


@pytest.fixture
def test_config_manager(tmp_path: Path) -> ConfigManager:
    """Creates an isolated ConfigManager storing config in tmp_path."""
    config_dir = tmp_path / ".xbooklibrary"
    return ConfigManager(config_dir=config_dir)


@pytest.fixture
async def initialized_db_manager(temp_library_dir: Path) -> DatabaseManager:
    """Creates and initializes a DatabaseManager for the temp library."""
    db_manager = DatabaseManager(temp_library_dir)
    await db_manager.initialize_database()
    return db_manager
