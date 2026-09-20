# Tasks: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature**: 007 Library-Wise LanceDB RAG & Conversational QA Agent  
**Branch**: `007-library-wise-rag-qa`  
**Status**: Ready  

---

## Phase 1: Setup & Foundational Schema (Priority: P1)

**Goal**: Establish relational schema for RAG tracking/chat sessions, Pydantic domain models, and the pluggable embedding provider abstraction.

### Tests for Foundational Schema & Models
- [x] T001 [P] Unit test for RAG domain schemas (`VectorChunk`, `SearchResult`, `Citation`, `ChatMessage`, `ChatSession`, `IndexStatus`) in `tests/unit/test_rag_domain.py`.
- [x] T002 [P] Unit test for `EmbeddingProvider` abstraction (verifying `GeminiEmbeddingProvider` and `MockEmbeddingProvider` output dimensions and normalized vectors) in `tests/unit/test_embedding_provider.py`.

### Implementation for Foundational Schema & Models
- [x] T003 Update `backend/database/schema.py` to create `x_index_status`, `x_chat_sessions`, and `x_chat_messages` tables with appropriate indexes and foreign keys.
- [x] T004 Implement domain models in `backend/domain/rag.py`.
- [x] T005 Implement `BaseEmbeddingProvider`, `GeminiEmbeddingProvider`, and `MockEmbeddingProvider` in `backend/providers/embedding_provider.py`.


---

## Phase 2: User Story 1 - Hierarchical Chunking & LanceDB Indexing Engine (Priority: P1)

**Goal**: Implement chapter-aware document chunking, LanceDB table initialization under `<LibraryRoot>/.vectors/`, and single-book & batch vector indexing with delta checksum skipping.

### Tests for User Story 1
- [x] T006 [P] [US1] Unit test for hierarchical chunking (sliding window with chapter breadcrumbs and token limits) in `tests/unit/test_rag_indexer.py`.
- [x] T007 [P] [US1] Unit test for LanceDB indexing (embedded storage in `<LibraryRoot>/.vectors/`, delta checksum skipping, and metadata preservation) in `tests/unit/test_rag_indexer.py`.

### Implementation for User Story 1
- [x] T008 [US1] Implement `RAGIndexer` in `backend/services/rag_indexer.py` with `chunk_book`, `index_book`, and `_get_or_create_table`.
- [x] T009 [US1] Implement incremental delta checksum checking in `RAGIndexer` using `x_index_status`.


---

## Phase 3: User Story 2 - Hybrid Search & Retrieval Service (Priority: P2)

**Goal**: Implement hybrid retrieval combining dense LanceDB vector cosine similarity with BM25 keyword matching via Reciprocal Rank Fusion (RRF).

### Tests for User Story 2
- [x] T010 [P] [US2] Unit test for dense search, keyword matching, and RRF rank fusion in `tests/unit/test_rag_search.py`.
- [x] T011 [P] [US2] Unit test for query filtering (scoped by `book_id`, `library_id`, or author) in `tests/unit/test_rag_search.py`.

### Implementation for User Story 2
- [x] T012 [US2] Implement `RAGSearchService` in `backend/services/rag_search.py` with vector cosine search, BM25 keyword matching, and Reciprocal Rank Fusion.
- [x] T013 [US2] Implement metadata scoping and filtering in `RAGSearchService`.


---

## Phase 4: User Story 3 - Grounded Conversational QA Agent (Priority: P3)

**Goal**: Implement multi-turn conversational chat sessions, prompt assembly with retrieved context, LLM answer synthesis, structured citation extraction, and refusal guardrails.

### Tests for User Story 3
- [x] T014 [P] [US3] Unit test for conversational chat agent (session persistence, multi-turn history, citation formatting, and out-of-context refusal) in `tests/unit/test_rag_chat_agent.py`.

### Implementation for User Story 3
- [x] T015 [US3] Implement `RAGChatAgent` in `backend/services/rag_chat_agent.py` supporting session creation, message persistence, context retrieval, grounded answer generation, and citation extraction.


---

## Phase 5: User Story 4 & 5 - Background Worker & REST Endpoints (Priority: P4)

**Goal**: Expose REST endpoints for indexing management, search, and conversational chat, with background job execution.

### Tests for User Story 4 & 5
- [x] T016 [P] [US4/US5] Contract tests for RAG endpoints (`/api/libraries/{id}/index`, `/api/books/{id}/index`, `/api/libraries/{id}/search`, `/api/chat/sessions`, `/api/chat/sessions/{id}/messages`) in `tests/contract/test_rag_api.py`.

### Implementation for User Story 4 & 5
- [x] T017 [US4/US5] Implement `rag_router.py` in `backend/api/rag_router.py`.
- [x] T018 [US4/US5] Mount `rag_router` in `backend/main.py`.


---

## Phase 6: Polish & Verification (Priority: P5)

**Goal**: Zero lint/formatting issues, 100% test pass rate across all features, verified library portability.

- [x] T019 Run `ruff check` and `ruff format` across `backend/` and `tests/`.
- [x] T020 Execute full Pytest test suite asserting 100% passing tests across all features with coverage check.

