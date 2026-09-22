# Feature Specification: Core Library Operations, In-Place Metadata Editor & Multi-Format Ingestion

**Feature Branch**: `015-core-metadata-editor-and-import`  
**Created**: 2026-09-22  
**Status**: Draft  
**Input**: User description: "focus on basic usage as books library, import files, in place editing of information, get book metadata etc on priority. First update the documentation as per github speckit and planning before development."

---

## 1. Executive Summary & Problem Statement

While `xBookLibrary` features sophisticated AI capabilities (vector RAG Q&A, Whisper transcription, dual-taxonomy classification, multi-book document synthesis), core library operations—the bread and butter of desktop Calibre—currently lack user-facing depth:
1. **Metadata Editing**: Users cannot manually edit standard book attributes (Title, Authors, Sort Names, Publisher, Publication Date, Rating, Tags, Series, Identifiers, Comments) through an in-place modal or form.
2. **Online Metadata Fetching**: Users cannot interactively search online providers (Google Books, OpenLibrary, CrossRef) by title, author, or ISBN, preview candidate matches with covers, and selectively apply them.
3. **Multi-Format Attachment & Deletion**: Users cannot attach an additional format file (e.g. adding a PDF to an existing EPUB entry) or delete a specific format directly from the UI.
4. **Bulk Metadata Editing**: Users cannot multi-select books in the catalog and batch-update tags, authors, publishers, or auto-increment series indices.
5. **Drag-and-Drop Ingestion**: The file upload experience lacks intuitive drag-and-drop dropzones across the main window and conflict handling (merge, replace, or skip).

Feature 015 delivers full Calibre parity for all day-to-day library operations, editing workflows, and file management.

---

## 2. User Scenarios & Testing *(Prioritized)*

### User Story 1: Comprehensive Single-Book Metadata Editor (Priority: P1)
**As a** library curator,  
**I want to** open an "Edit Metadata" modal for any selected book to manually review and edit all Calibre fields, identifiers, descriptions, and cover art,  
**So that** my book catalog is organized and accurate according to my personal preferences.

**Why this priority**: Essential core functionality of any library manager. Without manual editing, users are blocked from fixing typos or correcting inaccurate imported metadata.

**Independent Test**:
- Select a book, press `E` or click "Edit Metadata" in the Detail Inspector.
- Change Title, Authors, Series, Publisher, and Tags.
- Paste a new cover image from the clipboard or upload a file.
- Click "Save Changes".
- Verify that `metadata.db`, `metadata.opf`, and all UI components immediately reflect the updated metadata.

**Acceptance Scenarios**:
1. **Given** a selected book in the catalog grid or table, **When** the user clicks "Edit Metadata" or presses the `E` key, **Then** the Edit Metadata modal opens pre-filled with the book's current title, authors, sort keys, publisher, pubdate, rating, series, tags, identifiers, comments, and cover art.
2. **Given** the Edit Metadata modal is open, **When** the user modifies authors to `"Frank Herbert"`, series to `"Dune Chronicles"`, and series index to `1.5`, **Then** the system automatically updates `books`, `authors`, `books_authors_link`, `series`, and `books_series_link` upon saving.
3. **Given** the Edit Metadata modal is open, **When** the user pastes an image from the clipboard (Ctrl+V) or drops an image into the cover area, **Then** a preview is displayed, and saving replaces `cover.jpg` on disk and regenerates thumbnail caches.

---

### User Story 2: Interactive Online Metadata & Cover Fetching (Priority: P1)
**As a** reader with newly imported raw e-books,  
**I want to** search online databases (Google Books, OpenLibrary, CrossRef) by Title, Author, or ISBN from within the editor,  
**So that** I can retrieve official publisher metadata, book descriptions, and high-resolution cover art without manual typing.

**Why this priority**: Saves immense time when ingesting raw e-books that have missing, incomplete, or corrupted metadata.

**Independent Test**:
- Open the metadata editor for a book with only a title (e.g. "Foundation").
- Click "Fetch Online Metadata".
- Review the list of search candidates returned from Google Books and OpenLibrary.
- Select the best candidate, choose which fields to overwrite, and click "Apply".
- Verify the book's description, publication date, ISBN, and cover are populated.

**Acceptance Scenarios**:
1. **Given** the Edit Metadata modal is open, **When** the user clicks "Download Metadata", **Then** the system queries online providers using the book's current title, author, and/or ISBN, returning a list of ranked candidate cards with thumbnails, title, authors, publisher, and year.
2. **Given** a list of candidate results, **When** the user clicks a candidate, **Then** a side-by-side comparison view displays current vs. new values.
3. **Given** a selected candidate, **When** the user clicks "Apply Metadata", **Then** the chosen fields and high-resolution cover art are copied into the editor form for confirmation.

---

### User Story 3: Multi-Format Attachment & Deletion (Priority: P2)
**As a** multi-device reader,  
**I want to** add additional formats (e.g., adding a PDF or MOBI to an existing EPUB book record) or delete unneeded formats,  
**So that** each book in my library acts as a container for all of its format variations.

**Why this priority**: Prevents duplicate book entries when the user owns a title in multiple formats (e.g., EPUB for Kobo, PDF for tablet, MP3 for audio).

**Independent Test**:
- Inspect an existing book that only has an EPUB format.
- In the Formats section of the Detail Inspector, click "+ Add Format" and select a PDF file.
- Verify the PDF is ingested into the existing book's folder, registered in the `data` table, and immediately available for reading or export.
- Click the trash icon next to an obsolete format and confirm deletion. Verify the file is deleted from disk and removed from the `data` table.

**Acceptance Scenarios**:
1. **Given** an existing book record, **When** the user uploads or drops an additional format file onto the book's inspector, **Then** the system stores the file in `library/{author}/{title}/` and inserts a new record into `data` with `format = 'PDF'` and `book = book_id`.
2. **Given** a book with multiple formats, **When** the user clicks "Delete Format" on `MOBI`, **Then** a confirmation prompt appears; upon confirming, the file is safely deleted from disk and the `data` row is removed without deleting the book record itself.

---

### User Story 4: Bulk Multi-Book Metadata Editor (Priority: P2)
**As a** power user organizing a large library,  
**I want to** select multiple books and edit shared metadata in bulk,  
**So that** I can clean up tags, author names, publishers, or re-index entire book series with one operation.

**Why this priority**: Essential for library maintenance when adding series or mass-tagging imported files.

**Independent Test**:
- Select 5 books using checkbox selection or Shift+Click in Table View.
- Click "Bulk Edit (5)" in the action bar.
- Add tag `"Cyberpunk"`, set Publisher to `"Ace Books"`, and set Series to `"Sprawl"` with "Auto-number series index".
- Click "Apply to 5 Books".
- Verify all 5 books have been updated with sequential series indices (`1.0, 2.0, 3.0, 4.0, 5.0`) and shared tags.

**Acceptance Scenarios**:
1. **Given** multiple books selected in the catalog, **When** the user clicks "Bulk Edit", **Then** the Bulk Edit modal displays options to add/remove tags, set author, set publisher, set rating, and configure series auto-numbering.
2. **Given** the Bulk Edit modal, **When** the user specifies tags to add and tags to remove, **Then** only those specified tags are modified, leaving other book-specific tags intact.

---

### User Story 5: Streamlined Drag-and-Drop Ingestion with Conflict Handling (Priority: P3)
**As a** user importing new files,  
**I want to** drag and drop files anywhere onto the application window, with conflict prompts when duplicates are detected,  
**So that** I can import books effortlessly without accidental duplicate records.

**Why this priority**: Modern desktop-grade user experience for fast onboarding of book collections.

**Acceptance Scenarios**:
1. **Given** the library window is open, **When** files or folders are dragged over the window, **Then** a visual dropzone overlay appears with format detection badges.
2. **Given** a dropped file matches an existing title and author in the library, **When** ingestion occurs, **Then** the system prompts: "Book already exists: [Merge new format into existing book] [Create new separate book] [Skip]".

---

## 3. Functional Requirements

### Metadata & In-Place Editing
- **FR-001**: The system MUST provide an "Edit Metadata" modal for individual books covering:
  - Title, Title Sort (auto-computed via configurable articles `a`, `an`, `the`).
  - Authors (ordered list with corresponding Author Sort keys).
  - Series name and decimal series index (`series_index` float).
  - Publisher, Publication Date (`pubdate` ISO timestamp).
  - Rating (integer `0-10`, displayed as 0-5 stars with half-star increments).
  - Tags (comma-separated or chips, auto-linked to `tags` and `books_tags_link`).
  - Identifiers (key-value dictionary: `isbn`, `doi`, `google`, `openlibrary`, `asin`).
  - Comments / Description (rich text editor with Markdown and HTML preview).
  - Custom Columns (editable inputs for all user-defined columns, including `#read_status`, `#pages`, `#difficulty`).
- **FR-002**: The system MUST support cover art replacement via:
  - Local file picker (`.jpg`, `.png`, `.webp`).
  - Clipboard image paste (listening to `paste` event on the modal).
  - Drag-and-drop onto the cover box.
  - Reset to generated SVG cover.
- **FR-003**: Upon saving metadata edits, the system MUST:
  - Update `books`, `authors`, `tags`, `series`, `identifiers`, `comments`, and `data` tables in SQLite `metadata.db`.
  - Rewrite `metadata.opf` on disk to ensure 100% Calibre portable library compliance.
  - Trigger a UI state refresh across all open catalog views and detail panes.

### Online Metadata & Cover Search
- **FR-004**: The system MUST provide an interactive online metadata search endpoint (`GET /api/books/{book_id}/online-metadata/search` or `POST /api/online-metadata/query`).
- **FR-005**: Search queries MUST search across registered providers (Google Books API, OpenLibrary REST API, CrossRef API).
- **FR-006**: The system MUST return candidate matches with confidence score, source provider, title, authors, publisher, publication date, description, ISBN, and cover thumbnail URL.
- **FR-007**: The UI MUST allow selective field transfer (e.g. user can choose to adopt description and cover while preserving their original title/tags).

### Multi-Format Management
- **FR-008**: The system MUST provide `POST /api/books/{book_id}/formats` to upload and attach a new format file to an existing book.
- **FR-009**: The system MUST provide `DELETE /api/books/{book_id}/formats/{format}` to safely delete a format file from disk and remove its row in the `data` table.
- **FR-010**: The Detail Inspector MUST display actionable format chips with direct Download, Read, and Delete actions.

### Bulk Operations & Multi-Select
- **FR-011**: The catalog UI (both Grid and Table views) MUST support multi-selection via checkboxes, Ctrl+Click, and Shift+Click.
- **FR-012**: A floating bulk action bar MUST appear when $\ge 1$ book is selected, displaying total count, "Bulk Edit", and "Delete".
- **FR-013**: The bulk edit endpoint (`POST /api/books/bulk-update`) MUST accept:
  - `book_ids`: List of target book IDs.
  - `add_tags`: Tags to add to all selected books.
  - `remove_tags`: Tags to remove from all selected books.
  - `set_author`: Optional author to set.
  - `set_publisher`: Optional publisher to set.
  - `set_rating`: Optional rating to apply.
  - `set_series`: Optional series name.
  - `auto_number_series`: Boolean flag to assign sequential indices `1.0, 2.0, 3.0...` based on selection order.
  - `custom_values`: Key-value updates for custom columns.

---

## 4. Success Criteria

- **SC-001**: Users can open the Edit Metadata modal on any book in $< 200\text{ ms}$, edit any attribute, and save changes with immediate Calibre `metadata.db` and OPF synchronization.
- **SC-002**: Users can fetch online metadata for any standard book in $< 2\text{ s}$, inspect matches, and apply full metadata and cover art with 1 click.
- **SC-003**: Users can attach an additional format (e.g., adding a PDF to an EPUB) or delete a format without corrupting database links or file structures.
- **SC-004**: Users can select 50 books and batch-update tags, series, or author attributes in $< 500\text{ ms}$.
- **SC-005**: 100% backward and forward compatibility with standard Calibre installations: libraries modified by `xBookLibrary` can be opened in Calibre Desktop with zero errors or schema drift.
- **SC-006**: Full automated test coverage with contract, integration, and Playwright end-to-end UI validation.
