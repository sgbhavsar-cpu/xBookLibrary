# Research & Architectural Decisions: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature**: 007 Library-Wise LanceDB RAG & Conversational QA Agent  
**Date**: 2026-09-20  
**Status**: Completed  

---

## 1. Storage Isolation: Embedded LanceDB vs Central Vector Database

### Decision
Store vector embeddings inside each individual library root directory under `<LibraryRoot>/.vectors/` using embedded **LanceDB** (`lancedb<=0.38.0`).

### Rationale
- **Constitution Principle I (Self-Contained Portability)**: A library folder must be completely self-contained. If a user moves their Calibre library directory (or syncs it to a flash drive or NAS), all vector embeddings, indexes, and document knowledge stay intact without external database dependencies.
- **Embedded Zero-Config Architecture**: LanceDB operates natively inside the Python process using Apache Arrow / Lance columnar disk format. No standalone server process (like Pinecone, Milvus, or Qdrant daemon) is required, eliminating runtime maintenance for desktop users.
- **High Performance on Local Hardware**: Lance format enables disk-backed nearest-neighbor vector search with sub-millisecond retrieval on local SSDs, perfectly scaling to libraries of 10,000+ books without memory bloat.

### Alternatives Considered
- *Central SQLite vector extension (`sqlite-vec`)*: Promising, but immature cross-platform wheel availability and lacking native hybrid BM25 + vector search optimizations.
- *ChromaDB*: Higher dependency footprint, sqlite locking issues under Windows threads, and bloated disk footprint compared to Lance's columnar compression.
- *Qdrant / Milvus*: Requires running a Docker container or background service daemon, violating the self-contained desktop ethos of Calibre.

---

## 2. Document Chunking Strategy: Hierarchical Structural Chunking

### Decision
Implement **Hierarchical Structural Chunking** aware of chapter headings, sections, and paragraphs:
- Target chunk size: **768 tokens** (~3,000 characters) with a **100-token overlap** (~400 characters).
- Boundaries prioritize natural semantic breaks: chapter headings (`<h1>`/`<h2>`), section dividers, and double newline paragraphs.
- Every chunk prepends a hierarchical breadcrumb header:
  `[Book: "{Title}" by {Authors} | Chapter: "{Chapter Title}"]\n\n{Chunk Text}`
- Chunk metadata preserves: `chunk_id`, `book_id`, `library_id`, `chapter_index`, `chapter_title`, `start_char`, `end_char`, `token_count`.

### Rationale
- Standard arbitrary character chunking breaks mid-sentence and loses context (e.g., an excerpt describing a theorem without knowing what chapter or author it belongs to).
- Breadcrumb header injection ensures that vector embeddings capture the context of the containing chapter and book even if the specific passage uses pronouns or domain shorthand.
- 768 tokens provides sufficient argumentative or narrative depth for complex non-fiction and textbooks while fitting well within LLM context windows for top-K retrieval.

### Alternatives Considered
- *Fixed 500-character window*: Severely fragments sentences and thoughts, degrading retrieval accuracy.
- *Whole-chapter chunking*: Contexts exceed optimal retrieval resolution (chapters can be 5,000–15,000 words), diluting semantic similarity and wasting prompt context.

---

## 3. Hybrid Search: Vector Cosine Similarity + BM25 Keyword Search

### Decision
Combine dense semantic search with keyword search using **Reciprocal Rank Fusion (RRF)**:
$$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + rank_m(d)}$$
where $k = 60$.
- Dense search queries LanceDB cosine distance using normalized query embeddings.
- Keyword search computes lexical relevance over chunk content (using LanceDB full-text search / tantivy or an in-memory BM25 index over candidate chunks).
- Hybrid search allows users to filter by `book_id`, `library_id`, author, or tag.

### Rationale
- Dense vector search is outstanding at conceptual and thematic inquiries ("how does the author explain cognitive bias?") but frequently underperforms on exact named entities, unique IDs, or rare technical terms ("Algorithm 4.2", "Wozniak", "RFC 7519").
- Hybrid search provides the best of both worlds, ensuring 95%+ retrieval accuracy across both conceptual questions and specific keyword lookups.

---

## 4. Embedding Provider: Google Gemini `text-embedding-004` & Local Mock Fallback

### Decision
Utilize **Google Gemini `text-embedding-004`** (768 dimensions) as the primary cloud embedding engine via `litellm` / `google-genai`, with a local mock provider for offline tests and Ollama (`nomic-embed-text` [768-dim]) for local-only users.

### Rationale
- `text-embedding-004` delivers state-of-the-art MTEB retrieval performance at minimal latency and negligible cost.
- Output dimension is 768 floats, matching LanceDB's optimized vector indexing and keeping local `.vectors/` index size compact (~3 KB per chunk).
- The unified `EmbeddingProvider` abstraction mirrors our existing `LLMAdapter` pattern, allowing zero-code swapping between Gemini, Ollama, and test mocks.

---

## 5. Conversational QA Agent Architecture & Citation Grounding

### Decision
Implement a multi-turn conversational agent with **Strict Source Grounding**:
- **Prompt Structure**:
  1. System Prompt enforcing: "You are the scholarly research assistant for xBookLibrary. Answer the user's question using ONLY the retrieved source passages below. Every factual claim MUST include a citation in the format `[Book Title, Chapter Title]`. If the retrieved context does not contain sufficient evidence to answer, state clearly that the answer is not present in the indexed books."
  2. Rolling Chat History: Recent conversation turns preserved in session state (up to 10 turns).
  3. Context Block: Top-5 retrieved chunks formatted with structured metadata.
- **Structured Citations**: The agent API response returns both the generated markdown answer and an array of validated `Citation` objects (`book_id`, `book_title`, `authors`, `chapter_title`, `snippet`, `score`), allowing frontend components to highlight and deep-link directly to book pages.

### Rationale
- Satisfies Constitution Principle V (Verifiable Knowledge & Strict Grounding).
- Eliminates AI hallucinations and makes answers immediately auditable by human readers.

---

## 6. Background Indexing & Delta Checksum Tracking

### Decision
- Add an `x_index_status` table in SQLite (`metadata.db`) tracking:
  `book_id`, `library_id`, `indexed_at`, `chunk_count`, `checksum` (SHA-256 of the book file), `status` (`pending`, `indexing`, `indexed`, `failed`).
- Incremental indexing inspects file modification time and checksum: books whose checksum matches the existing index are skipped in under 5 milliseconds.
- Indexing jobs run via `JobWorker` and `BackgroundTasks`, updating progress records (`total_books`, `completed_books`, `current_book`, `percent_complete`).
