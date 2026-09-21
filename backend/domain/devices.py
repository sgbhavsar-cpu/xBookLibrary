"""Domain models and enums for device management, wireless sync, and e-reader protocols."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    KINDLE = "kindle"
    KOBO = "kobo"
    KOREADER = "koreader"
    USB = "usb"


class DeviceSyncStatus(str, Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    FAILED = "failed"


class Device(BaseModel):
    id: str
    name: str
    device_type: DeviceType
    target_address: Optional[str] = None
    auth_token: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_sync_at: Optional[datetime] = None


class DeviceCreateRequest(BaseModel):
    name: str
    device_type: DeviceType
    target_address: Optional[str] = None


class DeviceSyncLog(BaseModel):
    id: str
    book_id: int
    book_title: str
    device_id: Optional[str] = None
    device_type: DeviceType
    format_sent: str
    status: DeviceSyncStatus
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SendToDeviceRequest(BaseModel):
    device_id: Optional[str] = None
    custom_recipient: Optional[str] = None
    preferred_format: Optional[str] = None


class ExportToDirectoryRequest(BaseModel):
    target_directory: str
    format: Optional[str] = None


class KosyncProgress(BaseModel):
    document: str
    progress: str
    percentage: float
    device: Optional[str] = None
    device_id: Optional[str] = None
    timestamp: int


class SMTPSettings(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = ""


class KoboItem(BaseModel):
    Id: str
    Title: str
    Author: str
    Publisher: Optional[str] = None
    Description: Optional[str] = None
    DownloadUrl: str
    Format: str


class KoboSyncResponse(BaseModel):
    NewEntitlementCount: int
    Items: List[KoboItem]


class KoboStateUpdateRequest(BaseModel):
    ProgressPercent: float
    LastRead: Optional[str] = None
