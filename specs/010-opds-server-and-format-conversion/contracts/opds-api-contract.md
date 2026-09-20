# API Contract: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

## 1. OPDS 1.2 Catalog Feeds (Atom XML)

### Root Catalog Feed
- **Path**: `GET /opds` or `GET /api/opds/v1.2`
- **Response**: `application/atom+xml;profile=opds-catalog;kind=navigation;charset=utf-8`
- **Description**: Returns root navigation links (All Books, Recent, Authors, Taxonomies, OpenSearch).

### All Books Acquisition Feed
- **Path**: `GET /opds/books?page=1&limit=50`
- **Response**: `application/atom+xml;profile=opds-catalog;kind=acquisition;charset=utf-8`
- **Description**: Paged Atom feed of all books with acquisition download links and cover thumbnails.

### Recent Additions Feed
- **Path**: `GET /opds/recent`
- **Response**: `application/atom+xml;profile=opds-catalog;kind=acquisition;charset=utf-8`

### Taxonomy / Category Feeds
- **Path**: `GET /opds/taxonomies` (Navigation)
- **Path**: `GET /opds/taxonomies/{category_path}` (Acquisition)

### OpenSearch 1.1 Specification
- **Path**: `GET /opds/opensearch.xml`
- **Response**: `application/opensearchdescription+xml;charset=utf-8`

### OpenSearch Query Feed
- **Path**: `GET /opds/search?q={searchTerms}`
- **Response**: `application/atom+xml;profile=opds-catalog;kind=acquisition;charset=utf-8`

---

## 2. OPDS 2.0 Catalog Feed (Readium JSON)

### OPDS 2.0 Root Feed
- **Path**: `GET /api/opds/v2.0`
- **Response**: `application/opds+json;charset=utf-8`
- **Description**: Readium-compliant JSON catalog manifest with `navigation` and `publications`.

---

## 3. Format Conversion Endpoints

### Start Conversion Job
- **Path**: `POST /api/convert`
- **Request Body**:
```json
{
  "book_id": 42,
  "source_format": "MOBI",
  "target_format": "EPUB"
}
```
- **Response**: `202 Accepted`
```json
{
  "job_id": "conv-550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Conversion job queued"
}
```

### Get Conversion Job Status
- **Path**: `GET /api/convert/jobs/{job_id}`
- **Response**: `200 OK`
```json
{
  "id": "conv-550e8400-e29b-41d4-a716-446655440000",
  "book_id": 42,
  "source_format": "MOBI",
  "target_format": "EPUB",
  "status": "completed",
  "percent_complete": 100,
  "engine_used": "calibre_cli",
  "output_size_bytes": 1450230,
  "logs": ["Starting conversion...", "Successfully generated EPUB container"]
}
```
