# Feature Specification: 011 Custom Columns, Series Management & Virtual Libraries

**Feature**: 011 Custom Columns, Series Management & Virtual Libraries  
**Branch**: `011-custom-columns-series-virtual-libraries`  
**Status**: In Development  
**Standard**: Calibre 7.x SQLite Schema Parity & Spec-Kit  

---

## 1. Executive Summary

Feature 011 delivers three essential catalog organization capabilities to `xBookLibrary`:
1. **Calibre 7.x Custom Columns**: Dynamic schema creation and data editing for user-defined metadata columns (e.g. `#read_status`, `#difficulty`, `#rating`, `#pages_read`, `#notes`, `#owned_format`), maintaining 100% bidirectional SQLite table compatibility with desktop Calibre (`custom_columns`, `custom_column_<id>`, and `books_custom_column_<id>_link`).
2. **Series & Universe Management**: First-class tracking of book series, sagas, and reading orders with decimal sequence indexing (e.g. *Foundation #1*, *Dune #0.5*), series browsing, and auto-grouping.
3. **Virtual Libraries**: Dynamic, saved library subsets defined by search queries stored directly in Calibre's `preferences` table (`virtual_libraries` key), rendered as interactive quick-switch tabs with real-time book count badges.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: User-Defined Custom Metadata Columns (Priority: P1)
- **As a** reader or researcher with a personal classification system,
- **I want to** define and populate custom fields like `#read_status` (Unread, Reading, Read, Abandoned), `#pages`, or `#difficulty`,
- **So that** I can track personalized metadata that persists safely within Calibre's native database.

#### Acceptance Criteria:
1. `GET /api/libraries/{lib_id}/custom-columns` lists all active custom columns with label, name, datatype, and configuration.
2. `POST /api/libraries/{lib_id}/custom-columns` creates a new custom column, auto-generating the corresponding `custom_column_<id>` table (and link table for normalized types).
3. `PUT /api/books/{book_id}/custom-values` updates custom column values for a specific book.
4. Pre-packaged standard presets can be added with 1-click:
   - `#read_status` (Enumeration: Unread, Reading, Completed, Abandoned)
   - `#rating` (Rating: 1-5 stars)
   - `#pages` (Integer: Page count)
   - `#notes` (Comments: Markdown / Rich text notes)
5. Custom column values are returned alongside standard book metadata in `/api/books` and editable in `DetailInspector`.

---

### User Story 2: Series & Universe Management (Priority: P1)
- **As a** fiction or technical book collector,
- **I want to** organize books into chronological or narrative series with fractional volume indices (e.g. `#1`, `#2`, `#2.5`),
- **So that** I can read books in their intended sequence and group related volumes together.

#### Acceptance Criteria:
1. Books can be associated with a series name and a series index (float, default 1.0).
2. Updates synchronize cleanly with Calibre's `series` and `books_series_link` tables.
3. The UI displays series badges (e.g. `Foundation #2`) in grid cards, table views, and detail inspector.
4. The sidebar filter tree includes a "Series" taxonomy hierarchy with book counts.

---

### User Story 3: Virtual Libraries & Dynamic Filter Tabs (Priority: P1)
- **As a** reader with a large library (1,000+ books),
- **I want to** create and switch between Virtual Libraries (e.g. "Unread AI Research", "Sci-Fi Hugo Winners", "To Read"),
- **So that** I can focus on specific subsets without losing the global library context.

#### Acceptance Criteria:
1. `GET /api/libraries/{lib_id}/virtual-libraries` returns all saved virtual library configurations from the Calibre `preferences` table.
2. `POST /api/libraries/{lib_id}/virtual-libraries` creates or updates a virtual library with a name and a search expression.
3. `DELETE /api/libraries/{lib_id}/virtual-libraries/{name}` removes the virtual library.
4. Virtual Libraries render as quick-switch tabs above the book view.
5. Selecting a tab filters books in real-time according to its search expression.

---

## 3. Calibre 7.x Database Schema Integration

### 3.1 Custom Columns Schema
In Calibre SQLite:
- `custom_columns`:
  ```sql
  CREATE TABLE IF NOT EXISTS custom_columns (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      label TEXT NOT NULL UNIQUE,
      name TEXT NOT NULL,
      datatype TEXT NOT NULL,
      mark_for_delete INTEGER DEFAULT 0,
      editable INTEGER DEFAULT 1,
      display TEXT DEFAULT '{}',
      is_multiple INTEGER DEFAULT 0,
      normalized INTEGER DEFAULT 0
  );
  ```
- Denormalized table (`datatype IN ('int', 'float', 'bool', 'text', 'comments', 'datetime')` and `normalized = 0`):
  ```sql
  CREATE TABLE IF NOT EXISTS custom_column_<id> (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      book INTEGER NOT NULL UNIQUE,
      value <SQL_TYPE>
  );
  ```
- Normalized table (`datatype IN ('enumeration', 'series')` or `is_multiple = 1`):
  ```sql
  CREATE TABLE IF NOT EXISTS custom_column_<id> (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      value TEXT NOT NULL UNIQUE
  );
  CREATE TABLE IF NOT EXISTS books_custom_column_<id>_link (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      book INTEGER NOT NULL,
      value INTEGER NOT NULL,
      extra REAL
  );
  ```

### 3.2 Series Schema
Calibre tables used:
- `series`: `(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, sort TEXT)`
- `books_series_link`: `(id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL UNIQUE, series INTEGER NOT NULL)`
- Calibre book table column: `series_index REAL DEFAULT 1.0`

### 3.3 Virtual Libraries Storage
Stored in `preferences` table:
```sql
INSERT OR REPLACE INTO preferences (val, key) VALUES (?, 'virtual_libraries');
```
Where `val` is a JSON-serialized dictionary mapping virtual library name to search expression (e.g. `{"Unread Sci-Fi": "tags:\"Science Fiction\" and not #read_status:Completed"}`).
