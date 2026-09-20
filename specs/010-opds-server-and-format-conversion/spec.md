# Feature Specification: 010 OPDS 1.2/2.0 Catalog Feed Server & Format Conversion Engine

**Feature Branch**: `010-opds-server-and-format-conversion`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: OPDS 1.2 & 2.0 Feed Server (compatible with KOReader, Moon+ Reader, Apple Books) and Background Format Conversion Engine (MOBI ➔ EPUB, EPUB ➔ PDF, CBZ ➔ PDF/EPUB, TXT ➔ EPUB).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - OPDS 1.2 & 2.0 Catalog Feed for E-Readers (Priority: P1)

As an avid reader with an e-ink device (KOReader on Kobo/Kindle) or a mobile e-reader app (Moon+ Reader, Apple Books, KyBook), I want to connect to `http://<server-ip>:8000/opds` over Wi-Fi so that I can browse my entire xBookLibrary catalog, view book covers, search by author or category, and download EPUB/PDF books directly onto my device.

**Why this priority**: OPDS (Open Publication Distribution System) is the global standard for e-readers to browse and download books wirelessly without needing a USB cable.

**Independent Test**: Can be fully tested using standard HTTP client tools or an OPDS validator by requesting `/opds`, navigating taxonomy and recent feeds, and downloading an acquisition EPUB stream with valid MIME types.

**Acceptance Scenarios**:
1. **Given** an active xBookLibrary containing books, **When** an OPDS client requests `GET /opds` (or `GET /api/opds/v1.2`), **Then** the server returns an Atom XML feed with `application/atom+xml;profile=opds-catalog;kind=navigation` containing links to "All Books", "Recent Additions", "Authors", "Taxonomies", and OpenSearch description.
2. **Given** an acquisition feed request for a specific library or taxonomy, **When** the client fetches the feed, **Then** each entry includes Dublin Core metadata (`dc:identifier`, `dc:title`, `dc:creator`, `summary`), cover image link (`rel="http://opds-spec.org/image"`), and acquisition download links (`rel="http://opds-spec.org/acquisition"`).
3. **Given** an OPDS 2.0 client requesting `GET /api/opds/v2.0` with `Accept: application/opds+json`, **Then** the server responds with an OPDS 2.0 JSON Catalog format conformant to the Readium/W3C Community Group standard.

---

### User Story 2 - OpenSearch Description & Search Feeds (Priority: P1)

As a reader browsing via an e-reader app, I want to use the in-app search bar to find books by title, author, or keyword directly over OPDS.

**Why this priority**: OPDS search allows users to find books immediately without manually paging through large catalogs.

**Independent Test**: Request `GET /opds/opensearch.xml`, extract the search URL template `GET /opds/search?q={searchTerms}`, and verify that matching books are returned in an Atom acquisition feed.

**Acceptance Scenarios**:
1. **Given** the OPDS root feed, **When** inspecting link relations, **Then** a link with `rel="search"` points to `/opds/opensearch.xml` with `type="application/opensearchdescription+xml"`.
2. **Given** a search query `GET /opds/search?q=quantum`, **When** the server processes the query, **Then** an Atom acquisition feed is returned containing only books matching "quantum" in title, author, or tags.

---

### User Story 3 - Asynchronous Book Format Conversion Engine (Priority: P2)

As a library manager, I have books in legacy or device-specific formats (e.g., MOBI, AZW3, TXT, CBZ) and I want to convert them into modern reflowable EPUB or readable PDF so that they can be rendered in the web reader and on all mobile devices.

**Why this priority**: Format lock-in prevents users from reading older formats in modern web readers; automated conversion integrates multiple formats under the same Calibre book record.

**Independent Test**: Submit a conversion request `POST /api/convert` for a book from MOBI to EPUB, verify that the job processes asynchronously, produces an output EPUB file, and registers it as an additional format in Calibre's `metadata.db`.

**Acceptance Scenarios**:
1. **Given** a book with a MOBI format, **When** requesting conversion to EPUB, **Then** the background conversion service creates an EPUB file, verifies its integrity, adds the format to the book entity, and updates `metadata.db`.
2. **Given** a system with Calibre `ebook-convert` installed, **When** running conversions, **Then** the system uses `ebook-convert` for maximum fidelity; if not installed, it falls back to native Python format conversion utilities.
3. **Given** a comic archive (.cbz), **When** requesting conversion to PDF or EPUB, **Then** the converter extracts pages and compiles a high-resolution, sequentially-ordered document.

---

### User Story 4 - Format Conversion Progress & API Management (Priority: P2)

As a user initiating conversions, I want to monitor active conversion jobs in real-time and cancel or retry failed conversions.

**Why this priority**: Conversions can take from several seconds to a minute depending on book size; transparency prevents duplicate requests.

**Independent Test**: Query `GET /api/jobs/{job_id}` during and after conversion and verify accurate state transitions (`pending` ➔ `running` ➔ `completed` / `failed`).

**Acceptance Scenarios**:
1. **Given** an ongoing conversion job, **When** querying the job status, **Then** the response includes `percent_complete`, `source_format`, `target_format`, and execution logs.
2. **Given** a completed conversion, **When** checking the book details in `/api/books/{id}`, **Then** the new format appears in the `formats` array ready for immediate reading and download.

---

## Technical Architecture & Design Constraints

1. **OPDS Standards Adherence**:
   - **OPDS 1.2**: Atom XML with RFC 4287 syntax, Dublin Core namespaces (`xmlns:dc="http://purl.org/dc/elements/1.1/"`), and OPDS link relations (`rel="http://opds-spec.org/image"`, `rel="http://opds-spec.org/acquisition"`).
   - **OPDS 2.0**: JSON-based navigation and publication feeds compliant with the Readium OPDS 2.0 specification.
   - **OpenSearch 1.1**: OpenSearch Description XML with template-based URL search.
2. **Calibre Storage Integrity**:
   - Converted format files must be written into the existing book folder `<Author>/<Title> (<id>)/<Title> - <Author>.<EXT>` adhering to Calibre naming conventions.
   - Updates must be registered in SQLite `data` table with correct format string and file size.
3. **Zero-Breakage Graceful Degradation**:
   - Conversion engine must check for availability of external CLI tools (`ebook-convert`, `calibre`, `mutool`) and seamlessly fall back to lightweight pure-Python libraries (`pypdf`, `Pillow`, `ebooklib`, `markdown`).

---

## Ratified Design Decisions

1. **OPDS Authentication**:
   - **Default**: Open/unauthenticated on local area networks (LAN) for zero-friction setup with KOReader, Moon+ Reader, and Apple Books.
   - **Security Extension**: Optional HTTP Basic Authentication configurable per library in settings for remote/public WAN deployments.
2. **Format Conversion Engine Architecture**:
   - **Tiered Auto-Detect**: Inspect host `PATH` for Calibre's `ebook-convert` executable at startup. If present, use it for optimal CSS/typography styling fidelity; if absent, gracefully execute native Python converters (`pypdf`, `Pillow`, `markdown`, `docx`) with zero external system dependency requirement.

