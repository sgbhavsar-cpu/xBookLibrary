# Feature Specification: Core Library Data Model, Calibre Storage & Multi-Format Ingestion Strategy

**Feature Branch**: `001-core-library-ingestion`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "Core Library Model, Calibre Storage and Multi-Format Ingestion Strategy"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Multi-Format Book Upload & Ingestion (Priority: P1)

As a reader and digital book collector, I want to upload book files in various formats (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ/CBR) via a web interface so that they are automatically parsed, rich local metadata and covers are extracted, and the book is recorded in my portable library.

**Why this priority**: Core ingestion is the foundational entry point of the entire application. Without the ability to reliably parse files and record book entities, no downstream agentic enrichment, classification, summarization, or RAG can function.

**Independent Test**: Can be independently tested by uploading test files for each format (`test.epub`, `test.pdf`, `test.mobi`, `test.azw3`, `test.txt`, `test.docx`, `test.cbz`) and verifying that books are stored in SQLite and the file system with correct titles, authors, covers, and formats.

**Acceptance Scenarios**:
1. **Given** a valid EPUB or PDF file with embedded metadata and cover, **When** the user uploads it via the web interface, **Then** the system extracts title, authors, publication date, ISBN, cover image, and Table of Contents (TOC), copies the book into the deterministic Calibre folder structure, and creates the book record in `metadata.db`.
2. **Given** a book that lacks embedded metadata (e.g. a plain text or un-tagged PDF), **When** uploaded, **Then** the system gracefully falls back to clean filename heuristics for title/author and extracts sample text from the first pages for subsequent AI analysis.
3. **Given** an existing book record in the library (e.g. "Dune" in EPUB), **When** the user uploads another format of the same book (e.g. "Dune" in PDF or MOBI), **Then** the system merges the new format under the existing book record rather than creating a duplicate book entry.

---

### User Story 2 - Pluggable Parser Strategy across Full Format Suite (Priority: P1)

As a developer and system operator, I want all book parsers to adhere to a unified, pluggable `BookParserStrategy` interface so that every supported format delivers a standardized metadata and content payload.

**Why this priority**: A unified domain interface prevents format-specific branching from polluting the core library logic and guarantees extensibility for future formats.

**Independent Test**: Execute unit test suites against each concrete parser implementation using mock/fixture files, asserting that each parser outputs a valid `ParsedBookPayload` (Title, Authors, Identifiers, TOC, Cover bytes, Sample text).

**Acceptance Scenarios**:
1. **Given** an EPUB file, **When** processed by `EpubParser`, **Then** it parses the OPF package, extracts cover image bytes, spine items, and NCX/Nav TOC.
2. **Given** a PDF file, **When** processed by `PdfParser`, **Then** it extracts DocumentInfo, XMP metadata, page 1 rendered as cover image, PDF outline bookmarks as TOC, and the first 2,000 words as sample text.
3. **Given** a MOBI/AZW3 file, **When** processed by `MobiParser`, **Then** it extracts EXTH records, cover image, and chapter divisions.
4. **Given** a Comic Archive (CBZ/CBR), **When** processed by `ComicParser`, **Then** it extracts `ComicInfo.xml` (if present) and extracts the first image page as the cover thumbnail.
5. **Given** a DOCX or TXT file, **When** processed by `DocxTextParser`, **Then** it extracts document properties, heading hierarchy as TOC, and plain text sample.

---

### User Story 3 - Calibre-Compatible Portable Storage & Deterministic Layout (Priority: P2)

As a user with existing Calibre libraries or multiple reading devices, I want the storage layout and database to follow Calibre's portable folder structure so that my library remains 100% self-contained, backed up, or openable by other tooling.

**Why this priority**: Ensures long-term data ownership, zero vendor lock-in, and instant compatibility with existing e-reader tools.

**Independent Test**: Inspect the filesystem after importing 10 books across different authors, verifying that files are organized under `<LibraryRoot>/<Author>/<Title> (<Year>)/` with a valid SQLite `metadata.db` and accompanying `metadata.opf` file.

**Acceptance Scenarios**:
1. **Given** an imported book titled "Neuromancer" by "William Gibson" published in 1984, **When** persisted to disk, **Then** it is stored at `<LibraryRoot>/William Gibson/Neuromancer (1984)/Neuromancer - William Gibson.epub` with `cover.jpg` and `metadata.opf`.
2. **Given** an entire library directory moved to a new folder path or external drive, **When** the library is opened by xBookLibrary, **Then** all books, formats, covers, and metadata load seamlessly without path corruption.

---

### User Story 4 - Automated Directory Watcher & Bulk Import Scanner (Priority: P2)

As a power user, I want to designate an "Auto-Import" watch folder or scan an unorganized folder of books so that bulk collections are ingested in the background with real-time job progress.

**Why this priority**: Users frequently have folders of unorganized ebooks that need bulk ingestion without manual one-by-one file uploading.

**Independent Test**: Drop 20 ebook files into the designated auto-import directory, and assert that the file system watcher detects them, enqueues ingestion jobs, extracts metadata, and moves files into the library.

**Acceptance Scenarios**:
1. **Given** a directory designated as an Auto-Import folder, **When** new book files are added, **Then** the background watcher detects them, waits for file write completion, triggers the ingestion pipeline, and removes/archives the file from the intake folder.
2. **Given** a bulk import job of 50 books, **When** processing, **Then** the system emits WebSocket progress events indicating current file, completed count, and error reports for any unreadable files.

---

### User Story 5 - Multi-Library Registry & Switcher (Priority: P3)

As a reader with multiple library collections (e.g. "Technical & Research", "Fiction & Sci-Fi", "Comics"), I want to create and switch between distinct isolated libraries.

**Why this priority**: Isolates domain contexts, keeps databases nimble, and prepares for library-isolated RAG vector spaces.

**Independent Test**: Create two libraries ("Work" and "Personal"), add distinct books to each, and verify that switching the active library switches the active SQLite context and book lists with zero cross-contamination.

**Acceptance Scenarios**:
1. **Given** multiple registered libraries, **When** the user switches active library in the UI, **Then** the backend updates the active session to the selected library's SQLite connection and storage root.
2. **Given** a request to create a new library, **When** a new path and name are provided, **Then** the system scaffolds the directory, initializes a fresh `metadata.db`, and creates the `.vectors/` directory.

---

### Edge Cases

- **Corrupted / Incomplete Files**: If a file header is unreadable or truncated, the ingestion job marks the item as `FAILED_CORRUPT` with diagnostic error details, leaving other batch items unaffected.
- **DRM-Protected Files**: If a file is encrypted with Adobe or Kindle FairPlay DRM, the system extracts available header metadata, tags the book as `DRM_PROTECTED`, and alerts the user that full-text indexing and conversion are restricted.
- **Path Length & Special Characters**: Authors or titles containing characters illegal in Windows/Linux filesystems (`:`, `?`, `\`, `/`, `*`, `"`, `<`, `>`, `|`) or exceeding 240 characters MUST be sanitized deterministically while preserving original UTF-8 strings in the SQLite database.
- **Collision on Unknown Title/Author**: If multiple books with unknown metadata are imported simultaneously, the system MUST use UUID or file hash suffixes to prevent accidental file overwrites on disk.
- **Large Files (>500MB)**: PDF manuals or high-res comic archives MUST be processed using streaming I/O rather than loading the entire file into memory at once.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `LibraryManager` service that maintains a central registry of library paths in local application configuration (`~/.xbooklibrary/config.json`).
- **FR-002**: System MUST initialize a standard SQLite `metadata.db` schema inside each library root upon creation or first connection.
- **FR-003**: System MUST define and enforce a `BookParserStrategy` interface with concrete implementations:
  - `EpubParser` (using `ebooklib` / `zipfile` / `lxml`)
  - `PdfParser` (using `pypdf` / `pdfplumber` / `fitz`)
  - `MobiParser` (using `mobi` unpacker)
  - `ComicParser` (using `zipfile` / `rarfile` and `xml.etree`)
  - `DocxTextParser` (using `python-docx` and native text readers)
- **FR-004**: Each parser MUST return a standardized `ParsedBookPayload` containing:
  - Title (string)
  - Authors (list of strings)
  - Identifiers (dict: ISBN-10, ISBN-13, DOI, ASIN, etc.)
  - Publication Date / Year (optional string/int)
  - Publisher (optional string)
  - Description / Synopsis (optional string)
  - Table of Contents (hierarchical tree of chapter titles and page/anchor refs)
  - Cover Image (binary bytes and mime type)
  - Text Sample (first ~2,000 words for downstream agent processing)
  - Language (optional string)
- **FR-005**: System MUST store books on disk using the deterministic Calibre folder structure:  
  `<LibraryRoot>/<CleanAuthor>/<CleanTitle> (<Year>)/<CleanTitle> - <CleanAuthor>.<ext>`.
- **FR-006**: System MUST extract and persist `cover.jpg` (optimized JPEG, max 1200px dimension) in the book's directory and store a thumbnail reference in the database.
- **FR-007**: System MUST generate and keep updated a standard Calibre `metadata.opf` XML file in the book directory.
- **FR-008**: System MUST implement multi-format merging: when an imported file matches an existing book record by ISBN or normalized Title + Primary Author, the file is added to `book_formats` under that existing book.
- **FR-009**: System MUST provide REST API endpoints (FastAPI):
  - `GET /api/libraries` — List all registered libraries
  - `POST /api/libraries` — Create or register a library
  - `GET /api/books` — List books with pagination, search, and sorting
  - `GET /api/books/{id}` — Get book details, formats, TOC, and cover URL
  - `POST /api/books/upload` — Upload single or multiple book files
  - `GET /api/jobs/{job_id}` — Inspect ingestion job status and logs
- **FR-010**: System MUST provide a background `DirectoryWatcher` service that monitors designated intake folders and processes incoming files asynchronously.
- **FR-011**: System MUST compute and store SHA-256 hashes of all ingested files to prevent accidental byte-identical re-ingestion.

### Key Entities

- **Library**: Represents a self-contained book repository. Attributes: `id`, `name`, `path`, `created_at`, `book_count`.
- **Book**: Represents a creative work (abstract book entity). Attributes: `id`, `title`, `sort_title`, `publication_year`, `publisher`, `description`, `language`, `cover_path`, `rating`, `created_at`, `updated_at`.
- **Author**: Represents a book author/contributor. Attributes: `id`, `name`, `sort_name`. Linked to Book via many-to-many relationship `book_authors` with `role` (author, editor, illustrator, translator).
- **BookFormat**: Represents a physical file format of a book. Attributes: `id`, `book_id`, `format` (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ), `file_path`, `file_size_bytes`, `file_hash` (SHA-256), `created_at`.
- **Identifier**: Key-value identifier pair. Attributes: `id`, `book_id`, `type` (isbn, doi, asin, google, openlibrary), `value`.
- **TableOfContentsNode**: Node in the hierarchical book outline. Attributes: `id`, `book_id`, `title`, `level`, `page_number`, `anchor_href`, `order_index`.
- **IngestionJob**: Tracks asynchronous import tasks. Attributes: `id`, `status` (PENDING, PROCESSING, COMPLETED, FAILED), `total_files`, `processed_files`, `errors` (JSON array).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Successful ingestion of standard EPUB and PDF books with title, author, cover image, and TOC extracted in < 2.0 seconds per book on standard desktop hardware.
- **SC-002**: 100% test pass rate across parser test fixtures for all 7 formats (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ).
- **SC-003**: 0% file corruption or duplicate book entries when identical books or alternate formats of the same book are imported.
- **SC-004**: Complete library portability verified: copying an entire library folder to a new path and registering it in the application loads all books, covers, and formats with 100% fidelity.
- **SC-005**: File sanitization safely handles 100% of illegal path characters without throwing OS filesystem errors on Windows, macOS, or Linux.

---

## Assumptions

- Target operating environment has Python 3.12+ installed.
- Ingested files are accessible with standard read permissions on the local filesystem.
- The initial feature scope focuses on non-DRM book files; DRM-protected files will be recorded with metadata but full-text extraction will be gracefully skipped.
- Calibre `metadata.db` schema uses standard SQLite data types compatible with both Python's `sqlite3` and modern ORMs (SQLAlchemy 2.0).
