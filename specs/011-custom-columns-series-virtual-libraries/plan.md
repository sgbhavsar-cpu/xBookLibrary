# Implementation Plan: 011 Custom Columns, Series & Virtual Libraries

## Phase 1: Custom Columns & Series Domain Models (TDD)
1. `backend/domain/custom_columns.py`: Define `CustomColumnDefinition`, `CustomColumnCreateRequest`, `BookCustomValues`, `SeriesInfo`, `VirtualLibrary`.
2. `tests/unit/test_custom_columns_domain.py`: Unit tests for model validation, serialization, and preset definitions.

## Phase 2: Calibre Storage Manager for Custom Columns & Series
1. `backend/services/custom_columns_service.py`:
   - `get_custom_columns(library_id)`: Read from `custom_columns`.
   - `create_custom_column(...)`: Insert into `custom_columns` and execute DDL to create `custom_column_<id>` (and link table if normalized).
   - `install_default_presets(library_id)`: Setup `#read_status`, `#difficulty`, `#rating`, `#pages`.
   - `get_book_custom_values(library_id, book_id)`: Read denormalized and normalized values.
   - `set_book_custom_values(library_id, book_id, values)`: Write/update custom tables transactionally.
2. `backend/services/series_service.py`:
   - `get_series_list(library_id)`: Return distinct series and book counts.
   - `set_book_series(library_id, book_id, series_name, series_index)`: Upsert into `series`, `books_series_link`, and update `books.series_index`.
3. `backend/services/virtual_library_service.py`:
   - `get_virtual_libraries(library_id)`: Read `preferences` key `virtual_libraries`.
   - `save_virtual_library(library_id, name, query)`: Update `preferences`.
   - `delete_virtual_library(library_id, name)`.
   - `evaluate_query(query, books)`: Filter books in Python using query tokens (`tags:...`, `series:...`, `#read_status:...`, text).
4. `tests/unit/test_custom_columns_service.py`: Unit tests against in-memory Calibre SQLite database.

## Phase 3: API Routers & Contract Tests
1. `backend/api/custom_columns_router.py`: Expose custom columns, presets, series, and virtual libraries endpoints.
2. Register router in `backend/main.py`.
3. `tests/contract/test_custom_columns_api.py`: Contract tests verifying all endpoints and Calibre schema modifications.

## Phase 4: Frontend Integration
1. Types in `frontend/src/types/index.ts`: `CustomColumnDefinition`, `VirtualLibrary`, `SeriesInfo`.
2. API client in `frontend/src/api/client.ts`.
3. Zustand store `useStore.ts`: Active virtual library tab, custom columns cache, series list.
4. UI Components:
   - `frontend/src/components/VirtualLibraryBar.tsx`: Dynamic tabs with "+ New Virtual Library" dialog.
   - `frontend/src/components/DetailInspector.tsx`: Custom fields editor (read status dropdown, pages, rating) and series volume input.
   - `frontend/src/components/BookCard.tsx` & `BookTable.tsx`: Display series badges (e.g. `Foundation #1.0`).
   - `frontend/src/components/FilterSidebar.tsx`: Series tree group.

## Phase 5: Verification & Commit
1. Run backend pytest suite with coverage.
2. Run `npm run build` in `frontend/`.
3. Commit Feature 011 to git.
