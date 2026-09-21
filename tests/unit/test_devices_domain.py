"""Unit tests for Feature 013 Devices domain models and enums."""

from datetime import datetime
from backend.domain.devices import (
    Device,
    DeviceCreateRequest,
    DeviceSyncLog,
    DeviceSyncStatus,
    DeviceType,
    KosyncProgress,
    SMTPSettings,
)


def test_device_creation_and_defaults():
    dev = Device(
        id="dev-123",
        name="My Kindle",
        device_type=DeviceType.KINDLE,
        target_address="user@kindle.com",
    )
    assert dev.id == "dev-123"
    assert dev.name == "My Kindle"
    assert dev.device_type == DeviceType.KINDLE
    assert dev.target_address == "user@kindle.com"
    assert dev.auth_token is None
    assert isinstance(dev.created_at, datetime)


def test_device_sync_log_model():
    log = DeviceSyncLog(
        id="log-456",
        book_id=1,
        book_title="Foundation",
        device_id="dev-123",
        device_type=DeviceType.KINDLE,
        format_sent="EPUB",
        status=DeviceSyncStatus.COMPLETED,
    )
    assert log.id == "log-456"
    assert log.status == DeviceSyncStatus.COMPLETED
    assert log.error_message is None


def test_kosync_progress_model():
    prog = KosyncProgress(
        document="e80b5017098950fc",
        progress="/6/4[chapter1]!/4/2/1:0",
        percentage=0.65,
        device="Kobo Libra 2",
        device_id="kobo-999",
        timestamp=1726914560,
    )
    assert prog.document == "e80b5017098950fc"
    assert prog.percentage == 0.65
    assert prog.device == "Kobo Libra 2"


def test_smtp_settings_defaults():
    smtp = SMTPSettings()
    assert smtp.host == "smtp.gmail.com"
    assert smtp.port == 587
    assert smtp.use_tls is True
    assert smtp.use_ssl is False
