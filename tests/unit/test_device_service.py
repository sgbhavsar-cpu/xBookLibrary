"""Unit tests for DeviceService."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.domain.devices import (
    DeviceCreateRequest,
    DeviceSyncStatus,
    DeviceType,
    ExportToDirectoryRequest,
    SendToDeviceRequest,
    SMTPSettings,
)
from backend.services.device_service import DeviceService
from tests.fixtures.generators import create_mock_calibre_library


@pytest.fixture
def mock_calibre_lib(tmp_path: Path) -> Path:
    lib_dir = tmp_path / "DevLib"
    create_mock_calibre_library(lib_dir)
    return lib_dir


@pytest.fixture
def mock_lib_mgr(mock_calibre_lib: Path) -> MagicMock:
    mgr = MagicMock()
    mock_lib = MagicMock()
    mock_lib.id = "lib-test"
    mock_lib.path = str(mock_calibre_lib)
    mgr.get_library.return_value = mock_lib
    return mgr


@pytest.mark.asyncio
async def test_device_crud_lifecycle(mock_lib_mgr: MagicMock):
    svc = DeviceService(library_manager=mock_lib_mgr)

    # 1. Create Device
    req = DeviceCreateRequest(
        name="My Oasis",
        device_type=DeviceType.KINDLE,
        target_address="user@kindle.com",
    )
    dev = await svc.create_device("lib-test", req)
    assert dev.name == "My Oasis"
    assert dev.device_type == DeviceType.KINDLE
    assert dev.target_address == "user@kindle.com"
    assert dev.auth_token is None

    # 2. List Devices
    devices = await svc.list_devices("lib-test")
    assert len(devices) == 1
    assert devices[0].id == dev.id

    # 3. Create Wireless Device (Kobo) generates auth_token
    kobo_req = DeviceCreateRequest(
        name="My Kobo Clara",
        device_type=DeviceType.KOBO,
    )
    kobo_dev = await svc.create_device("lib-test", kobo_req)
    assert kobo_dev.auth_token is not None

    devices_updated = await svc.list_devices("lib-test")
    assert len(devices_updated) == 2

    # 4. Delete Device
    deleted = await svc.delete_device("lib-test", dev.id)
    assert deleted is True

    devices_final = await svc.list_devices("lib-test")
    assert len(devices_final) == 1
    assert devices_final[0].id == kobo_dev.id


@pytest.mark.asyncio
async def test_send_to_device_kindle_success(mock_lib_mgr: MagicMock, mock_calibre_lib: Path):
    mock_email_svc = MagicMock()
    mock_email_svc.send_book_email = AsyncMock()

    svc = DeviceService(library_manager=mock_lib_mgr, email_service=mock_email_svc)

    # Book 1 has EPUB and PDF in mock_calibre_library
    req = SendToDeviceRequest(
        custom_recipient="reader@kindle.com",
        preferred_format="EPUB",
    )
    smtp_settings = SMTPSettings(sender_email="admin@library.com")

    log = await svc.send_to_device("lib-test", book_id=1, req=req, smtp_settings=smtp_settings)
    assert log.status == DeviceSyncStatus.COMPLETED
    assert log.format_sent == "EPUB"
    assert log.book_id == 1
    assert log.error_message is None

    mock_email_svc.send_book_email.assert_called_once()
    call_kwargs = mock_email_svc.send_book_email.call_args[1]
    assert call_kwargs["recipient"] == "reader@kindle.com"
    assert call_kwargs["subject"] == "Foundation"


@pytest.mark.asyncio
async def test_export_to_directory(mock_lib_mgr: MagicMock, tmp_path: Path):
    svc = DeviceService(library_manager=mock_lib_mgr)
    export_dest = tmp_path / "USB_Drive"

    req = ExportToDirectoryRequest(
        target_directory=str(export_dest),
        format="EPUB",
    )
    exported_path = await svc.export_to_directory("lib-test", book_id=1, req=req)

    assert Path(exported_path).exists()
    assert "Isaac Asimov" in exported_path
    assert "Foundation" in exported_path

    # Verify log entry created
    logs = await svc.list_sync_logs("lib-test")
    assert len(logs) >= 1
    assert logs[0].device_type == DeviceType.USB
    assert logs[0].status == DeviceSyncStatus.COMPLETED
