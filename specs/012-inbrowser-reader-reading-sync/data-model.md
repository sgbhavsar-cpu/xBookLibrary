# Data Model: In-Browser Web Reader & Reading Progress Sync

## Database Schema Extensions (`metadata.db`)

```sql
CREATE TABLE IF NOT EXISTS reading_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    format TEXT NOT NULL,
    location TEXT NOT NULL,
    progress_percent REAL NOT NULL DEFAULT 0.0,
    total_seconds INTEGER NOT NULL DEFAULT 0,
    last_read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id, format)
);

CREATE TABLE IF NOT EXISTS annotations (
    id TEXT PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    format TEXT NOT NULL,
    location TEXT NOT NULL,
    selected_text TEXT NOT NULL,
    color TEXT NOT NULL DEFAULT 'yellow',
    note_text TEXT,
    chapter_title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id TEXT PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    format TEXT NOT NULL,
    location TEXT NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Domain Models (`backend/domain/reading.py`)

- `ReadingProgress`:
  - `book_id: int`
  - `format: str`
  - `location: str` (CFI for EPUB, page index for PDF/CBZ)
  - `progress_percent: float`
  - `total_seconds: int = 0`
  - `last_read_at: Optional[datetime] = None`
- `Annotation`:
  - `id: str`
  - `book_id: int`
  - `format: str`
  - `location: str`
  - `selected_text: str`
  - `color: str` (yellow, green, blue, pink, purple)
  - `note_text: Optional[str] = None`
  - `chapter_title: Optional[str] = None`
  - `created_at: Optional[datetime] = None`
  - `updated_at: Optional[datetime] = None`
- `Bookmark`:
  - `id: str`
  - `book_id: int`
  - `format: str`
  - `location: str`
  - `title: str`
  - `created_at: Optional[datetime] = None`
- `ComicPageInfo`:
  - `index: int`
  - `filename: str`
  - `url: str`
- `ComicManifest`:
  - `book_id: int`
  - `total_pages: int`
  - `pages: list[ComicPageInfo]`
  - `series_name: Optional[str] = None`
  - `issue_number: Optional[float] = None`
