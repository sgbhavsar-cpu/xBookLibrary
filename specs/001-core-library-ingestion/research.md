# Research: Core Library Model, Calibre Storage & Multi-Format Ingestion Strategy

**Feature Branch**: `001-core-library-ingestion`  
**Date**: 2026-09-20  

## 1. Calibre Database Architecture & In-Place Adoption

### Calibre SQLite `metadata.db` Analysis
Calibre stores all library metadata inside a single SQLite database named `metadata.db` at the library root. The core tables include:
- `books`: `id INTEGER PRIMARY KEY`, `title TEXT`, `sort TEXT`, `timestamp DATETIME`, `pubdate DATETIME`, `series_index REAL`, `author_sort TEXT`, `isbn TEXT`, `path TEXT`, `uuid TEXT`, `has_cover BOOL`, `last_modified DATETIME`.
- `authors`: `id INTEGER PRIMARY KEY`, `name TEXT`, `sort TEXT`, `link TEXT`.
- `books_authors_link`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `author INTEGER`.
- `data`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `format TEXT`, `uncompressed_size INTEGER`, `name TEXT`.
- `identifiers`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `type TEXT`, `val TEXT`.
- `series`: `id INTEGER PRIMARY KEY`, `name TEXT`, `sort TEXT`.
- `books_series_link`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `series INTEGER`.
- `tags`: `id INTEGER PRIMARY KEY`, `name TEXT`.
- `books_tags_link`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `tag INTEGER`.
- `comments`: `id INTEGER PRIMARY KEY`, `book INTEGER`, `text TEXT`.

### Zero-Copy In-Place Adoption Strategy
1. **Introspection**: When an existing library is selected, xBookLibrary checks for `metadata.db`. It validates that the essential tables exist.
2. **Non-Destructive Augmentation**: To store xBookLibrary-specific extensions (such as hierarchical Table of Contents, ingestion jobs, and AI summary pointers) without altering Calibre's native schema or breaking third-party readers, xBookLibrary introduces isolated `x_` prefixed tables:
   - `x_toc_nodes` (`id`, `book_id`, `title`, `level`, `page_number`, `anchor_href`, `order_index`)
   - `x_ingestion_jobs` (`id`, `status`, `total_files`, `processed_files`, `error_log`, `created_at`)
   - `x_library_metadata` (`key`, `value`)
   Calibre completely ignores unknown tables, guaranteeing 100% two-way compatibility.
3. **Directory Layout**: Books remain at their current relative path stored in `books.path` (e.g. `William Gibson/Neuromancer (1984)`).

---

## 2. Multi-Format Book Parser Strategies & Libraries

We selected the following mature, pure/lightweight Python libraries for the parser strategies:

| Format | Library / Tool | Metadata Extracted | Cover Extraction | TOC Extraction |
| :--- | :--- | :--- | :--- | :--- |
| **EPUB** | `ebooklib` + `lxml` | OPF metadata (DC:title, creator, date, identifier) | Manifest item with `cover-image` property | NCX / Nav document spine tree |
| **PDF** | `pypdf` + `pypdfium2` | DocumentInfo & XMP Dublin Core metadata | Page 1 rendered to JPEG via `pypdfium2` | PDF outline / bookmark tree |
| **MOBI / AZW3** | PalmDOC / EXTH parser (`mobi` / custom byte parser) | EXTH records (Title, Author, ASIN, Date) | EXTH record 201 (CoverOffset) image bytes | NCX or internal Guide TOC |
| **CBZ / CBR** | `zipfile` / `rarfile` | `ComicInfo.xml` (Series, Number, Title, Credits) | First sorted image in archive | N/A (Comic page list) |
| **DOCX** | `python-docx` | CoreProperties (title, author, created) | Embedded thumbnail if present | Heading styles (Heading 1, 2, 3) |
| **TXT / MD** | `chardet` (encoding) + regex | First line or Markdown `# Title`, Frontmatter | Generated title placeholder | Markdown headers `#`, `##` |

### Uniform Contract: `ParsedBookPayload`
All parsers implement the abstract `BookParserStrategy`:
```python
class BookParserStrategy(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> ParsedBookPayload:
        pass
```
The resulting `ParsedBookPayload` is format-agnostic, enabling downstream services (storage, metadata diff, summarizer) to work with a single unified data model.

---

## 3. Calibre-Standard File Organization & Path Sanitization

### Path Sanitization Rules
Operating systems (especially Windows) restrict certain characters: `\ / : * ? " < > |`.
- Filename Sanitizer:
  ```python
  def sanitize_filename(name: str, max_length: int = 120) -> str:
      clean = re.sub(r'[\\/*?:"<>|]', "_", name).strip()
      clean = re.sub(r"\s+", " ", clean)
      return clean[:max_length]
  ```
- Folder Hierarchy:
  `<LibraryRoot>/<CleanAuthor>/<CleanTitle> (<Year>)/`
  - Main file: `<CleanTitle> - <CleanAuthor>.<ext>`
  - Cover: `cover.jpg`
  - OPF: `metadata.opf` (standard Calibre XML metadata format)

---

## 4. Asynchronous Ingestion Pipeline & Background Watcher

1. **Intake Processing**:
   - Files uploaded via HTTP multipart or detected by the `watchfiles` directory watcher are enqueued in an asynchronous worker queue.
   - SHA-256 hash is computed immediately to check for duplicates.
2. **Duplicate Handling**:
   - If hash matches an existing file in `data`, the import is flagged as `DUPLICATE_IDENTICAL`.
   - If ISBN or (Normalized Title + Primary Author) matches an existing book record, the file is added as a new format under that book (e.g. adding EPUB to existing PDF).
   - Otherwise, a new Book record and physical directory are created.
3. **Progress Reporting**:
   - Ingestion jobs are tracked in `x_ingestion_jobs` and broadcasted via Server-Sent Events (SSE) or WebSocket to the frontend UI.
