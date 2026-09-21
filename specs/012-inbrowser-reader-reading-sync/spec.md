# Feature Specification: In-Browser Web Reader & Reading Progress Sync

**Feature Branch**: `012-inbrowser-reader-reading-sync`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "Advanced In-Browser Reader & Cross-Device Reading Sync (Continuous/paged EPUB & PDF, CBZ/CBR comic reader, text highlights & annotations, and automatic progress sync to Calibre #read_status / #pages)"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Immersive EPUB & PDF Reading Experience (Priority: P1)

As a digital library reader, I want to open any EPUB or PDF book directly in my web browser with customized typography, layout modes, and dark/sepia/light themes so that I can enjoy a comfortable and distraction-free reading experience without downloading files or needing external software.

**Why this priority**: Reading is the core value proposition of a digital library. Providing a high-fidelity, customizable reading canvas for the two most dominant book formats (EPUB and PDF) delivers an immediate Minimum Viable Product.

**Independent Test**: Can be fully tested by selecting an EPUB or PDF book from the library catalog, clicking "Read", and verifying font sizing, layout switching (continuous vs. paginated), theme changes (Light, Sepia, Dark, Black), and navigation via table of contents and keyboard shortcuts.

**Acceptance Scenarios**:

1. **Given** a user is browsing an EPUB book, **When** they click "Read Now", **Then** the reader opens instantly displaying the book contents formatted with the user's preferred theme, font size, and layout (paginated or continuous scroll).
2. **Given** an active reading session in an EPUB, **When** the user navigates using arrow keys, page buttons, or Table of Contents chapters, **Then** the viewer navigates smoothly without lag or layout shifting.
3. **Given** a user is viewing a PDF document, **When** they open the PDF reader, **Then** pages render with continuous vertical scroll, zoom controls (fit-to-width, fit-to-page, custom zoom percentage), and page jump navigation.

---

### User Story 2 - Persistent Reading Progress & Calibre Status Synchronization (Priority: P1)

As a reader reading across different laptops, tablets, and phones, I want my exact reading location, progress percentage, and read status to automatically save to the library backend and sync to Calibre custom columns so that I can resume seamlessly from any device and keep my library catalog status up to date.

**Why this priority**: Without cross-device progress synchronization, web reading feels disjointed and ephemeral. Syncing progress directly into Calibre-compatible metadata (`#read_status`, `#pages_read`, or bookmarks) ensures harmony between reading and library management.

**Independent Test**: Can be tested by reading an EPUB or PDF book to 45%, closing the browser, opening the book from another browser or incognito session, and verifying the reader restores to the exact same sentence/page, while the library catalog automatically marks the book as "reading" or "completed" upon reaching 100%.

**Acceptance Scenarios**:

1. **Given** a user reads an EPUB or PDF, **When** they turn pages or scroll, **Then** their exact location (CFI or page number) and progress percentage are saved to the backend within a 2-second debounce.
2. **Given** a book previously closed at 62% progress, **When** the user opens the reader on any device, **Then** the reader automatically navigates to that exact location with a "Resumed from last reading position" notification.
3. **Given** a library configured with `#read_status` and `#pages` custom fields, **When** the reader detects reading activity or completion (>= 98%), **Then** `#read_status` transitions from `unread` to `reading` or `completed`, and estimated pages read are updated.

---

### User Story 3 - Comic & Manga Graphic Reader (CBZ / CBR) (Priority: P2)

As a fan of graphic novels, comics, and manga, I want to read `.cbz` and `.cbr` archives directly in the browser with single-page, dual-page spread, and continuous vertical webtoon scroll modes, plus Right-to-Left manga paging, so that graphic books render authentically according to their artistic medium.

**Why this priority**: Digital libraries contain rich collections of comics and manga. Specialized graphic rendering modes (especially dual-page spreads and Right-to-Left orientation) provide essential support for visual storytelling.

**Independent Test**: Can be tested by opening a CBZ or CBR book, toggling between Left-to-Right, Right-to-Left (Manga), and Vertical Webtoon modes, and verifying high-resolution page rendering and thumbnail strip navigation.

**Acceptance Scenarios**:

1. **Given** a comic archive (CBZ or CBR), **When** opened in the reader, **Then** pages are extracted and displayed seamlessly with crisp resolution and rapid pre-fetching of adjacent pages.
2. **Given** a manga volume, **When** the user toggles "Manga Mode (Right-to-Left)", **Then** pressing the Right Arrow or clicking the left margin advances to the next page in Japanese reading order.
3. **Given** a webtoon or digital comic, **When** "Webtoon Mode (Vertical Continuous)" is enabled, **Then** all pages stack vertically with zero seam margins for continuous scrolling.

---

### User Story 4 - Highlights, Annotations & Bookmarks Studio (Priority: P2)

As a researcher, student, or active reader, I want to highlight text passages in multiple colors, attach personal notes, and bookmark key chapters, with an inspector panel listing all my annotations so that I can review and export my findings.

**Why this priority**: Highlighting and note-taking transform passive reading into active knowledge acquisition, directly complementing the library's summarization and synthesis capabilities.

**Independent Test**: Can be tested by selecting a passage of text in the reader, applying a yellow highlight with an attached note, viewing the highlight appear in the reader sidebar, clicking it to jump back to the location, and exporting notes to Markdown.

**Acceptance Scenarios**:

1. **Given** highlighted text selected by a user, **When** a color palette option (yellow, green, blue, pink, purple) is chosen, **Then** the highlight persists across sessions and browser refreshes.
2. **Given** an existing highlight, **When** the user adds an annotation comment, **Then** a note badge appears in the margin and the note is accessible from the "Highlights & Notes" drawer.
3. **Given** multiple annotations across a book, **When** the user clicks "Export Notes", **Then** a cleanly formatted Markdown summary with book title, author, chapter citations, and user thoughts is generated for download or copying.

---

### User Story 5 - In-Reader Contextual AI Assistant (Priority: P3)

As an inquisitive reader, I want to select unfamiliar words, historical references, or complex passages while reading and ask the AI assistant to define, explain, or summarize them in context without breaking my reading flow.

**Why this priority**: Integrated AI contextual lookup elevates the reading experience beyond static viewers, letting readers comprehend difficult literature and technical papers instantly.

**Independent Test**: Can be tested by selecting a complex paragraph in an EPUB/PDF, clicking the "Ask AI" floating pill, and verifying an instant contextual explanation grounded in the surrounding chapter.

**Acceptance Scenarios**:

1. **Given** highlighted or selected text in the reader, **When** the user clicks "Explain Concept", **Then** a compact floating card displays an explanation tailored to the surrounding narrative or technical context.
2. **Given** an unfamiliar foreign phrase or idiom, **When** the user selects "Translate & Clarify", **Then** the translated phrase with linguistic nuance is displayed.

---

### Edge Cases

- **Corrupt or DRM-locked EPUB/PDF files**: The reader MUST display a helpful, user-friendly notification indicating that the book cannot be rendered in-browser, offering an external download link.
- **Very large comic archives (500MB+ CBZ/CBR)**: The backend MUST stream and cache extracted page images progressively on demand rather than unpacking the entire archive into memory at once.
- **Offline / Disconnected Reading**: If the network connection drops while reading, progress updates MUST queue locally in browser storage and sync back to the server once connectivity is restored.
- **Font size extremes**: Layout MUST remain responsive and legible at maximum (32px+) and minimum (12px) font settings without cutting off text or overlapping navigation buttons.
- **EPUB with non-standard internal CSS**: User-chosen reader themes (Dark, Sepia, Font size) MUST take precedence over hardcoded publisher inline styles that could cause white-on-white unreadable text.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render EPUB books in-browser supporting both paginated spread mode and continuous vertical scroll mode.
- **FR-002**: The reader MUST provide customizable typography and visual themes: Light, Sepia, Dark, and OLED Black, with adjustable font families (system serif, sans-serif, OpenDyslexic), font sizes (12px to 32px), line height, and margin width.
- **FR-003**: The system MUST render PDF documents with continuous vertical scrolling, zoom controls (fit-to-width, fit-to-height, 50%-300%), and direct page jump navigation.
- **FR-004**: The system MUST support reading comic and manga archives (`.cbz` and `.cbr`), providing single-page, dual-page spread, Right-to-Left (Manga order), and vertical webtoon continuous scroll modes.
- **FR-005**: The reader MUST track exact reading position (EPUB CFI, PDF page number, comic image index) and calculate reading percentage completed (0% to 100%).
- **FR-006**: The system MUST persist reading progress to the backend server with a 2-second debounce, ensuring cross-device and cross-session resumption from the exact last reading point.
- **FR-007**: When reading progress is recorded, the system MUST automatically synchronize the book's status in the library catalog (transitioning `#read_status` to `reading` upon first reading, and `completed` when progress exceeds 98%).
- **FR-008**: The reader MUST support text selection highlights in at least 5 distinct colors (yellow, green, blue, pink, purple) with optional attached text notes.
- **FR-009**: The reader MUST provide a slide-out navigation panel containing: (a) interactive Table of Contents, (b) Bookmarks list, (c) Highlights and Annotations manager with search and filter capabilities.
- **FR-010**: The user MUST be able to export all bookmarks, highlights, and annotations for a book to standard Markdown format.
- **FR-011**: The reader MUST provide an in-reader AI helper popup for selected text offering instant actions: "Explain in Context", "Summarize Selection", and "Define Vocabulary".
- **FR-012**: The reader interface MUST support keyboard shortcuts (Left/Right arrow keys for page turns, Spacebar for advance, F for fullscreen toggle, Esc for exit).

---

### Key Entities *(include if feature involves data)*

- **ReadingProgress**: Represents a user's current reading position in a specific book.
  - *Attributes*: `book_id`, `format` (EPUB, PDF, CBZ), `location` (CFI string or page number), `progress_percent` (0.0 to 100.0), `last_read_at`, `total_reading_seconds`.
- **Annotation**: Represents a user-created highlight or note anchored to a book location.
  - *Attributes*: `id`, `book_id`, `format`, `location` (CFI or page number), `selected_text`, `color` (yellow, green, blue, pink, purple), `note_text`, `chapter_title`, `created_at`, `updated_at`.
- **Bookmark**: Represents a saved bookmarker tag.
  - *Attributes*: `id`, `book_id`, `location`, `title`, `created_at`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Reader opens any standard EPUB or PDF book and renders the first page in under 1.5 seconds.
- **SC-002**: Reading progress updates sync to the backend reliably with 100% location accuracy upon browser reload or switching to another device.
- **SC-003**: 100% of user highlights and annotations persist across reading sessions and correctly navigate the user back to the anchored passage when clicked.
- **SC-004**: Comic/Manga reader smoothly loads adjacent pages with pre-fetching so that page transitions feel instantaneous (< 200ms).
- **SC-005**: Automatic sync updates the book's `#read_status` custom column without requiring manual catalog editing.
- **SC-006**: Full keyboard accessibility: 100% of primary reading actions (next page, previous page, fullscreen, toggle sidebar) are operable via standard keyboard shortcuts.

---

## Assumptions

- Users access the web reader through modern web browsers supporting Web Standards, HTML5 Canvas, and modern CSS.
- For comic archives, `.cbz` (ZIP) and `.cbr` (RAR) files contain standard web-compatible images (JPEG, PNG, WebP).
- Calibre libraries may or may not have pre-created custom columns; if `#read_status` is present, the system updates it; if not present, reading progress is still safely stored in the library's reading progress table without error.
- Text selection and highlighting in PDFs rely on embedded text layers in the PDF document (scanned image-only PDFs without OCR support page bookmarks, while OCRed PDFs support full text selection).
