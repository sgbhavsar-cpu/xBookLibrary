# Research & Architecture Decisions: 011 Custom Columns, Series & Virtual Libraries

## 1. Calibre Custom Column Architecture
Calibre uses a metadata-driven approach where every custom column has an entry in `custom_columns`:
- `label`: Starts with `#` internally or has leading `#` prepended when queried by user (e.g. `read_status` maps to `#read_status`).
- `datatype`:
  - `enumeration`: Options stored in `display` JSON: `{"enum_values": ["Unread", "Reading", "Completed", "Abandoned"]}`.
    Uses normalized tables `custom_column_<id>` (stores distinct string options) + `books_custom_column_<id>_link (book, value)`.
  - `int`: 64-bit integer, denormalized `custom_column_<id> (book, value)`.
  - `float`: IEEE floating point, denormalized.
  - `bool`: 0 or 1 integer, denormalized.
  - `text`: Single text line.
  - `comments`: Long markdown/HTML text.
  - `rating`: Integer (1 to 5, halved as 2 to 10 in Calibre internal representations, or standard 1-5).
  - `series`: Series title with `extra` column in link table for series index.

## 2. Virtual Libraries & Query Syntax
Calibre stores Virtual Libraries as a JSON dictionary in the `preferences` table with key `virtual_libraries`:
```json
{
  "Unread Tech": "tags:\"Computer Science\" and not #read_status:Completed",
  "Foundation Saga": "series:\"Foundation\""
}
```
Query Evaluation:
- Query parser evaluates simple token conditions:
  - `tags:"..."` or `tag:...`
  - `author:"..."` or `authors:...`
  - `series:"..."`
  - `#<custom_column>:...`
  - `not ...`, `and ...`, `or ...`
- If no field prefix is specified, falls back to text search against title, authors, and comments.

## 3. Series Schema Compatibility
In standard Calibre `metadata.db`:
- `series` table contains `(id INTEGER PRIMARY KEY, name TEXT UNIQUE, sort TEXT)`.
- `books_series_link` contains `(id INTEGER PRIMARY KEY, book INTEGER UNIQUE, series INTEGER)`.
- `books` table contains `series_index REAL DEFAULT 1.0`.
This allows a book to belong to a series with a specific volume number (e.g. `Isaac Asimov - Foundation (1.0)`).
When a series name is edited, the `series` table and link table are updated transactionally.
