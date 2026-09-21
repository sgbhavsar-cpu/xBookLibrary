# Tasks: 012 In-Browser Web Reader & Reading Progress Sync

**Feature**: 012 In-Browser Web Reader & Reading Progress Sync  
**Branch**: `012-inbrowser-reader-reading-sync`  
**Status**: Ready  

---

## Phase 1: Domain Models & Unit Tests (Priority: P1)
- [x] T001 Define `ReadingProgress`, `ReadingProgressCreateRequest`, `Annotation`, `AnnotationCreateRequest`, `Bookmark`, `BookmarkCreateRequest`, `ComicPageInfo`, and `ComicManifest` in `backend/domain/reading.py`.
- [x] T002 Implement unit tests in `tests/unit/test_reading_domain.py` verifying model validation and edge cases.

---

## Phase 2: Database Storage & Reading Services (Priority: P1)
- [x] T003 Update `backend/database/schema.py` to create `reading_progress`, `annotations`, and `bookmarks` tables.
- [x] T004 Implement `ReadingService` in `backend/services/reading_service.py` supporting progress retrieval, saving, automatic Calibre custom column sync (`#read_status`), annotations CRUD, bookmarks CRUD, and markdown export.
- [x] T005 Implement `ComicService` in `backend/services/comic_service.py` to extract page lists and stream images from CBZ archives.
- [x] T006 Implement unit tests in `tests/unit/test_reading_service.py` validating progress saving, Calibre custom status updates, annotations, and comic page extraction.

---

## Phase 3: API Endpoints & Contract Tests (Priority: P1)
- [x] T007 Implement `backend/api/reader_router.py` exposing progress, annotations, bookmarks, markdown export, comic manifest, and comic page image endpoints.
- [x] T008 Mount `reader_router` in `backend/main.py`.
- [x] T009 Implement contract tests in `tests/contract/test_reader_api.py` validating endpoint lifecycles and Calibre database integration.

---

## Phase 4: Frontend UI & Reader Suite (Priority: P2)
- [x] T010 Add TypeScript interfaces in `frontend/src/types/index.ts` for reading progress, annotations, bookmarks, and comic manifests.
- [x] T011 Implement API methods in `frontend/src/api/client.ts` for reader endpoints.
- [x] T012 Update Zustand store in `frontend/src/store/useStore.ts` with reading progress, annotations, active format, and sync actions.
- [x] T013 Implement `frontend/src/components/reader/ComicReader.tsx` supporting Left-to-Right, Right-to-Left (Manga), and Vertical Webtoon scroll modes.
- [x] T014 Implement `frontend/src/components/reader/AnnotationsDrawer.tsx` for viewing, searching, jumping to, and exporting highlights/notes.
- [x] T015 Update `frontend/src/components/reader/EpubReader.tsx` with text highlighting listener, progress debounced backend sync, and annotations.
- [x] T016 Update `frontend/src/components/reader/PdfReader.tsx` with progress sync and page navigation.
- [x] T017 Enhance reader modal in `frontend/src/App.tsx` and `DetailInspector.tsx` to let users choose format (EPUB, PDF, CBZ) and toggle the annotations drawer.

---

## Phase 5: Verification & Commit (Priority: P3)
- [x] T018 Run `uv run pytest --cov=backend` to verify all backend tests pass.
- [x] T019 Run `npm run build` in `frontend/` to verify zero TypeScript errors and production bundle.
- [x] T020 Commit Feature 012 to git.
