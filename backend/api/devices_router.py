"""FastAPI router for device registration, Send-to-Device, directory export, and SMTP settings."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.devices import (
    Device,
    DeviceCreateRequest,
    DeviceSyncLog,
    ExportToDirectoryRequest,
    SendToDeviceRequest,
    SMTPSettings,
)
from backend.services.device_service import DeviceService
from backend.services.email_service import EmailService
from backend.services.library_manager import LibraryManager

router = APIRouter(tags=["Devices & Send-to-Device"])


def get_config_manager() -> ConfigManager:
    return ConfigManager()


def get_library_manager(cfg: ConfigManager = Depends(get_config_manager)) -> LibraryManager:
    return LibraryManager(config_manager=cfg)


def get_email_service(cfg: ConfigManager = Depends(get_config_manager)) -> EmailService:
    app_cfg = cfg.load()
    return EmailService(smtp_settings=app_cfg.preferences.smtp_settings)


def get_device_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
    email_svc: EmailService = Depends(get_email_service),
) -> DeviceService:
    return DeviceService(library_manager=lib_mgr, email_service=email_svc)


# --- Devices CRUD ---
@router.get(
    "/api/libraries/{library_id}/devices",
    response_model=List[Device],
    summary="List all registered target devices for a library",
)
async def list_devices(
    library_id: str,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        return await device_service.list_devices(library_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/api/libraries/{library_id}/devices",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new target e-reader device",
)
async def create_device(
    library_id: str,
    req: DeviceCreateRequest,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        return await device_service.create_device(library_id, req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/api/libraries/{library_id}/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a registered device",
)
async def delete_device(
    library_id: str,
    device_id: str,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        success = await device_service.delete_device(library_id, device_id)
        if not success:
            raise HTTPException(status_code=404, detail="Device not found.")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Dispatch & Export ---
@router.post(
    "/api/libraries/{library_id}/books/{book_id}/send",
    response_model=DeviceSyncLog,
    summary="Send a book to an e-reader (e.g. Kindle via SMTP)",
)
async def send_to_device(
    library_id: str,
    book_id: int,
    req: SendToDeviceRequest,
    cfg: ConfigManager = Depends(get_config_manager),
    device_service: DeviceService = Depends(get_device_service),
):
    app_cfg = cfg.load()
    smtp_settings = app_cfg.preferences.smtp_settings
    try:
        log = await device_service.send_to_device(
            library_id, book_id, req, smtp_settings=smtp_settings
        )
        return log
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class ExportResponse(BaseModel):
    exported_path: str


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/export",
    response_model=ExportResponse,
    summary="Export a book to a local/USB directory",
)
async def export_to_directory(
    library_id: str,
    book_id: int,
    req: ExportToDirectoryRequest,
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        exported_path = await device_service.export_to_directory(library_id, book_id, req)
        return ExportResponse(exported_path=exported_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/api/libraries/{library_id}/devices/logs",
    response_model=List[DeviceSyncLog],
    summary="List recent device sync and export activity logs",
)
async def list_sync_logs(
    library_id: str,
    limit: int = Query(50, ge=1, le=200),
    device_service: DeviceService = Depends(get_device_service),
):
    try:
        return await device_service.list_sync_logs(library_id, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Global SMTP Settings ---
@router.get(
    "/api/settings/smtp",
    response_model=SMTPSettings,
    summary="Get configured SMTP settings (with password masked)",
)
async def get_smtp_settings(cfg: ConfigManager = Depends(get_config_manager)):
    app_cfg = cfg.load()
    settings = app_cfg.preferences.smtp_settings.model_copy()
    if settings.password:
        settings.password = "********"
    return settings


@router.put(
    "/api/settings/smtp",
    response_model=SMTPSettings,
    summary="Update SMTP delivery settings",
)
async def update_smtp_settings(
    new_settings: SMTPSettings,
    cfg: ConfigManager = Depends(get_config_manager),
):
    app_cfg = cfg.load()
    if new_settings.password == "********":
        # Keep existing password if not updated
        new_settings.password = app_cfg.preferences.smtp_settings.password

    app_cfg.preferences.smtp_settings = new_settings
    cfg.save(app_cfg)
    return new_settings


class TestSmtpResponse(BaseModel):
    success: bool
    message: str


@router.post(
    "/api/settings/smtp/test",
    response_model=TestSmtpResponse,
    summary="Test connection to the configured SMTP server",
)
async def test_smtp_settings(
    settings: Optional[SMTPSettings] = None,
    cfg: ConfigManager = Depends(get_config_manager),
    email_svc: EmailService = Depends(get_email_service),
):
    app_cfg = cfg.load()
    active_settings = settings or app_cfg.preferences.smtp_settings
    if active_settings.password == "********":
        active_settings.password = app_cfg.preferences.smtp_settings.password

    try:
        success = await email_svc.test_connection(active_settings)
        if success:
            return TestSmtpResponse(success=True, message="Successfully connected and authenticated with SMTP server.")
        return TestSmtpResponse(success=False, message="Could not authenticate with SMTP server.")
    except Exception as e:
        return TestSmtpResponse(success=False, message=str(e))
