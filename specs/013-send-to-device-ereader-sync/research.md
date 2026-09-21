# Feature 013: Research & Technical Architecture

## 1. Kindle SMTP Personal Document Delivery Protocol

### 1.1 Amazon Send-to-Kindle Requirements
- **Recipient Address**: Target email address formatted as `<username>@kindle.com`.
- **Approved Sender**: The sender email configured in SMTP settings must be added by the user to their "Approved Personal Document E-mail List" in Amazon account settings (Content & Devices -> Preferences).
- **Accepted Formats**: EPUB, PDF, DOCX, TXT, RTF, HTM, HTML, PNG, GIF, JPG, BMP.
  - *Critical note*: Amazon has officially deprecated MOBI/AZW3 for Personal Document Service. EPUB is now the strongly recommended format.
  - *Automated fallback*: When a user requests to send a book that is only available in MOBI or DOCX, xBookLibrary leverages `ConversionService` (from Feature 010) to automatically convert the book to EPUB prior to email dispatch.
- **Attachment Size Limit**: Maximum 50MB per email. Books exceeding 50MB must fail early with a clear notification.
- **Subject & Content**: Subject line is set to the book title; empty body or minimal metadata summary.

### 1.2 Python SMTP Implementation (`aiosmtplib` / `email.mime`)
- Asynchronous email sending via `aiosmtplib` or standard `smtplib` run inside an `asyncio.to_thread` executor.
- Supports STARTTLS (port 587), SSL/TLS (port 465), or plaintext (port 25).
- Credentials stored securely in `~/.xbooklibrary/config.json` under `UserPreferences.smtp_settings`.

---

## 2. Kobo Wireless Wi-Fi Sync Protocol

### 2.1 Protocol Emulation
Kobo e-readers (Clara, Libra, Sage, Elipsa, etc.) can be pointed to a custom sync server by configuring `api_endpoint` in `Kobo eReader.conf`:
```ini
[OneStoreServices]
api_endpoint=http://<server-ip>:8000/api/sync/kobo/<token>
```
The Kobo firmware expects standard Kobo Store API endpoints:
1. `GET /v1/user/profile`: Returns basic user account and library identifier.
2. `GET /v1/library/sync`: Returns a JSON feed of synchronized items with metadata (title, author, publisher, ISBN) and download URLs.
3. `PUT /v1/library/{book_id}/state`: Receives reading progress updates sent by the Kobo device when connected to Wi-Fi.
   - Payload contains `ProgressPercent`, `LastRead`, `TimeSpentReading`, etc.
   - xBookLibrary translates this directly into `x_reading_progress` and updates the Calibre `#read_status` column.
4. `GET /v1/books/{book_id}/file`: Streams the EPUB book binary directly to the e-reader.

---

## 3. KOReader Kosync Protocol

### 3.1 Kosync Specification
KOReader provides a lightweight, open-source progress synchronization protocol:
- **Client Auth**: `POST /users/auth` with `username` and `password` or API token; returns `{"auth": true, "user": username}`.
- **Push Progress**: `PUT /syncs/progress`
  - Payload:
    ```json
    {
      "document": "<md5/sha1 hash of book file>",
      "progress": "/6/4[chapter1]!/4/2/1:0",
      "percentage": 0.42,
      "device": "Kobo Clara 2E",
      "device_id": "c3f81e...",
      "timestamp": 1726912345
    }
    ```
- **Fetch Progress**: `GET /syncs/progress/{document_hash}`
  - Returns the latest progress record across all user devices.

---

## 4. USB / Mass Storage Directory Export
- Standard Calibre folder template:
  `{Author}/{Title} ({Year})/{Title} - {Author}.{ext}`
- Copies the format file cleanly to any local mount path or attached USB drive directory.
