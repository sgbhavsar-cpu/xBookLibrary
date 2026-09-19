# Tasks: Core Library Model, Calibre Storage & Multi-Format Ingestion Strategy

**Feature Branch**: `001-core-library-ingestion`  
**Date**: 2026-09-20  
**Spec**: [specs/001-core-library-ingestion/spec.md](file:///c:/sac/progs/xBookLibrary/specs/001-core-library-ingestion/spec.md)  
**Plan**: [specs/001-core-library-ingestion/plan.md](file:///c:/sac/progs/xBookLibrary/specs/001-core-library-ingestion/plan.md)  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency management with `uv`.

- [x] T001 Initialize Python project layout with `backend/` and `tests/` directories per plan.md.
- [x] T002 Create `pyproject.toml` with `uv` configuring FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, `watchfiles`, `ebooklib`, `pypdf`, `pypdfium2`, `python-docx`, `pytest`, and `ruff`.
- [x] T003 [P] Configure Ruff linting and formatting configuration in `pyproject.toml`.
- [x] T004 [P] Create `tests/conftest.py` with reusable test fixtures (temporary directories, sample mock files).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain contracts, models, and SQLite schema layer that all user stories depend upon.

**CRITICAL**: No user story implementation can proceed until this foundation is in place.

- [x] T005 Implement domain entity models in `backend/domain/entities.py` (Book, Author, BookFormat, Identifier, TocNode, IngestionJob).
- [x] T006 [P] Implement abstract parser contracts and payload dataclasses in `backend/domain/parsers.py` (`BookParserStrategy`, `ParsedBookPayload`, `TocItem`).
- [x] T007 Implement global application configuration and library registry manager in `backend/config.py` (`~/.xbooklibrary/config.json`).
- [x] T008 Implement dynamic per-library SQLite engine and session factory in `backend/database/connection.py`.
- [x] T009 Implement Calibre standard table DDL and `x_` extension tables (`x_toc_nodes`, `x_file_hashes`, `x_ingestion_jobs`) in `backend/database/schema.py`.
- [x] T010 Implement filesystem path sanitization and Calibre directory layout generator in `backend/services/storage_service.py`.

**Checkpoint**: Foundation ready — database schema, domain models, and storage utilities verified with unit tests.

---

## Phase 3: User Story 3 - Pluggable Parser Strategy across Full Format Suite (Priority: P1)

**Goal**: Standardized metadata, cover, TOC, and sample text extraction across all 7 supported formats (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ).

**Independent Test**: Execute parser unit tests asserting that each format outputs a valid `ParsedBookPayload` with title, author, cover bytes, and TOC nodes.

### Tests for User Story 3
- [x] T011 [P] [US3] Unit tests for `EpubParser` in `tests/unit/parsers/test_epub_parser.py`.
- [x] T012 [P] [US3] Unit tests for `PdfParser` in `tests/unit/parsers/test_pdf_parser.py`.
- [x] T013 [P] [US3] Unit tests for `MobiParser` (MOBI & AZW3) in `tests/unit/parsers/test_mobi_parser.py`.
- [x] T014 [P] [US3] Unit tests for `ComicParser` (CBZ/CBR & ComicInfo.xml) in `tests/unit/parsers/test_comic_parser.py`.
- [x] T015 [P] [US3] Unit tests for `DocxParser` and `TextParser` in `tests/unit/parsers/test_docx_text_parser.py`.

### Implementation for User Story 3
- [x] T016 [P] [US3] Implement `EpubParser` using `ebooklib` + `lxml` in `backend/parsers/epub_parser.py`.
- [x] T017 [P] [US3] Implement `PdfParser` using `pypdf` + `pypdfium2` in `backend/parsers/pdf_parser.py`.
- [x] T018 [P] [US3] Implement `MobiParser` using PalmDOC & EXTH headers in `backend/parsers/mobi_parser.py`.
- [x] T019 [P] [US3] Implement `ComicParser` using `zipfile` & `ComicInfo.xml` in `backend/parsers/comic_parser.py`.
- [x] T020 [P] [US3] Implement `DocxParser` and `TextParser` in `backend/parsers/docx_parser.py` and `backend/parsers/text_parser.py`.
- [x] T021 [US3] Implement `ParserRegistry` factory in `backend/parsers/__init__.py` to auto-resolve parser strategy by file extension.

**Checkpoint**: All 7 format parsers passing unit tests with standardized payload extraction.

---

## Phase 4: User Story 2 - Existing Calibre Library In-Place Adoption & Sync (Priority: P1)

**Goal**: Zero-copy adoption of existing Calibre library folders, reading `metadata.db`, mapping books/authors/tags/series in place, and preparing `.vectors/`.

**Independent Test**: Point `LibraryManager` to an existing Calibre test directory; verify all books and metadata are immediately accessible without moving or altering any files.

### Tests for User Story 2
- [x] T022 [P] [US2] Unit test for Calibre `metadata.db` schema introspection and validation in `tests/unit/test_calibre_introspection.py`.
- [x] T023 [P] [US2] Integration test for adopting an existing Calibre library in `tests/integration/test_calibre_adoption.py`.

### Implementation for User Story 2
- [x] T024 [US2] Implement Calibre schema introspection and migration validator in `backend/services/calibre_sync.py`.
- [x] T025 [US2] Implement in-place library adoption routine in `backend/services/library_manager.py`.
- [x] T026 [US2] Implement `.vectors/` directory initialization and `x_` table registration in `backend/services/library_manager.py`.

**Checkpoint**: Existing Calibre libraries can be adopted in place in under 5 seconds with zero file modifications.

---

## Phase 5: User Story 1 - Interactive Multi-Format Book Upload & Ingestion (Priority: P1)

**Goal**: Web upload for single/multiple books with automatic format detection, parsing, cover generation, Calibre `metadata.opf` export, and smart multi-format deduplication.

**Independent Test**: Upload EPUB, PDF, and alternate formats of the same book via the API; verify they are saved to disk in the Calibre layout and recorded in SQLite with deduplication and format merging.

### Tests for User Story 1
- [ ] T027 [P] [US1] Unit test for SHA-256 byte deduplication and multi-format merging in `tests/unit/test_format_merging.py`.
- [ ] T028 [P] [US1] API contract test for `POST /api/books/upload` and `GET /api/books/{id}` in `tests/contract/test_books_api.py`.

### Implementation for User Story 1
- [ ] T029 [US1] Implement `IngestionService` in `backend/services/ingestion_service.py` to coordinate file hashing, parser execution, cover saving, and OPF creation.
- [ ] T030 [US1] Implement smart multi-format deduplication logic in `backend/services/ingestion_service.py` (attaching new format to existing book record).
- [ ] T031 [US1] Implement `metadata.opf` XML builder in `backend/services/storage_service.py`.
- [ ] T032 [US1] Implement FastAPI `books_router.py` with `/api/books`, `/api/books/{id}`, and `/api/books/upload`.

**Checkpoint**: End-to-end book upload, parsing, Calibre storage, and retrieval fully functional.

---

## Phase 6: User Story 4 - Calibre-Compatible Deterministic Layout & Portability (Priority: P2)

**Goal**: Full library directory portability and deterministic folder organization (`<Author>/<Title> (<Year>)/<Title> - <Author>.<ext>`).

**Independent Test**: Relocate a library directory to a new temporary path, update registry, and verify that all book files, covers, and formats load seamlessly.

### Tests for User Story 4
- [ ] T033 [P] [US4] Test library folder relocation and relative path resolution in `tests/unit/test_library_portability.py`.

### Implementation for User Story 4
- [ ] T034 [US4] Implement relative path resolution and portability verification in `backend/services/storage_service.py`.
- [ ] T035 [US4] Implement cover streaming and thumbnail generation endpoint (`GET /api/books/{id}/cover`) in `backend/api/books_router.py`.

**Checkpoint**: Library folders can be moved to any disk location or machine without breaking references.

---

## Phase 7: User Story 5 - Automated Directory Watcher & Bulk Import Scanner (Priority: P2)

**Goal**: Background watcher monitoring intake folders and automatically ingesting dropped book files with real-time job tracking.

**Independent Test**: Drop 10 files into the designated auto-import folder; assert watcher detects them, processes them, and records results in `x_ingestion_jobs`.

### Tests for User Story 5
- [ ] T036 [P] [US5] Integration test for directory watcher in `tests/integration/test_watcher_service.py`.

### Implementation for User Story 5
- [ ] T037 [US5] Implement `WatcherService` using `watchfiles` in `backend/services/watcher_service.py`.
- [ ] T038 [US5] Implement async batch job worker and status tracking in `backend/services/job_worker.py`.
- [ ] T039 [US5] Implement FastAPI `jobs_router.py` with `GET /api/jobs/{job_id}`.

**Checkpoint**: Auto-import directory automatically monitors and ingests files in the background.

---

## Phase 8: User Story 6 - Multi-Library Registry & Switcher (Priority: P3)

**Goal**: Create, register, list, and switch between distinct isolated libraries.

**Independent Test**: Register two libraries via API, switch active library, and verify queries strictly isolate books to the active library.

### Tests for User Story 6
- [ ] T040 [P] [US6] API contract test for `GET /api/libraries` and `POST /api/libraries` in `tests/contract/test_libraries_api.py`.

### Implementation for User Story 6
- [ ] T041 [US6] Implement library switching logic in `backend/services/library_manager.py`.
- [ ] T042 [US6] Implement FastAPI `libraries_router.py` with `/api/libraries` and active library selection.

**Checkpoint**: Multiple libraries can be created and toggled dynamically with strict database isolation.

---

## Phase 9: Polish, Validation & Verification

**Purpose**: Code quality, test coverage, and documentation verification.

- [ ] T043 Run `ruff check backend/ tests/` and `ruff format backend/ tests/` with zero lint issues.
- [ ] T044 Execute complete Pytest suite (`pytest --cov=backend tests/`) asserting >85% coverage on core services and parsers.
- [ ] T045 Execute and validate end-to-end user scenarios from `quickstart.md`.
