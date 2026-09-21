# Research: In-Browser Web Reader & Reading Progress Sync

## 1. EPUB Rendering & CFI Tracking (epub.js)
- **epub.js v0.3.93+**: Already included in `frontend/package.json`.
- Flow options: `flow: 'paginated'` vs `flow: 'scrolled-doc'`.
- Progress tracking: `book.locations.generate(1024)` allows calculating percentage from CFI (`book.locations.percentageFromCfi(cfi)`).
- Selection & Highlighting: epub.js rendition supports `rendition.on('selected', (cfiRange, contents) => ...)` and `rendition.annotations.add('highlight', cfiRange, {}, (e) => ..., 'hl-class', { fill: color })`.
- Annotations can be re-rendered when loading the book via `rendition.annotations.add(...)`.

## 2. Comic & Manga Streaming (CBZ / CBR)
- CBZ files are standard ZIP archives containing image files (`.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`).
- Python standard library `zipfile` handles `.cbz` streaming without third-party dependencies.
- Images inside CBZ should be naturally sorted: `sort(key=natural_keys)` to prevent `page_10.jpg` coming before `page_2.jpg`.
- Webtoon mode: continuous vertical scroll with flex-column, images rendered at full width with `object-fit: contain`.
- Manga mode: Right-to-Left paging (`direction: rtl` or navigation flipping Next ➔ Left, Prev ➔ Right).

## 3. PDF In-Browser Viewing
- PDF files can be served with partial content byte ranges (`Accept-Ranges: bytes`) for smooth streaming.
- Standard HTML5 iframe / object with `#toolbar=0&navpanes=0&page={n}` works cross-platform.
- For interactive highlights and exact progress on PDFs, an overlaid page tracking bar with page jump and zoom controls provides a seamless experience.

## 4. Reading Progress & Calibre Custom Column Parity
- Tables in `metadata.db`:
  - `reading_progress (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER, format TEXT, location TEXT, progress_percent REAL, total_seconds INTEGER, last_read_at TIMESTAMP, UNIQUE(book_id, format))`
  - `annotations (id TEXT PRIMARY KEY, book_id INTEGER, format TEXT, location TEXT, selected_text TEXT, color TEXT, note_text TEXT, chapter_title TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)`
  - `bookmarks (id TEXT PRIMARY KEY, book_id INTEGER, format TEXT, location TEXT, title TEXT, created_at TIMESTAMP)`
- When progress updates:
  - If `#read_status` exists in `custom_columns`:
    - `progress_percent == 0`: `'unread'`
    - `0 < progress_percent < 98`: `'reading'`
    - `progress_percent >= 98`: `'completed'`
  - Transactional update via `CustomColumnsService.set_custom_column_values`.
