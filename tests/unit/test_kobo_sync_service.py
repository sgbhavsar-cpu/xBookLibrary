"""Unit tests for KoboSyncService."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
import aiosqlite

from backend.domain.entities import Library
from backend.services.kobo_sync_service import KoboSyncService
from tests.fixtures.generators import create_mock_calibre_library


@pytest.fixture
def mock_calibre_lib(tmp_path: Path) -> Path:
    lib_dir = tmp_path / "KoboDevLib"
    create_mock_calibre_library(lib_dir)
    return lib_dir


@pytest.fixture
async def kobo_env(mock_calibre_lib: Path):
    # Insert a device with auth_token in x_devices table
    db_path = mock_calibre_lib / "metadata.db"
    async with aiosqlite.connect(db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS x_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                target_address TEXT,
                auth_token TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_sync_at DATETIME
            )
        """)
        await db.execute(
            "INSERT INTO x_devices (id, name, device_type, auth_token) VALUES ('dev-kobo-1', 'My Kobo', 'kobo', 'token-abc-123')"
        )
        await db.commit()

    mock_lib = Library(
        id="lib-kobo",
        name="Kobo Library",
        path=str(mock_calibre_lib),
    )
    lib_mgr = MagicMock()
    lib_mgr.list_libraries.return_value = [mock_lib]
    lib_mgr.get_library.return_value = mock_lib
    return lib_mgr, "token-abc-123"


@pytest.mark.asyncio
async def test_kobo_user_profile(kobo_env):
    lib_mgr, token = kobo_env
    svc = KoboSyncService(library_manager=lib_mgr)

    profile = await svc.get_user_profile(token)
    assert profile["library_id"] == "lib-kobo"
    assert "kobo-" in profile["user_key"]


@pytest.mark.asyncio
async def test_kobo_sync_library(kobo_env):
    lib_mgr, token = kobo_env
    svc = KoboSyncService(library_manager=lib_mgr)

    resp = await svc.sync_library(token)
    assert resp.NewEntitlementCount == 2
    assert len(resp.Items) == 2
    titles = [item.Title for item in resp.Items]
    assert "Foundation" in titles
    assert "Neuromancer" in titles
    assert resp.Items[0].DownloadUrl.startswith(f"/api/sync/kobo/{token}/v1/books/")


@pytest.mark.asyncio
async def test_kobo_update_reading_state(kobo_env):
    lib_mgr, token = kobo_env
    mock_reading_svc = MagicMock()
    mock_reading_svc.save_progress = AsyncMock()

    svc = KoboSyncService(library_manager=lib_mgr, reading_service=mock_reading_svc)

    res = await svc.update_reading_state(token, book_id=1, progress_percent=42.5)
    assert res is True
    mock_reading_svc.save_progress.assert_called_once()
    args = mock_reading_svc.save_progress.call_args[0]
    assert args[0] == "lib-kobo"
    assert args[1] == 1
    assert args[2].progress_percent == 42.5


@pytest.mark.asyncio
async def test_kobo_get_book_file(kobo_env):
    lib_mgr, token = kobo_env
    svc = KoboSyncService(library_manager=lib_mgr)

    file_path, media_type, fname = await svc.get_book_file(token, book_id=1)
    assert file_path.exists()
    assert media_type == "application/epub+zip"
    assert "Foundation" in fname
