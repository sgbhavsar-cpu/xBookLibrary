"""Contract tests for Feature 013 Device Management and Sync API endpoints."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Library
from backend.main import app
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def mock_devices_contract_library(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_dir = tmp_path / "ContractDevicesLib"
    lib_dir.mkdir(parents=True)

    db_mgr = DatabaseManager(lib_dir)
    asyncio.run(db_mgr.initialize_database())

    async def seed():
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            cursor = await conn.execute(
                "INSERT INTO books (title, author_sort, path) VALUES ('Foundation', 'Asimov, Isaac', 'Asimov/Foundation')"
            )
            book_id = cursor.lastrowid
            await conn.execute(
                "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'EPUB', 1024, 'Foundation - Isaac Asimov')",
                (book_id,),
            )
            await conn.commit()
            return book_id

    book_id = asyncio.run(seed())

    book_folder = lib_dir / "Asimov" / "Foundation"
    book_folder.mkdir(parents=True)
    create_sample_epub(book_folder / "Foundation - Isaac Asimov.epub", title="Foundation", author="Isaac Asimov")

    cfg_mgr = ConfigManager(cfg_dir)
    lib = Library(
        id="lib-contract-devices",
        name="Contract Devices Lib",
        path=str(lib_dir),
    )
    cfg_mgr.register_library(lib, set_active=True)

    return "lib-contract-devices", book_id, lib_dir


@pytest.mark.asyncio
async def test_device_crud_contract(mock_devices_contract_library):
    lib_id, book_id, _ = mock_devices_contract_library
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create Kindle device
        res = await client.post(
            f"/api/libraries/{lib_id}/devices",
            json={"name": "Paperwhite", "device_type": "kindle", "target_address": "test@kindle.com"},
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Paperwhite"
        assert data["device_type"] == "kindle"
        dev_id = data["id"]

        # 2. List devices
        list_res = await client.get(f"/api/libraries/{lib_id}/devices")
        assert list_res.status_code == 200
        items = list_res.json()
        assert len(items) == 1
        assert items[0]["id"] == dev_id

        # 3. Delete device
        del_res = await client.delete(f"/api/libraries/{lib_id}/devices/{dev_id}")
        assert del_res.status_code == 204

        # 4. Verify empty list
        empty_res = await client.get(f"/api/libraries/{lib_id}/devices")
        assert len(empty_res.json()) == 0


@pytest.mark.asyncio
async def test_send_to_device_contract(mock_devices_contract_library):
    lib_id, book_id, _ = mock_devices_contract_library
    transport = ASGITransport(app=app)

    with patch("backend.services.email_service.EmailService.send_book_email", new_callable=AsyncMock) as mock_send:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.post(
                f"/api/libraries/{lib_id}/books/{book_id}/send",
                json={"custom_recipient": "kindle_user@kindle.com", "preferred_format": "EPUB"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "completed"
            assert data["format_sent"] == "EPUB"
            assert data["book_id"] == book_id
            mock_send.assert_called_once()

            # Check logs endpoint
            logs_res = await client.get(f"/api/libraries/{lib_id}/devices/logs")
            assert logs_res.status_code == 200
            logs = logs_res.json()
            assert len(logs) >= 1
            assert logs[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_kobo_and_kosync_contracts(mock_devices_contract_library):
    lib_id, book_id, _ = mock_devices_contract_library
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a Kobo device to get auth_token
        kobo_dev_res = await client.post(
            f"/api/libraries/{lib_id}/devices",
            json={"name": "My Kobo", "device_type": "kobo"},
        )
        assert kobo_dev_res.status_code == 201
        kobo_token = kobo_dev_res.json()["auth_token"]
        assert kobo_token is not None

        # 1. Kobo user profile
        prof_res = await client.get(f"/api/sync/kobo/{kobo_token}/v1/user/profile")
        assert prof_res.status_code == 200
        assert prof_res.json()["library_id"] == lib_id

        # 2. Kobo library sync
        sync_res = await client.get(f"/api/sync/kobo/{kobo_token}/v1/library/sync")
        assert sync_res.status_code == 200
        assert sync_res.json()["NewEntitlementCount"] >= 1

        # 3. Kobo reading state update
        state_res = await client.put(
            f"/api/sync/kobo/{kobo_token}/v1/library/{book_id}/state",
            json={"ProgressPercent": 50.0},
        )
        assert state_res.status_code == 200
        assert state_res.json()["success"] is True

        # 4. KOReader push progress & get progress
        push_res = await client.put(
            "/api/sync/koreader/syncs/progress",
            json={
                "document": "doc123456789",
                "progress": "/6/2[part1]",
                "percentage": 0.75,
                "device": "KOReader Device",
                "device_id": "hw-1",
                "timestamp": 1726919000,
            },
        )
        assert push_res.status_code == 200
        assert push_res.json()["document"] == "doc123456789"

        get_prog_res = await client.get("/api/sync/koreader/syncs/progress/doc123456789")
        assert get_prog_res.status_code == 200
        assert get_prog_res.json()["percentage"] == 0.75


@pytest.mark.asyncio
async def test_smtp_settings_contract(mock_devices_contract_library):
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get settings
        res = await client.get("/api/settings/smtp")
        assert res.status_code == 200
        orig = res.json()
        assert "host" in orig

        # Update settings
        up_res = await client.put(
            "/api/settings/smtp",
            json={
                "host": "mail.customserver.com",
                "port": 465,
                "username": "books@customserver.com",
                "password": "secretpassword",
                "use_tls": False,
                "use_ssl": True,
                "sender_email": "books@customserver.com",
            },
        )
        assert up_res.status_code == 200
        updated = up_res.json()
        assert updated["host"] == "mail.customserver.com"
        assert updated["use_ssl"] is True

        # Verify password masking on get
        masked_res = await client.get("/api/settings/smtp")
        assert masked_res.json()["password"] == "********"
