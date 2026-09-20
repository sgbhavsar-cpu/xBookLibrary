# Tasks: Agentic Metadata Enrichment & Multimodal Reconciliation

**Feature Branch**: `004-agentic-metadata-enrichment`  
**Date**: 2026-09-20  
**Spec**: [specs/004-agentic-metadata-enrichment/spec.md](file:///c:/sac/progs/xBookLibrary/specs/004-agentic-metadata-enrichment/spec.md)  
**Plan**: [specs/004-agentic-metadata-enrichment/plan.md](file:///c:/sac/progs/xBookLibrary/specs/004-agentic-metadata-enrichment/plan.md)  

---

## Phase 1: Setup & Dependencies

**Purpose**: Dependency installation and provider configuration.

- [ ] T001 Add `litellm>=1.50.0` and `respx>=0.22.0` (for HTTP mocking) to `pyproject.toml`.
- [ ] T002 Verify environment variable loading (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `OLLAMA_HOST`) in `backend/config.py`.

---

## Phase 2: Foundational Domain Contracts & Staging Storage

**Purpose**: Data models and file-based staging management.

- [ ] T003 Implement enrichment domain models in `backend/domain/enrichment.py` (`CandidateMetadata`, `CoverCandidate`, `ProposedField`, `MetadataProposal`).
- [ ] T004 Implement `ProposalManager` in `backend/services/proposal_manager.py` to persist, load, and discard JSON proposals in `.vectors/staging/`.
- [ ] T005 [P] Unit tests for `ProposalManager` staging and cleanup in `tests/unit/test_proposal_manager.py`.

---

## Phase 3: User Story 1 - Multi-Source Online Bibliographic Providers (Priority: P1)

**Goal**: Fetch, parse, and normalize metadata from OpenLibrary, Google Books, and CrossRef with HTTP disk caching.

### Tests for User Story 1
- [ ] T006 [P] [US1] Unit tests for `OpenLibraryProvider` in `tests/unit/providers/test_openlibrary_provider.py`.
- [ ] T007 [P] [US1] Unit tests for `GoogleBooksProvider` in `tests/unit/providers/test_google_books_provider.py`.
- [ ] T008 [P] [US1] Unit tests for `CrossRefProvider` in `tests/unit/providers/test_crossref_provider.py`.

### Implementation for User Story 1
- [ ] T009 [US1] Implement `MetadataProvider` abstract base strategy in `backend/providers/base.py`.
- [ ] T010 [US1] Implement 7-day TTL file-based HTTP cache in `backend/services/http_cache.py`.
- [ ] T011 [US1] Implement `OpenLibraryProvider` in `backend/providers/openlibrary.py`.
- [ ] T012 [US1] Implement `GoogleBooksProvider` in `backend/providers/google_books.py` with high-res cover URL resolution.
- [ ] T013 [US1] Implement `CrossRefProvider` in `backend/providers/crossref.py`.

---

## Phase 4: User Story 2 - Multimodal LLM Vision Fallback (Priority: P1)

**Goal**: Analyze cover image and first pages to extract bibliographic details using LiteLLM (Gemini 2.0 Flash / Ollama).

### Tests for User Story 2
- [ ] T014 [P] [US2] Unit tests for `LiteLLMClientAdapter` in `tests/unit/providers/test_llm_adapter.py`.

### Implementation for User Story 2
- [ ] T015 [US2] Implement `LiteLLMClientAdapter` in `backend/providers/llm_adapter.py` with structured JSON schema prompt.
- [ ] T016 [US2] Implement visual page image extractor for PDF/EPUB in `backend/services/vision_extractor.py`.

---

## Phase 5: User Story 3 & 4 - Cascade Orchestration, Decision Safeguards & Storage (Priority: P1)

**Goal**: Coordinate parallel fetch, enforce strict ISBN auto-apply vs. visual diff staging, and apply approved proposals to Calibre storage.

### Tests for User Story 3 & 4
- [ ] T017 [P] [US3] Unit test for `EnrichmentOrchestrator` decision logic (Exact ISBN auto-applied vs. Fuzzy title staged) in `tests/unit/test_enrichment_orchestrator.py`.
- [ ] T018 [P] [US3] Integration test for applying an approved proposal to Calibre SQLite and `metadata.opf` in `tests/integration/test_proposal_application.py`.

### Implementation for User Story 3 & 4
- [ ] T019 [US3] Implement `EnrichmentOrchestrator` in `backend/services/enrichment_orchestrator.py`.
- [ ] T020 [US3] Implement atomic Calibre record updater in `backend/services/enrichment_orchestrator.py` updating `books`, `authors`, `tags`, `comments`, and `metadata.opf`.

---

## Phase 6: REST API Endpoints (Priority: P1)

**Goal**: Provide REST endpoints for triggering enrichment, querying pending diffs, and approving/discarding proposals.

### Tests for Phase 6
- [ ] T021 [P] API contract tests for `/api/books/{id}/enrich` and `/api/proposals` in `tests/contract/test_proposals_api.py`.

### Implementation for Phase 6
- [ ] T022 Implement `proposals_router.py` in `backend/api/proposals_router.py`.
- [ ] T023 Mount `proposals_router` in `backend/main.py`.

---

## Phase 7: Polish & Verification

**Purpose**: Zero lint issues, comprehensive test suite pass.

- [ ] T024 Run `ruff check` and `ruff format` on `backend/` and `tests/`.
- [ ] T025 Execute full Pytest suite across all features asserting 100% green tests.
