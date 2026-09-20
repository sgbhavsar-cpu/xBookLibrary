# Feature Specification: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature Branch**: `007-library-wise-rag-qa`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "create library wise RAG so that chat bot agent can answer questions from books of that library or create new document based on that knowledge."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Per-Library Vector Indexing & Hierarchical Chunking (Priority: P1)

As a reader and researcher, I want my library's books parsed, hierarchically chunked (preserving chapter titles, sections, and page references), and embedded into a dedicated local vector database inside the library directory, so that the knowledge base remains 100% portable and isolated without cloud vendor lock-in.

**Why this priority**: Without persistent, high-quality vector embeddings and chunk metadata stored inside `<LibraryRoot>/.vectors/`, semantic retrieval and conversational QA cannot function.

**Independent Test**: Can be independently tested by ingesting/indexing a book (EPUB, PDF, TXT, DOCX), asserting the creation of LanceDB tables under `<LibraryRoot>/.vectors/`, and verifying chunk records contain accurate chapter titles, parent headings, and text offsets.

**Acceptance Scenarios**:
1. **Given** a book in the library with extracted chapters and text, **When** indexing is requested, **Then** the book is split into semantic chunks (512–1024 tokens with overlap) tagged with `book_id`, `title`, `authors`, `chapter_title`, and `chunk_index`, embedded via the configured embedding provider, and stored in `<LibraryRoot>/.vectors/`.
2. **Given** a library containing 50 books where 10 are already indexed, **When** a bulk library index job runs, **Then** only the 40 unindexed or modified books are processed (incremental delta indexing), skipping up-to-date embeddings.
3. **Given** a library folder moved to another path or machine, **When** opened in xBookLibrary, **Then** the `.vectors/` index continues to operate without re-embedding or path corruption.

---

### User Story 2 - Hybrid Semantic & Keyword Retrieval (Priority: P2)

As a researcher searching across my book collection, I want to query my library using natural language and receive the most relevant passages through hybrid search (dense semantic vector matching + BM25 keyword matching), so that specific terminology, character names, and abstract thematic queries all retrieve accurate context.

**Why this priority**: Pure dense search often misses exact technical terms or character names, while pure keyword search fails on thematic inquiries. Hybrid search provides the optimal retrieval precision required for grounded answering.

**Independent Test**: Can be tested by querying known keywords (e.g., specific acronym or name) and semantic concepts (e.g., "central philosophical argument on ethics"), verifying that hybrid reciprocal rank fusion (RRF) returns the correct book chapters in the top 5 results.

**Acceptance Scenarios**:
1. **Given** an indexed library, **When** a user submits a query with exact technical jargon, **Then** the search pipeline combines BM25 keyword scoring and cosine vector distance to rank exact matches and conceptually related passages.
2. **Given** a search scoped to a specific book (`book_id` filter) or category/tag, **When** executing retrieval, **Then** results are strictly constrained to the filtered scope without scanning unrelated library books.

---

### User Story 3 - Grounded Conversational QA Agent with Citations (Priority: P3)

As a reader, I want to chat with an AI assistant about a specific book or an entire library, asking detailed questions and receiving clear, comprehensive answers where every claim cites the exact book title, author, chapter, and page/section, with zero ungrounded hallucinations.

**Why this priority**: A book library QA chatbot must be trustworthy; unsubstantiated hallucinations degrade user confidence. Verifiable source citations allow users to click directly to the relevant chapter in the reader.

**Independent Test**: Can be tested by asking a question whose answer exists solely in Chapter 3 of an indexed book, verifying that the generated answer cites `[Title, Chapter 3]` and correctly refuses or states ignorance if asked a question outside the library's contents.

**Acceptance Scenarios**:
1. **Given** a conversation scoped to a library, **When** a user asks a complex multi-part question, **Then** the conversational agent retrieves relevant passages, synthesizes an answer, maintains conversational context across multiple turns, and appends structured citation markers.
2. **Given** a query on a topic not covered by any book in the library, **When** the agent evaluates retrieved context, **Then** it transparently informs the user that the information was not found in the indexed books rather than hallucinating external facts.

---

### User Story 4 - Background Indexing Worker & Progress Tracking (Priority: P4)

As a user with a large library (hundreds or thousands of books), I want library indexing to run as an asynchronous background task with live progress feedback (books processed, current book title, estimated time remaining), so that the application remains responsive and I can monitor indexing progress.

**Why this priority**: Parsing and embedding large collections can take several minutes to hours depending on library size and hardware/API throughput. Users must not face UI freezing or silent background failures.

**Independent Test**: Can be tested by triggering library-wide indexing, observing the job status progression (`queued` -> `running` with progress percentage and book count -> `completed`), and confirming that individual book parsing errors do not halt the entire batch.

**Acceptance Scenarios**:
1. **Given** a background indexing job running on 20 books, **When** progress is polled, **Then** the job state reports `total_books`, `completed_books`, `current_book_title`, and `percent_complete`.
2. **Given** a corrupted PDF or DRM-locked file during indexing, **When** the parser fails, **Then** the error is logged in the job report and indexing continues for all remaining books without crashing.

---

### Edge Cases

- **Large Books (>1,000 pages)**: Chunking must stream or paginate content without exhausting process RAM; vector batch inserts should commit in manageable chunks (e.g., 100 chunks per vector insert).
- **Empty or Scanned Image Books**: If a book lacks extractable text (e.g., image-only PDF without OCR), the indexer must flag it as `no_text_extracted` rather than raising uncaught exceptions.
- **Provider Rate Limiting**: If Google Gemini API returns HTTP 429 during embedding or generation, the pipeline must implement exponential backoff with jitter and retry gracefully.
- **Ollama / Offline Fallback**: If cloud API keys are missing or offline, the system must seamlessly fall back to local Ollama embeddings/LLM if configured.
- **Multiple Concurrent Queries**: LanceDB connection and read queries must support concurrent requests across threads without database locking conflicts.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store LanceDB vector tables in `<LibraryRoot>/.vectors/` ensuring 100% self-contained library portability.
- **FR-002**: System MUST segment parsed book text into semantic chunks of configurable size (default 512–1024 tokens) preserving chapter boundaries and section hierarchies.
- **FR-003**: System MUST embed text chunks using the unified provider interface (Google Gemini `text-embedding-004` / local fallback) with vector dimensions matching the active model.
- **FR-004**: System MUST record chunk metadata including `chunk_id`, `book_id`, `library_id`, `book_title`, `authors`, `chapter_index`, `chapter_title`, `token_count`, and text offsets.
- **FR-005**: System MUST support hybrid search combining dense vector similarity (cosine) with BM25 keyword ranking using Reciprocal Rank Fusion (RRF).
- **FR-006**: System MUST support query filtering by `library_id`, `book_id`, authors, and tags.
- **FR-007**: System MUST provide a conversational QA agent that takes a user query, retrieves top-K relevant chunks (with relevance scoring), and synthesizes a grounded response.
- **FR-008**: System MUST include verifiable citations in conversational responses, referencing `[Book Title, Chapter / Section]`.
- **FR-009**: System MUST support multi-turn conversational chat sessions, preserving rolling dialogue history within the session context.
- **FR-010**: System MUST provide asynchronous background job execution for single-book and full-library indexing with granular progress reporting.
- **FR-011**: System MUST support incremental delta indexing, only computing embeddings for books that have been added, modified, or not yet indexed.
- **FR-012**: System MUST expose REST API endpoints for indexing management, search queries, and conversational chat interactions.

---

### Key Entities

- **VectorChunk**: Represents an embedded slice of a book. Key attributes: `chunk_id`, `book_id`, `library_id`, `chapter_index`, `chapter_title`, `content`, `vector` (float array), `token_count`.
- **ChatSession**: Represents an active conversational thread. Key attributes: `session_id`, `library_id`, `book_id` (optional scope), `messages` (list of user/assistant turns), `created_at`, `updated_at`.
- **ChatMessage**: An individual turn in a dialogue. Key attributes: `message_id`, `role` (`user` | `assistant`), `content`, `citations` (list of `Citation` items), `timestamp`.
- **Citation**: Verifiable source reference for an assistant claim. Key attributes: `book_id`, `book_title`, `authors`, `chapter_title`, `snippet`, `score`.
- **IndexJob**: Background job tracking book or library embedding. Key attributes: `job_id`, `library_id`, `status`, `total_books`, `completed_books`, `current_book`, `errors`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Single-book indexing for an average 300-page book completes in under 30 seconds (excluding external API rate limits).
- **SC-002**: Hybrid search queries return top-K ranked passages in under 250 milliseconds against a library of 10,000 chunks.
- **SC-003**: Conversational QA agent produces grounded answers with accurate chapter citations in 100% of factual test queries.
- **SC-004**: Incremental re-indexing of an already indexed library finishes in under 2 seconds by skipping unchanged books.
- **SC-005**: 100% test pass rate across unit, integration, and API contract tests with zero regressions on existing library/metadata features.

---

## Assumptions

- Book text and chapters can be reliably extracted via existing format parsers (`EPUBParser`, `PDFParser`, `TextParser`, `DocxParser`, `MOBIParser`).
- The primary embedding provider is Google Gemini API (`text-embedding-004`), with mock adapters for offline test execution and Ollama for local deployments.
- LanceDB embedded requires no standalone daemon/server process and operates directly against files in the local filesystem.
- Calibre library portability is preserved because `.vectors/` is stored directly inside each library root directory and uses relative book identifiers.
