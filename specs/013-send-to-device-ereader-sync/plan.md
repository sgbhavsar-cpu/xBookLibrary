# Implementation Plan: Send-to-Device & Wireless E-Reader Sync

## Architecture & Component Breakdown

```mermaid
graph TD
    UI[Frontend: Send-to-Device Modal & Settings Panel] --> API[FastAPI Device & Sync Routers]
    API --> DS[DeviceService]
    API --> KS[KoboSyncService]
    API --> KOS[KosyncService]
    
    DS --> ES[EmailService (aiosmtplib / smtplib)]
    DS --> CS[ConversionService (Auto-convert non-EPUB)]
    DS --> DB[(Calibre metadata.db / x_tables)]
    
    KS --> DB
    KS --> CC[CustomColumnsService (#read_status sync)]
    
    KOS --> DB
    KOS --> CC
```

### Key Modules:
1. **Domain Layer**:
   - `backend/domain/devices.py`: Pydantic models for `Device`, `DeviceSyncLog`, `KosyncProgress`, `SMTPSettings`, request schemas.
2. **Database Layer**:
   - `backend/database/schema.py`: Augment `CALIBRE_SCHEMA_DDL` with `x_devices`, `x_device_sync_logs`, `x_kosync_progress`.
3. **Service Layer**:
   - `backend/services/email_service.py`: Asynchronous SMTP MIME multipart builder with attachment handling and size checks.
   - `backend/services/device_service.py`: Device registration, Send-to-Kindle dispatch with auto-conversion, local directory export, sync audit logging.
   - `backend/services/kobo_sync_service.py`: Kobo Store API compatibility, metadata catalog generation, file streaming, reading progress sync to `#read_status`.
   - `backend/services/kosync_service.py`: KOReader Kosync user auth, document hash progress storage and retrieval.
4. **API Layer**:
   - `backend/api/devices_router.py`: Mounted at `/api/libraries/{library_id}/devices`, `/api/settings/smtp`.
   - `backend/api/kobo_sync_router.py`: Mounted at `/api/sync/kobo`.
   - `backend/api/kosync_router.py`: Mounted at `/api/sync/koreader`.
5. **Frontend Layer**:
   - `frontend/src/types/index.ts`: Device, sync log, and SMTP types.
   - `frontend/src/api/client.ts`: Device management, send-to-device, and SMTP test methods.
   - `frontend/src/components/devices/SendToDeviceModal.tsx`: Modal for choosing target device, Kindle email, or export path.
   - `frontend/src/components/devices/DeviceSettings.tsx`: Settings panel to configure SMTP and registered devices.
   - `frontend/src/components/DetailInspector.tsx`: "Send to Device" action button.
