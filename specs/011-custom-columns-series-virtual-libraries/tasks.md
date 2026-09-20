# Tasks: 011 Custom Columns, Series Management & Virtual Libraries

**Feature**: 011 Custom Columns, Series Management & Virtual Libraries  
**Branch**: `011-custom-columns-series-virtual-libraries`  
**Status**: Ready  

---

## Phase 1: Data Models & Unit Tests (Priority: P1)
- [x] T001 Define `CustomColumnDatatype`, `CustomColumnDefinition`, `CustomColumnCreateRequest`, `BookCustomValues`, `SeriesInfo`, and `VirtualLibrary` in `backend/domain/custom_columns.py`.
- [x] T002 Implement unit tests `tests/unit/test_custom_columns_domain.py` verifying model validation and preset configurations.

---

## Phase 2: Calibre Storage Services (Priority: P1)
- [x] T003 Implement `CustomColumnsService` in `backend/services/custom_columns_service.py` with dynamic DDL table creation (`custom_columns`, `custom_column_<id>`, and link tables), reading and transactional writing of custom values.
- [x] T004 Implement built-in preset installer (`#read_status`, `#difficulty`, `#rating`, `#pages`) in `CustomColumnsService`.
- [x] T005 Implement `SeriesService` in `backend/services/series_service.py` handling `series`, `books_series_link`, and `books.series_index`.
- [x] T006 Implement `VirtualLibraryService` in `backend/services/virtual_library_service.py` reading/writing Calibre `preferences` table and query filtering.
- [x] T007 Implement unit tests `tests/unit/test_custom_columns_service.py` testing DDL execution, value persistence, series numbering, and query filtering.

---

## Phase 3: API Endpoints & Contract Tests (Priority: P1)
- [x] T008 Implement `backend/api/custom_columns_router.py` exposing custom columns, presets, book custom values, series list, and virtual libraries endpoints.
- [x] T009 Register router in `backend/main.py` and extend book queries to attach custom column values and series info.
- [x] T010 Implement contract tests `tests/contract/test_custom_columns_api.py` testing API lifecycles and Calibre SQLite state.

---

## Phase 4: Frontend Integration & Modern UI (Priority: P2)
- [x] T011 Update TypeScript types in `frontend/src/types/index.ts`.
- [x] T012 Add API methods in `frontend/src/api/client.ts`.
- [x] T013 Update Zustand store `frontend/src/store/useStore.ts` with custom columns, series, and active virtual library state.
- [x] T014 Implement `frontend/src/components/VirtualLibraryBar.tsx` for quick-switching virtual library tabs and creating new ones.
- [x] T015 Update `frontend/src/components/DetailInspector.tsx` with editable series index and custom column fields (#read_status, #rating, #pages).
- [x] T016 Display series badges in `BookCard.tsx` and `BookTable.tsx`.
- [x] T017 Add Series group in `FilterSidebar.tsx`.

---

## Phase 5: Verification & Commit (Priority: P3)
- [x] T018 Run `uv run pytest --cov=backend` to verify all backend tests pass.
- [x] T019 Run `npm run build` in `frontend/` to verify zero TypeScript errors and production bundle.
- [x] T020 Commit Feature 011 to git.
