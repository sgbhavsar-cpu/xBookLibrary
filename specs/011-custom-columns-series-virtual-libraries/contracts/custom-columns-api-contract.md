# API Contracts: 011 Custom Columns, Series & Virtual Libraries

## 1. Custom Columns Endpoints

### `GET /api/libraries/{library_id}/custom-columns`
Returns all custom column definitions for the specified library.
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "label": "read_status",
    "name": "Read Status",
    "datatype": "enumeration",
    "is_multiple": false,
    "normalized": true,
    "display": {
      "enum_values": ["Unread", "Reading", "Completed", "Abandoned"]
    }
  },
  {
    "id": 2,
    "label": "pages",
    "name": "Pages",
    "datatype": "int",
    "is_multiple": false,
    "normalized": false,
    "display": {}
  }
]
```

### `POST /api/libraries/{library_id}/custom-columns`
Creates a new custom column in the library's `metadata.db`.
- **Request Body**:
```json
{
  "label": "read_status",
  "name": "Read Status",
  "datatype": "enumeration",
  "display": {
    "enum_values": ["Unread", "Reading", "Completed", "Abandoned"]
  }
}
```
- **Response**: `201 Created`

### `POST /api/libraries/{library_id}/custom-columns/presets`
Installs standard presets (e.g. `#read_status`, `#difficulty`, `#rating`, `#pages`) with one call.
- **Response**: `200 OK` with created columns.

### `GET /api/books/{book_id}/custom-values`
Returns custom column values for a single book.
- **Response**: `200 OK`
```json
{
  "book_id": 42,
  "values": {
    "read_status": "Reading",
    "pages": 480,
    "rating": 5
  }
}
```

### `PUT /api/books/{book_id}/custom-values`
Updates custom column values for a book.
- **Request Body**:
```json
{
  "read_status": "Completed",
  "pages": 480,
  "rating": 5
}
```
- **Response**: `200 OK`

---

## 2. Series Endpoints

### `GET /api/libraries/{library_id}/series`
Returns all series names and their book counts.
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Foundation",
    "book_count": 7
  }
]
```

### `PUT /api/books/{book_id}/series`
Updates a book's series name and volume index.
- **Request Body**:
```json
{
  "name": "Foundation",
  "series_index": 2.0
}
```
- **Response**: `200 OK`

---

## 3. Virtual Libraries Endpoints

### `GET /api/libraries/{library_id}/virtual-libraries`
Returns all saved virtual libraries from Calibre `preferences`.
- **Response**: `200 OK`
```json
[
  {
    "name": "Unread Books",
    "query": "#read_status:Unread",
    "book_count": 14
  }
]
```

### `POST /api/libraries/{library_id}/virtual-libraries`
Creates or updates a virtual library.
- **Request Body**:
```json
{
  "name": "Sci-Fi Classics",
  "query": "tags:\"Science Fiction\" and rating:>4"
}
```
- **Response**: `200 OK`

### `DELETE /api/libraries/{library_id}/virtual-libraries/{name}`
Deletes a virtual library.
- **Response**: `200 OK`
