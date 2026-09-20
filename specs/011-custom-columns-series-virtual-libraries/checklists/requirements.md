# Requirements Checklist: 011 Custom Columns, Series Management & Virtual Libraries

- [x] **Requirement 1: Calibre 7.x Custom Columns Core Schema**
  - [x] Query existing custom columns from `custom_columns` table.
  - [x] Create new custom columns with auto-generated `custom_column_<id>` (and `books_custom_column_<id>_link` for normalized types).
  - [x] Support standard Calibre datatypes: `enumeration`, `int`, `float`, `bool`, `text`, `comments`, `series`, `rating`.

- [x] **Requirement 2: Custom Values Reading and Writing**
  - [x] Read custom values when fetching books for a library.
  - [x] Write/update custom values transactionally per book.
  - [x] Provide 1-click built-in presets: `#read_status` (Unread, Reading, Completed, Abandoned), `#difficulty` (Introductory, Intermediate, Advanced), `#rating`, and `#pages`.

- [x] **Requirement 3: First-Class Series Management**
  - [x] Maintain Calibre `series` table and `books_series_link`.
  - [x] Support decimal series indexing (`series_index` e.g. 1.0, 2.5).
  - [x] Support filtering books by series in UI and API.

- [x] **Requirement 4: Calibre Preferences Virtual Libraries**
  - [x] Read/write virtual library definitions to `preferences` table (`virtual_libraries` JSON string).
  - [x] Filter books dynamically by virtual library search expression.
  - [x] Allow creating, editing, and deleting virtual libraries via API and UI.

- [x] **Requirement 5: Modern UI Integration**
  - [x] Tab bar above the book grid/table for switching Virtual Libraries with "+ New Virtual Library" button.
  - [x] Custom column inputs in `DetailInspector` (dropdown for `#read_status`, number input for `#pages`, rating stars for `#rating`).
  - [x] Series badge display in `BookCard` and `BookTable`.
  - [x] Series category hierarchy in `FilterSidebar`.
