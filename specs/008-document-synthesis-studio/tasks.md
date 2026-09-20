# Tasks: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature**: 008 Multi-Book Document Synthesis & Knowledge Brief Studio  
**Branch**: `008-document-synthesis-studio`  
**Status**: Ready  

---

## Phase 1: Setup & Foundational Schema (Priority: P1)

**Goal**: Establish relational schema for synthesized research documents and Pydantic v2 domain models.

### Tests for Foundational Schema & Models
- [ ] T001 [P] Unit test for synthesis domain models (`SynthesisSection`, `SynthesisSource`, `SynthesisDocument`, `SynthesisJobStatus`) in `tests/unit/test_synthesis_domain.py`.

### Implementation for Foundational Schema & Models
- [ ] T002 Update `backend/database/schema.py` to add `x_synthesis_documents` table and index.
- [ ] T003 Implement domain models in `backend/domain/synthesis.py`.

---

## Phase 2: User Story 1 & 2 - Multi-Stage Document Synthesis Engine (Priority: P1)

**Goal**: Implement the 4-stage synthesis pipeline: outline generation, targeted sectional evidence retrieval, grounded section drafting with inline citations, and document assembly with bibliography.

### Tests for User Story 1 & 2
- [ ] T004 [P] [US1/US2] Unit tests for outline generation, section retrieval, grounded drafting, and bibliography assembly in `tests/unit/test_synthesis_service.py`.

### Implementation for User Story 1 & 2
- [ ] T005 [US1/US2] Implement `DocumentSynthesisService` in `backend/services/document_synthesis_service.py` with `generate_document`, `generate_outline`, `retrieve_section_evidence`, `draft_section`, and `assemble_document`.

---

## Phase 3: User Story 3 - Exporters & Document Persistence (Priority: P2)

**Goal**: Implement Markdown and styled HTML export formatters, and local disk persistence under `<LibraryRoot>/.synthesis/`.

### Tests for User Story 3
- [ ] T006 [P] [US3] Unit tests for Markdown/HTML formatters and filesystem storage in `tests/unit/test_synthesis_exporter.py`.

### Implementation for User Story 3
- [ ] T007 [US3] Implement `SynthesisExporter` in `backend/services/synthesis_exporter.py` with Markdown/HTML formatting and disk saving.

---

## Phase 4: User Story 4 & REST Endpoints (Priority: P3)

**Goal**: Expose REST endpoints for triggering synthesis, tracking background jobs, listing/retrieving documents, and exporting files.

### Tests for User Story 4
- [ ] T008 [P] [US4] Contract tests for synthesis endpoints (`/api/synthesis/generate`, `/api/synthesis/documents`, `/api/synthesis/documents/{id}`, `/api/synthesis/documents/{id}/export`) in `tests/contract/test_synthesis_api.py`.

### Implementation for User Story 4
- [ ] T009 [US4] Implement `synthesis_router.py` in `backend/api/synthesis_router.py`.
- [ ] T010 [US4] Mount `synthesis_router` in `backend/main.py`.

---

## Phase 5: Polish & Verification (Priority: P4)

**Goal**: Zero lint/formatting issues, 100% test pass rate across all features, verified library portability.

- [ ] T011 Run `ruff check` and `ruff format` across `backend/` and `tests/`.
- [ ] T012 Execute full Pytest test suite asserting 100% passing tests across all features with coverage check.
