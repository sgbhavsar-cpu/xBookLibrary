# Tasks: Send-to-Device & Wireless E-Reader Sync (Feature 013)

## Phase 1: Setup & Domain Models
- [x] T001: Define domain models and enums (`Device`, `DeviceType`, `DeviceSyncLog`, `DeviceSyncStatus`, `KosyncProgress`, `SMTPSettings`) in `backend/domain/devices.py`.
- [x] T002: Add `smtp_settings: SMTPSettings` to `UserPreferences` in `backend/config.py`.
- [x] T003: Update `backend/database/schema.py` to add `x_devices`, `x_device_sync_logs`, and `x_kosync_progress` to `CALIBRE_SCHEMA_DDL`.

## Phase 2: Core Services & Unit Tests
- [x] T004: Create unit tests for devices domain in `tests/unit/test_devices_domain.py`.
- [x] T005: Implement `backend/services/email_service.py` with SMTP delivery, MIME attachment creation, and error handling.
- [x] T006: Create unit tests for `EmailService` in `tests/unit/test_email_service.py`.
- [x] T007: Implement `backend/services/device_service.py` with device registration, Send-to-Kindle dispatch with format auto-conversion, directory export, and sync logging.
- [x] T008: Create unit tests for `DeviceService` in `tests/unit/test_device_service.py`.
- [x] T009: Implement `backend/services/kobo_sync_service.py` with Kobo profile, library sync delta, book streaming, and reading state update.
- [x] T010: Create unit tests for `KoboSyncService` in `tests/unit/test_kobo_sync_service.py`.
- [x] T011: Implement `backend/services/kosync_service.py` with user auth and progress hashing sync.
- [x] T012: Create unit tests for `KosyncService` in `tests/unit/test_kosync_service.py`.

## Phase 3: API Endpoints & Contract Tests
- [x] T013: Implement `backend/api/devices_router.py` for device CRUD, send, export, and logs.
- [x] T014: Implement `backend/api/kobo_sync_router.py` for Kobo Store Sync protocol.
- [x] T015: Implement `backend/api/kosync_router.py` for KOReader progress sync.
- [x] T016: Mount routers in `backend/main.py`.
- [x] T017: Create contract tests for device sync endpoints in `tests/contract/test_devices_api.py`.

## Phase 4: Frontend UI
- [x] T018: Add device, sync log, and SMTP TypeScript interfaces in `frontend/src/types/index.ts`.
- [x] T019: Add device API methods in `frontend/src/api/client.ts` and store state in `frontend/src/store/useStore.ts`.
- [x] T020: Build `frontend/src/components/devices/SendToDeviceModal.tsx`.
- [x] T021: Build `frontend/src/components/devices/DeviceSettingsModal.tsx`.
- [x] T022: Integrate "Send to Device" button into `frontend/src/components/DetailInspector.tsx` and header.

## Phase 5: Verification & Delivery
- [x] T023: Execute full backend test suite (`uv run pytest`) and verify 100% pass rate.
- [x] T024: Validate production frontend build (`tsc -b && vite build`).
- [x] T025: Commit Feature 013 to git.
