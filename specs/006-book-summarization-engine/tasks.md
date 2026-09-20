# Tasks: Multi-Resolution AI Book Summarization Engine

**Feature**: `006-book-summarization-engine`  
**Input**: [specs/006-book-summarization-engine/plan.md](file:///c:/sac/progs/xBookLibrary/specs/006-book-summarization-engine/plan.md)  

---

## Phase 1: Setup & Foundational Schema

**Goal**: Establish domain entities and database schema for multi-resolution summaries.

- [ ] T001 Add `x_summaries` table and indexes to `backend/database/schema.py`.
- [ ] T002 Implement domain models `ExecutiveSnapshot`, `ChapterSummary`, `ConceptualIndex`, `SummaryMetadata`, and `BookSummary` in `backend/domain/summary.py`.

---

## Phase 2: User Story 1 - Multi-Resolution Summary Engine (Priority: P1)

**Goal**: Extract chapter text from book files, execute hierarchical map-reduce prompts via LLM, and synthesize tiered summaries.

### Tests for User Story 1
- [ ] T003 [P] [US1] Unit test for chapter extraction, map-reduce LLM prompts, and single-pass fallback in `tests/unit/test_summarization_service.py`.

### Implementation for User Story 1
- [ ] T004 [US1] Implement chapter text extraction and section boundary detection in `backend/services/summarization_service.py`.
- [ ] T005 [US1] Implement chapter-level summary mapping prompt in `backend/services/summarization_service.py`.
- [ ] T006 [US1] Implement executive snapshot & conceptual index reduce prompt in `backend/services/summarization_service.py`.
- [ ] T007 [US1] Implement single-pass summary optimization for short works (< 3,000 words) in `backend/services/summarization_service.py`.

---

## Phase 3: User Story 2 - Dual-Storage & Instant Cache Retrieval (Priority: P2)

**Goal**: Persist summaries in `<Author>/<Title> (<Year>)/summary.json` and SQLite `x_summaries`, providing sub-50ms cached retrieval.

### Tests for User Story 2
- [ ] T008 [P] [US2] Unit test verifying `summary.json` disk persistence, `x_summaries` SQLite caching, and in-place adoption in `tests/unit/test_summary_storage.py`.

### Implementation for User Story 2
- [ ] T009 [US2] Implement `summary.json` serialization and writing in `StorageService` / `SummarizationService`.
- [ ] T010 [US2] Implement SQLite CRUD operations for `x_summaries` in `SummarizationService`.
- [ ] T011 [US2] Implement automatic adoption of pre-existing `summary.json` during library scan/ingestion.

---

## Phase 4: User Story 3 & 4 - Customization, Exporter & Asynchronous Jobs (Priority: P3/P4)

**Goal**: Support background job tracking, custom prompt instructions, and export to Markdown, HTML, and Calibre OPF `<dc:description>`.

### Tests for User Story 3 & 4
- [ ] T012 [P] [US3/US4] Unit test for Markdown/HTML formatters, custom prompt regeneration, and Calibre OPF synchronization in `tests/unit/test_summary_exporter.py`.

### Implementation for User Story 3 & 4
- [ ] T013 [US3] Implement background job integration with chapter progress updates in `SummarizationService`.
- [ ] T014 [US4] Implement Markdown and styled HTML export formatters in `backend/services/summary_exporter.py`.
- [ ] T015 [US4] Implement Calibre metadata synchronization (updating `comments` and `metadata.opf` `<dc:description>`) in `backend/services/summary_exporter.py`.

---

## Phase 5: REST API Endpoints (Priority: P5)

**Goal**: Expose REST endpoints for retrieving, generating, exporting, and syncing book summaries.

### Tests for User Story 5
- [ ] T016 [P] [US5] Contract tests for `/api/books/{id}/summary`, `/api/books/{id}/summary/export`, and `/api/books/{id}/summary/sync-calibre` in `tests/contract/test_summaries_api.py`.

### Implementation for User Story 5
- [ ] T017 [US5] Implement `summaries_router.py` in `backend/api/summaries_router.py`.
- [ ] T018 [US5] Mount `summaries_router` in `backend/main.py`.

---

## Phase 6: Polish & Verification

**Goal**: Zero lint/formatting issues, 100% test pass rate across all features, verified Calibre compatibility.

- [ ] T019 Run `ruff check` and `ruff format` across `backend/` and `tests/`.
- [ ] T020 Execute full Pytest test suite asserting 100% passing tests across all features with coverage check.
