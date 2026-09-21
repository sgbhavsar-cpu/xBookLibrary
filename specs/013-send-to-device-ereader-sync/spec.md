# Feature Specification: Send-to-Device & Wireless E-Reader Sync

**Feature Branch**: `013-send-to-device-ereader-sync`  
**Created**: 2026-09-21  
**Status**: Draft  
**Input**: User description: "Feature 013: Send-to-Device & Wireless E-Reader Sync (Kindle SMTP, Kobo Wi-Fi sync, KOReader sync)"

## User Scenarios & Testing

### User Story 1 - Send to Kindle via SMTP with Format Conversion (Priority: P1)

As a digital book reader owning an Amazon Kindle, I want to send any book from my xBookLibrary directly to my Kindle email address (`@kindle.com`) with one click, so that it arrives wirelessly in my Kindle library without needing a USB cable.

**Why this priority**: "Send to Kindle" is the single most widely used remote delivery method for e-reader users. Amazon deprecated MOBI support for personal documents and now prefers EPUB. Automatically ensuring the book is delivered as EPUB (converting on the fly if needed) provides seamless user delight.

**Independent Test**: Configure SMTP settings, select a book (even one with only MOBI or DOCX), trigger "Send to Kindle", verify email dispatch and delivery logging in `x_device_sync_logs`.

**Acceptance Scenarios**:
1. **Given** valid SMTP settings and a registered Kindle email, **When** a user clicks "Send to Kindle" on an EPUB or PDF book, **Then** an email is dispatched in the background with the book file attached, the subject matching the book title, and a success record logged in `x_device_sync_logs`.
2. **Given** a book that only exists in MOBI or DOCX format, **When** "Send to Kindle" is invoked, **Then** the system automatically runs the conversion engine to produce an EPUB, sends the resulting EPUB, and preserves the converted file.
3. **Given** invalid SMTP credentials or an unreachable mail server, **When** delivery fails, **Then** the failure error message is stored in `x_device_sync_logs` and surfaced to the UI without crashing the server.

---

### User Story 2 - Kobo Wireless Wi-Fi Sync (Priority: P1)

As a Kobo e-reader owner, I want my Kobo device to connect directly over Wi-Fi to xBookLibrary using the standard Kobo Store Sync protocol, so that all my books appear on my e-reader automatically and my reading progress syncs back to Calibre `#read_status`.

**Why this priority**: Kobo e-readers support wireless library syncing via custom API endpoints (e.g. Kobo Store sync emulation). This eliminates the need to plug in a USB cable every time new books are acquired.

**Independent Test**: Connect an HTTP client simulating Kobo device sync headers, retrieve library sync delta, download book binary, and update reading state.

**Acceptance Scenarios**:
1. **Given** a generated Kobo sync token, **When** a Kobo device requests `GET /v1/library/sync`, **Then** the system returns a paginated JSON delta of books with author, title, publication date, and download URLs.
2. **Given** a Kobo device downloading a book, **When** it requests `GET /v1/books/{book_id}/file`, **Then** the EPUB/KEPUB binary stream is returned with correct headers.
3. **Given** a Kobo device reporting updated reading state via `PUT /v1/library/{book_id}/state`, **Then** the reading progress percentage, last read timestamp, and `#read_status` in Calibre are updated.

---

### User Story 3 - KOReader Wireless Progress Sync (Kosync) (Priority: P2)

As a user running KOReader on my e-reader (Kindle, Kobo, Android, or E-Ink device), I want xBookLibrary to provide a compatible Kosync synchronization server, so that my reading location and progress sync bidirectionally across all my devices running KOReader.

**Why this priority**: KOReader is the most popular open-source e-reader software. Its Kosync protocol is lightweight, document-hash based, and provides two-way progress synchronization.

**Independent Test**: Register a KOReader user, authenticate, push reading progress for a document checksum, and fetch progress from another simulated client.

**Acceptance Scenarios**:
1. **Given** a KOReader client, **When** it authenticates via `POST /api/sync/koreader/users/auth`, **Then** a valid authentication response is returned.
2. **Given** a KOReader client sending reading progress via `PUT /api/sync/koreader/syncs/progress`, **Then** the document hash, progress string, and percentage are saved to the database.
3. **Given** another KOReader device opening the same book, **When** it queries `GET /api/sync/koreader/syncs/progress/{document_hash}`, **Then** it receives the latest progress location and timestamp.

---

### User Story 4 - USB / Local Device Export (Priority: P2)

As a user who prefers transferring books via USB mass storage or an SD card, I want to export selected books to a target directory with standard Calibre author/title directory formatting.

**Why this priority**: Provides universal fallback for all offline e-readers, MP3 players, and USB-mounted devices.

**Independent Test**: Select a book and target folder, trigger export, verify file is written to `{target}/{Author}/{Title} - {Author}.{ext}`.

**Acceptance Scenarios**:
1. **Given** a target folder path, **When** the user triggers export for a book, **Then** the book file is copied to the destination formatted according to Calibre naming conventions.

---

### User Story 5 - Device Management & Sync Activity Log (Priority: P3)

As a library administrator, I want a settings interface to configure SMTP credentials, manage Kindle email destinations, generate Kobo sync tokens, and view an audit log of all device sync attempts.

**Why this priority**: Users need clear visibility into whether their book transfers succeeded, failed, or are in progress.

**Independent Test**: View device settings, save SMTP settings, inspect sync audit log entries.

**Acceptance Scenarios**:
1. **Given** the Settings modal, **When** the user configures SMTP details and adds a Kindle recipient, **Then** the configuration is saved to `~/.xbooklibrary/config.json`.
2. **Given** recent sync actions, **When** the user views the Sync Logs tab, **Then** a chronological list of attempts, device types, book titles, timestamps, and delivery statuses is displayed.

---

### Edge Cases

- **Large Book Attachments**: If an EPUB/PDF exceeds Amazon's 50MB email limit, the system warns the user and marks the sync log as `failed: file exceeds 50MB limit`.
- **Offline / Transient SMTP Failures**: SMTP errors (connection timeouts, authentication rejections) are caught gracefully, recorded with human-readable error messages in `x_device_sync_logs`, and returned via API without server crashes.
- **Concurrent Device Syncs**: Multiple Kobo or KOReader devices syncing simultaneously are handled safely via non-blocking async database transactions.
- **Missing Format Conversion**: If a book has no compatible format for Kindle (and conversion fails), delivery is safely aborted with an informative error log.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide an SMTP email delivery service with support for SSL, TLS, and STARTTLS.
- **FR-002**: System MUST allow configuring default sender email, SMTP server host, port, username, and password in app preferences.
- **FR-003**: System MUST support registering named target devices with device type (`kindle`, `kobo`, `koreader`, `usb`) and recipient address / identifier.
- **FR-004**: System MUST automatically check format suitability when sending to Kindle (preferring EPUB, then PDF; converting MOBI/DOCX to EPUB if needed).
- **FR-005**: System MUST record all delivery attempts in an `x_device_sync_logs` database table (tracking `id`, `book_id`, `device_id`, `device_type`, `status`, `error_message`, `timestamp`).
- **FR-006**: System MUST implement Kobo Store Sync API v1 compatibility endpoints (`/v1/user/profile`, `/v1/library/sync`, `/v1/library/{book_id}/state`, `/v1/books/{book_id}/file`).
- **FR-007**: System MUST implement KOReader Kosync synchronization endpoints (`/api/sync/koreader/users/create`, `/auth`, `/syncs/progress`).
- **FR-008**: System MUST update Calibre custom column `#read_status` when reading progress is received from Kobo or KOReader devices.
- **FR-009**: System MUST allow exporting books to a local or mounted directory following `{Author}/{Title} - {Author}.{ext}` structure.
- **FR-010**: Frontend UI MUST provide a "Send to Device" dropdown action in Book Details and a Device Settings manager in Settings.

---

## Success Criteria

1. **Kindle SMTP Delivery**: Successfully constructs and sends MIME multipart emails with EPUB/PDF attachments and records status.
2. **Kobo Wireless Sync**: Successfully responds to Kobo device sync headers and updates reading progress.
3. **KOReader Kosync**: Successfully stores and retrieves progress hashes for multi-device sync.
4. **Test Suite Coverage**: All unit, integration, and contract tests pass with 100% success rate.
5. **Zero Frontend Regressions**: TypeScript builds cleanly with 0 errors.
