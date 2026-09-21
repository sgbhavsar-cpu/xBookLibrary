# Feature 013: Device Sync API Contract

## 1. Device Management Endpoints

### `GET /api/libraries/{library_id}/devices`
Returns all registered devices for the specified library.
- **Response 200**:
  ```json
  [
    {
      "id": "dev-1a2b3c4d",
      "name": "Jane's Kindle Oasis",
      "device_type": "kindle",
      "target_address": "jane_kindle@kindle.com",
      "auth_token": null,
      "created_at": "2026-09-21T10:00:00Z",
      "last_sync_at": "2026-09-21T10:30:00Z"
    }
  ]
  ```

### `POST /api/libraries/{library_id}/devices`
Registers a new target device.
- **Request Body**:
  ```json
  {
    "name": "Living Room Kobo Clara",
    "device_type": "kobo",
    "target_address": null
  }
  ```
- **Response 201**: Returns created `Device` object with generated `auth_token` (for wireless devices).

### `DELETE /api/libraries/{library_id}/devices/{device_id}`
Deletes a registered device.
- **Response 204**: No Content.

---

## 2. Dispatch / Send-to-Device

### `POST /api/libraries/{library_id}/books/{book_id}/send`
Sends a book to a registered device (e.g. Kindle via SMTP) with auto-conversion if needed.
- **Request Body**:
  ```json
  {
    "device_id": "dev-1a2b3c4d",
    "format": "EPUB"
  }
  ```
- **Response 200**:
  ```json
  {
    "log_id": "log-9f8e7d6c",
    "status": "completed",
    "message": "Dispatched Foundation to jane_kindle@kindle.com as EPUB"
  }
  ```

### `POST /api/libraries/{library_id}/books/{book_id}/export`
Copies the book file to a target local/USB directory formatted in Calibre structure.
- **Request Body**:
  ```json
  {
    "target_directory": "E:/documents",
    "format": "EPUB"
  }
  ```
- **Response 200**:
  ```json
  {
    "exported_path": "E:/documents/Isaac Asimov/Foundation (1951)/Foundation - Isaac Asimov.epub"
  }
  ```

### `GET /api/libraries/{library_id}/devices/logs`
Returns the recent activity log for device transfers.
- **Response 200**: List of `DeviceSyncLog` items.

---

## 3. Kobo Wireless Sync Protocol

### `GET /api/sync/kobo/{auth_token}/v1/user/profile`
- **Response 200**:
  ```json
  {
    "user_key": "kobo-user-1",
    "user_id": "user-1",
    "library_id": "lib-ca322e95"
  }
  ```

### `GET /api/sync/kobo/{auth_token}/v1/library/sync`
Returns library catalog items with metadata and download URLs.
- **Response 200**:
  ```json
  {
    "NewEntitlementCount": 3,
    "Items": [
      {
        "Id": "book-1",
        "Title": "Foundation",
        "Author": "Isaac Asimov",
        "DownloadUrl": "/api/sync/kobo/{auth_token}/v1/books/1/file",
        "Format": "EPUB"
      }
    ]
  }
  ```

### `PUT /api/sync/kobo/{auth_token}/v1/library/{book_id}/state`
Receives reading progress from Kobo and updates Calibre `#read_status`.
- **Request Body**:
  ```json
  {
    "ProgressPercent": 45.5,
    "LastRead": "2026-09-21T11:00:00Z"
  }
  ```
- **Response 200**: `{"success": true}`.

### `GET /api/sync/kobo/{auth_token}/v1/books/{book_id}/file`
Binary file stream of book with `application/epub+zip` content type.

---

## 4. KOReader Wireless Progress Sync (Kosync)

### `POST /api/sync/koreader/users/create`
Registers a Kosync user.
- **Request Body**: `{"username": "reader", "password": "secret"}`
- **Response 201**: `{"created": true, "username": "reader"}`

### `POST /api/sync/koreader/users/auth`
- **Request Body**: `{"username": "reader", "password": "secret"}`
- **Response 200**: `{"auth": true, "user": "reader"}`

### `PUT /api/sync/koreader/syncs/progress`
Pushes reading progress for a document checksum.
- **Request Body**:
  ```json
  {
    "document": "e80b5017098950fc58aad83c8c14978e",
    "progress": "/6/4[chapter1]!/4/2/1:0",
    "percentage": 0.52,
    "device": "Kindle PW5",
    "device_id": "kpw5-4921",
    "timestamp": 1726914560
  }
  ```
- **Response 200**: `{"document": "e80b5017...", "timestamp": 1726914560}`

### `GET /api/sync/koreader/syncs/progress/{document_hash}`
- **Response 200**: Returns latest `KosyncProgress` object.

---

## 5. Global SMTP Settings

### `GET /api/settings/smtp`
Returns current SMTP config (excluding sensitive password).

### `PUT /api/settings/smtp`
Updates SMTP config.

### `POST /api/settings/smtp/test`
Validates connection to the configured SMTP server.
