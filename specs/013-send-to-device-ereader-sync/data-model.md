# Feature 013: Data Model & SQLite Extension Schema

## 1. Domain Entities & Enums

### 1.1 DeviceType Enum
```python
from enum import Enum

class DeviceType(str, Enum):
    KINDLE = "kindle"
    KOBO = "kobo"
    KOREADER = "koreader"
    USB = "usb"
```

### 1.2 DeviceSyncStatus Enum
```python
class DeviceSyncStatus(str, Enum):
    PENDING = "pending"
    IN_FLIGHT = "in_flight"
    COMPLETED = "completed"
    FAILED = "failed"
```

### 1.3 Device Model
```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Device(BaseModel):
    id: str
    name: str
    device_type: DeviceType
    target_address: Optional[str] = None  # e.g. email or mount path
    auth_token: Optional[str] = None      # for wireless sync token
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_sync_at: Optional[datetime] = None

class DeviceCreateRequest(BaseModel):
    name: str
    device_type: DeviceType
    target_address: Optional[str] = None
```

### 1.4 DeviceSyncLog Model
```python
class DeviceSyncLog(BaseModel):
    id: str
    book_id: int
    book_title: str
    device_id: Optional[str] = None
    device_type: DeviceType
    format_sent: str
    status: DeviceSyncStatus
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.5 KosyncProgress Model
```python
class KosyncProgress(BaseModel):
    document: str       # MD5 or SHA1 hash of book
    progress: str       # e-reader location string
    percentage: float   # 0.0 to 1.0
    device: str         # Device name
    device_id: str      # Unique hardware ID
    timestamp: int      # Epoch timestamp
```

### 1.6 SMTPSettings (Stored in Global AppConfig Preferences)
```python
class SMTPSettings(BaseModel):
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    sender_email: str = ""
```

---

## 2. SQLite Extension Schema (`CALIBRE_SCHEMA_DDL`)

In-place Calibre extension tables:

```sql
CREATE TABLE IF NOT EXISTS x_devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    device_type TEXT NOT NULL,
    target_address TEXT,
    auth_token TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_sync_at DATETIME
);

CREATE TABLE IF NOT EXISTS x_device_sync_logs (
    id TEXT PRIMARY KEY,
    book_id INTEGER NOT NULL,
    book_title TEXT NOT NULL,
    device_id TEXT,
    device_type TEXT NOT NULL,
    format_sent TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(device_id) REFERENCES x_devices(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS x_kosync_progress (
    document_hash TEXT PRIMARY KEY,
    progress TEXT NOT NULL,
    percentage REAL NOT NULL,
    device TEXT,
    device_id TEXT,
    updated_at INTEGER NOT NULL
);
```
