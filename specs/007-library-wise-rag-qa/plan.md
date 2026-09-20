# Implementation Plan: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature**: 007 Library-Wise LanceDB RAG & Conversational QA Agent  
**Branch**: `007-library-wise-rag-qa`  
**Date**: 2026-09-20  
**Status**: Ready for Implementation  

---

## Technical Context

xBookLibrary turns personal digital book collections into actionable, verifiable knowledge. Feature 007 establishes the core Library-Wise RAG system and conversational QA agent:
1. **Self-Contained Vector Storage**: Embedded LanceDB stored inside `<LibraryRoot>/.vectors/` ensuring complete portability.
2. **Hierarchical Semantic Chunking**: Chapter-aware, token-bounded document segmentation (768 tokens, 100 overlap) prepended with book/chapter breadcrumbs.
3. **Pluggable Embedding Providers**: Google Gemini `text-embedding-004` (768 dimensions), mock test provider, and Ollama fallback.
4. **Hybrid Search Pipeline**: Dense cosine distance combined with BM25 keyword matching via Reciprocal Rank Fusion (RRF).
5. **Grounded Conversational QA Agent**: Multi-turn dialogue with strict evidence guardrails, producing verifiable `[Title, Chapter]` citations.
6. **Background Asynchronous Worker**: Background single-book and library batch indexing with progress reporting and checksum delta skipping.

---

## Constitution Check

- **Principle I: Self-Contained Portable Library Isolation**:
  - *Pass*: Vector indexes are stored in `<LibraryRoot>/.vectors/` alongside `metadata.db`. Moving the directory preserves all embeddings.
- **Principle II: Clean Architecture & Pluggable Strategy**:
  - *Pass*: `EmbeddingProvider` and `RAGService` operate against domain abstractions, decoupled from raw web routes and database drivers.
- **Principle IV: Test-First Discipline**:
  - *Pass*: Strict TDD with unit, integration, and contract tests written and verified before implementation.
- **Principle V: Multi-Resolution Knowledge & Grounded RAG**:
  - *Pass*: Hierarchical chunking preserves chapter context; QA agent enforces strict grounding with verifiable citations. Zero ungrounded hallucinations permitted.

---

## Phase Breakdown

### Phase 1: Foundational Schema & Domain Models
- Update `backend/database/schema.py` to create `x_index_status`, `x_chat_sessions`, and `x_chat_messages` tables.
- Create `backend/domain/rag.py` with Pydantic v2 schemas: `VectorChunk`, `SearchResult`, `Citation`, `ChatMessage`, `ChatSession`, `IndexStatus`.
- Implement `backend/providers/embedding_provider.py` with `BaseEmbeddingProvider`, `GeminiEmbeddingProvider`, `MockEmbeddingProvider`.

### Phase 2: User Story 1 - Hierarchical Chunking & LanceDB Indexing Engine
- Implement `backend/services/rag_indexer.py`:
  - `chunk_book(book_id, library_path, chapters)`: token-aware sliding window with breadcrumbs.
  - `index_book(book_id, library_path)`: LanceDB table connection to `<LibraryRoot>/.vectors/`, batch embedding, and vector insertion.
  - Incremental checksum delta checks via `x_index_status`.
- Tests: `tests/unit/test_rag_indexer.py` (chunking logic, LanceDB storage, delta skips).

### Phase 3: User Story 2 - Hybrid Search & Retrieval Service
- Implement `backend/services/rag_search.py`:
  - Dense vector cosine similarity search in LanceDB.
  - Keyword BM25 scoring over chunk text.
  - Reciprocal Rank Fusion (RRF) combiner.
  - Filtering by `book_id`, `library_id`, author.
- Tests: `tests/unit/test_rag_search.py` (dense search, keyword search, RRF fusion, scoping).

### Phase 4: User Story 3 - Conversational QA Agent with Citations
- Implement `backend/services/rag_chat_agent.py`:
  - Session management in SQLite (`x_chat_sessions`, `x_chat_messages`).
  - Context assembly: query reformulation, top-K chunk retrieval, prompt templating.
  - LLM completion with citation extraction and validation.
  - Ungrounded query refusal guardrail.
- Tests: `tests/unit/test_rag_chat_agent.py` (session turns, citation validation, refusal).

### Phase 5: User Story 4 & 5 - Background Worker & REST Endpoints
- Implement `backend/api/rag_router.py`:
  - `POST /api/libraries/{id}/index` & `POST /api/books/{id}/index`
  - `GET /api/libraries/{id}/index/status`
  - `POST /api/libraries/{id}/search`
  - `POST /api/chat/sessions`, `GET /api/chat/sessions`, `GET /api/chat/sessions/{id}`, `DELETE /api/chat/sessions/{id}`
  - `POST /api/chat/sessions/{id}/messages`
- Mount `rag_router` in `backend/main.py`.
- Tests: `tests/contract/test_rag_api.py`.

### Phase 6: Polish & Verification
- Ruff linter & formatter verification.
- Full pytest test suite asserting 100% green tests across all features.
