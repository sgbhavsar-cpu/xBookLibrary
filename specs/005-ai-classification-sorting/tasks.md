# Tasks: AI Classification & Taxonomy Sorting

**Feature**: `005-ai-classification-sorting`  
**Input**: [specs/005-ai-classification-sorting/plan.md](file:///c:/sac/progs/xBookLibrary/specs/005-ai-classification-sorting/plan.md)  

---

## Phase 1: Setup & Foundational Schema

**Goal**: Extend database schema and establish domain entities and reference dictionaries.

- [ ] T001 Add `x_classifications`, `x_taxonomies`, `x_books_taxonomies_link`, `x_bookshelves`, and `x_books_bookshelves_link` tables to `backend/database/schema.py`.
- [ ] T002 Implement domain models `ClassificationResult`, `TaxonomyNode`, and `Bookshelf` in `backend/domain/classification.py`.
- [ ] T003 Implement standard reference dictionary of top 500 BISAC categories and Dewey Decimal divisions in `backend/data/bisac_ddc_reference.py`.

---

## Phase 2: User Story 1 - Dual-Taxonomy Classification Engine (Priority: P1)

**Goal**: Analyze books to assign primary BISAC codes/headings and Dewey Decimal numbers with offline heuristic fallback.

### Tests for User Story 1
- [ ] T004 [P] [US1] Unit test for BISAC & DDC classification logic (LLM structured extraction + offline dictionary fallback) in `tests/unit/test_classification_service.py`.

### Implementation for User Story 1
- [ ] T005 [US1] Implement offline heuristic classifier matching title/author/tags against embedded dictionary in `backend/services/classification_service.py`.
- [ ] T006 [US1] Implement LLM zero-shot structured classification using `LiteLLMClientAdapter` in `backend/services/classification_service.py`.
- [ ] T007 [US1] Implement TOC outline and chapter preview sampling for books with sparse metadata in `backend/services/classification_service.py`.
- [ ] T008 [US1] Implement SQLite persistence for `x_classifications` and injection into Calibre tags and OPF metadata in `backend/services/classification_service.py`.

---

## Phase 3: User Story 2 - Custom Hierarchical Taxonomy & Virtual Bookshelves (Priority: P2)

**Goal**: Enable custom hierarchical category trees and virtual bookshelf groupings without altering Calibre disk structure.

### Tests for User Story 2
- [ ] T009 [P] [US2] Unit test for custom taxonomy hierarchy CRUD and virtual bookshelf assignment in `tests/unit/test_taxonomy_service.py`.

### Implementation for User Story 2
- [ ] T010 [US2] Implement `TaxonomyService` managing hierarchical category trees (`x_taxonomies`) in `backend/services/taxonomy_service.py`.
- [ ] T011 [US2] Implement virtual bookshelf CRUD and book assignment (`x_bookshelves`, `x_books_bookshelves_link`) in `backend/services/taxonomy_service.py`.
- [ ] T012 [US2] Implement automated mapping of classified books to best-fit custom taxonomy nodes in `backend/services/taxonomy_service.py`.

---

## Phase 4: User Story 3 - High-Precision Tagging & Staged Diff Safeguards (Priority: P3)

**Goal**: Refine tags, filter noise, and route uncertain classifications (< 0.85 confidence) to `.vectors/staging/` for human approval.

### Tests for User Story 3
- [ ] T013 [P] [US3] Unit test verifying confidence threshold (>= 0.85 auto-apply vs. < 0.85 staged diff proposal) in `tests/unit/test_classification_safeguards.py`.

### Implementation for User Story 3
- [ ] T014 [US3] Implement semantic tag cleaner (removing noise like "ebook", "general", "paperback") in `backend/services/classification_service.py`.
- [ ] T015 [US3] Implement staging of low-confidence classification proposals in `.vectors/staging/` via `ProposalManager`.
- [ ] T016 [US3] Implement application of approved classification proposals to Calibre records and `metadata.opf`.

---

## Phase 5: User Story 4 - REST API Endpoints (Priority: P4)

**Goal**: Expose REST endpoints for book classification, taxonomy tree management, and virtual bookshelves.

### Tests for User Story 4
- [ ] T017 [P] [US4] Contract tests for `/api/books/{id}/classify`, `/api/taxonomies`, and `/api/bookshelves` in `tests/contract/test_taxonomies_api.py`.

### Implementation for User Story 4
- [ ] T018 [US4] Implement `taxonomies_router.py` in `backend/api/taxonomies_router.py`.
- [ ] T019 [US4] Mount `taxonomies_router` in `backend/main.py`.

---

## Phase 6: Polish & Verification

**Goal**: 100% test coverage, zero lint/formatting issues, verified Calibre compatibility.

- [ ] T020 Run `ruff check` and `ruff format` across `backend/` and `tests/`.
- [ ] T021 Execute full Pytest test suite asserting 100% passing tests across all features.
