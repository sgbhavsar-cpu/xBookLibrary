# Research & Architectural Tradeoffs: Core Metadata Editing & Import

**Feature**: `015-core-metadata-editor-and-import`

---

## 1. Online Metadata Provider Aggregation

### Requirements
When a user clicks "Fetch Online Metadata" for a book, we want fast, ranked search candidates without requiring paid API keys or complex setups.

### Evaluated Providers
1. **Google Books API** (`https://www.googleapis.com/books/v1/volumes?q=...`):
   - **Pros**: Largest catalog of modern trade books; includes rich descriptions, categories, page counts, publisher, pubdate, and high-resolution covers.
   - **Cons**: Rate limits on unauthenticated IPs (mitigated by caching and user query throttling).
2. **OpenLibrary API** (`https://openlibrary.org/search.json?q=...` and `https://covers.openlibrary.org/`):
   - **Pros**: Completely open; excellent ISBN and work-level identifier resolution; fast cover CDN.
   - **Cons**: User-contributed summaries occasionally sparse.
3. **CrossRef API** (`https://api.crossref.org/works?query.bibliographic=...`):
   - **Pros**: Unmatched for academic papers, journals, textbook DOIs, and scholarly publications.
   - **Cons**: Usually does not include book jacket covers.

### Architecture Decision
Implement an `OnlineMetadataService` that queries Google Books and OpenLibrary in parallel via `asyncio.gather()`, aggregates and deduplicates results, computes a composite match confidence score based on title and author similarity, and returns ranked candidates.

---

## 2. Cover Art Image Processing & Storage

### Technical Strategy
- **Upload Formats**: Accept `.jpg`, `.jpeg`, `.png`, and `.webp`.
- **Normalization**: Convert all incoming images to RGB JPEG (`cover.jpg`) saved directly into the book's directory (`library/{author}/{title}/cover.jpg`).
- **Resizing**: Store full-resolution cover up to $1600 \times 2400$ at quality 85.
- **Thumbnail Cache**: Dynamic resizing in `GET /api/books/{id}/cover?width=...&height=...` uses Pillow with `Image.Resampling.LANCZOS` and returns `304 Not Modified` when HTTP `If-None-Match` or `If-Modified-Since` headers match file `mtime`.
- **Clipboard Paste**: Listen for `window.addEventListener('paste', handlePaste)` when the Edit Metadata modal is active. If `e.clipboardData.items` contains an image (`image/*`), convert to a File blob and display in the cover preview immediately.

---

## 3. Calibre `metadata.opf` Synchronization

### Requirement
Calibre writes a `metadata.opf` file alongside the e-book in the directory. If `metadata.db` is ever rebuilt or moved, Calibre re-indexes the library from these `.opf` files.

### Implementation
- Implement `OpfGenerator` in `backend/services/opf_generator.py`.
- Whenever a book is edited, ingested, or has its cover changed:
  1. Commit changes to SQLite `metadata.db`.
  2. Generate OPF 2.0 XML with Dublin Core metadata and Calibre `<meta>` extensions (`calibre:series`, `calibre:series_index`, `calibre:rating`, `calibre:timestamp`).
  3. Write atomically to `{book_dir}/metadata.opf` using a temporary file rename.

---

## 4. Multi-Format Storage in Calibre's `data` Table

### Calibre Schema Details
```sql
CREATE TABLE data (
    id INTEGER PRIMARY KEY,
    book INTEGER NOT NULL,
    format TEXT NOT NULL COLLATE NOCASE,
    uncompressed_size INTEGER NOT NULL,
    name TEXT NOT NULL,
    UNIQUE(book, format)
);
```

### Ingestion Rules for Additional Formats
- When attaching format $F$ to book $B$:
  - Format is uppercased (`PDF`, `EPUB`, `MOBI`, `CBZ`, etc.).
  - File is named `{data_row.name}.{format.lower()}`.
  - Insert or replace row in `data` table.
  - If format is primary or newly added, update book's cached format list in frontend state.
- When deleting format $F$:
  - Delete physical file from disk.
  - Delete row `WHERE book = ? AND format = ?`.
  - Ensure at least one format remains, or mark book as empty container if all formats are deleted.
