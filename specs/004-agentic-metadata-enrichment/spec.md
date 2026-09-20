# Feature Specification: Agentic Metadata Enrichment & Multimodal Reconciliation

**Feature Branch**: `004-agentic-metadata-enrichment`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "Agentic metadata update before classification and sorting, multi-source enrichment (OpenLibrary, Google Books, CrossRef), LLM cover/title fallback, confidence-based hybrid review with side-by-side visual diff."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Source Online Metadata Cascade (Priority: P1)

As a reader importing digital books, I want the system to automatically query OpenLibrary and Google Books in parallel (and CrossRef for academic works) using ISBN or title/author, so that missing bibliographic details (publisher, publication date, description, categories, language, identifiers) are retrieved without manual typing.

**Why this priority**: High-quality metadata is the essential prerequisite for accurate downstream AI classification, sorting, summarization, and vector search.

**Independent Test**: Can be independently tested by querying `MetadataEnrichmentService` with a known ISBN (e.g. `9780441172719` for *Dune*) or Title/Author pair, asserting that candidate payloads from OpenLibrary and Google Books are fetched, normalized, and scored for confidence.

**Acceptance Scenarios**:
1. **Given** a book with an ISBN, **When** enrichment is triggered, **Then** the system queries OpenLibrary and Google Books in parallel within 3 seconds, normalizes the responses into a canonical metadata schema, and calculates field-level match confidence.
2. **Given** a book without an ISBN, **When** enrichment is triggered, **Then** the system normalizes the title and author from file heuristics and searches OpenLibrary and Google Books, returning top matching candidates.
3. **Given** an academic or technical monograph with a DOI or university imprint, **When** OpenLibrary and Google Books yield low confidence (<0.70), **Then** the system cascades to query CrossRef and arXiv APIs.

---

### User Story 2 - Multimodal LLM Vision Fallback for Obscure or Untagged Books (Priority: P1)

As a digital collector importing scanned PDFs, indie books, or older files with no online ISBN match, I want an AI agent to inspect the book's cover image and first three pages (title page, copyright page, table of contents) using multimodal vision (Google Gemini or local Ollama), so that accurate title, author, publisher, and year are extracted even when online databases fail.

**Why this priority**: Guarantees that obscure, vintage, scanned, or non-commercial books are not left as generic filenames like `scan_001.pdf`.

**Independent Test**: Provide an untagged PDF with only visual text on page 1 (cover) and page 2 (title page); assert that the LLM Vision parser extracts the title, author, and copyright year with >= 85% accuracy and tags the record with extraction confidence.

**Acceptance Scenarios**:
1. **Given** a book where online API lookups return zero results or confidence < 0.70, **When** LLM fallback is engaged, **Then** the system renders the cover and first 3 pages as high-quality images and sends a structured prompt to the configured LLM vision adapter (Gemini or Ollama).
2. **Given** the LLM vision response, **When** parsed by the system, **Then** it validates the JSON schema against the canonical book metadata model, extracting `title`, `authors`, `publisher`, `publication_year`, and `description`.
3. **Given** an offline environment with no cloud API keys, **When** LLM fallback runs, **Then** it automatically routes to local Ollama (`llama3.2-vision` or `qwen2.5`) with zero cloud data transmission.

---

### User Story 3 - Visual Diff Staging & Confidence-Based Human-in-the-Loop Review (Priority: P1)

As a library curator, I want high-confidence matches (>= 0.85) to be automatically applied, while ambiguous or conflicting updates are placed into an ephemeral staging queue with a side-by-side visual diff modal, so that I maintain ultimate authority over my library's catalog without tedious manual review of obvious matches.

**Why this priority**: Constitution Principle III (Agentic Safeguards & Human Authority) mandates that AI automation never silently overwrites human library data without verification of ambiguous fields.

**Independent Test**: Ingest one book with an exact ISBN match (assert auto-applied) and one book with conflicting titles from two sources (assert staged in `.vectors/staging/<proposal_id>.json`); approve the staged proposal via API and verify `metadata.db` and `metadata.opf` are updated.

**Acceptance Scenarios**:
1. **Given** an enrichment result where composite confidence score >= 0.85 and no conflicting fields exist, **When** processed, **Then** the system directly updates Calibre's `metadata.db` and writes updated `metadata.opf` without blocking the user.
2. **Given** an enrichment result with conflicting values (e.g. Source A says "1965", Source B says "1969") or confidence < 0.85, **When** processed, **Then** an ephemeral proposal JSON is stored in `.vectors/staging/<proposal_id>.json` and the book is marked as `NEEDS_REVIEW`.
3. **Given** a staged proposal, **When** the user opens the visual diff review in the web UI, **Then** the UI renders a side-by-side field-by-field comparison (Current vs. Proposed) allowing individual field overrides and a 1-click "Approve" or "Discard".
4. **Given** an approved proposal, **When** accepted, **Then** changes are applied to `metadata.db` and `metadata.opf`, and the staging file is deleted.

---

### User Story 4 - High-Definition Cover Art Selection & Comparison (Priority: P2)

As a collector who values visual library presentation, I want the system to compare original embedded cover artwork with high-resolution artwork discovered online (Google Books, OpenLibrary), displaying them side-by-side with resolution tags so that the sharpest cover can be chosen.

**Why this priority**: High-resolution cover art is essential for the modern 3-pane Calibre UI gallery and grid views.

**Independent Test**: Ingest a book with a low-res thumbnail (150x200); enrich from Google Books with a 1200x1800 cover; assert system detects resolution difference and provides both candidate covers with pixel dimensions and file sizes.

**Acceptance Scenarios**:
1. **Given** a book with an existing embedded cover and an online high-res candidate (>= 600px width), **When** enriched, **Then** both images are staged with dimension metadata (`width`, `height`, `aspect_ratio`).
2. **Given** an auto-enrichment workflow, **When** the online cover is significantly higher quality than the embedded thumbnail, **Then** the online cover is recommended and queued for visual approval or auto-applied per user preference.

---

### User Story 5 - Batch Library Metadata Refresh & Rate-Limited Enqueueing (Priority: P2)

As a library owner adopting an existing Calibre library of 1,000 books, I want to trigger a batch enrichment job that processes books asynchronously with intelligent rate limiting, so that my entire library is enriched without exceeding external API quotas.

**Why this priority**: Allows bulk upgrading of legacy Calibre libraries with minimal user intervention.

**Independent Test**: Trigger batch enrichment on 20 books; assert rate limiting respects provider constraints (e.g. 1 request per second for OpenLibrary), progress is tracked via `x_ingestion_jobs`, and failures are captured without aborting the batch.

**Acceptance Scenarios**:
1. **Given** a request to enrich multiple books, **When** queued, **Then** an async worker processes them with exponential backoff and rate limiting.
2. **Given** intermittent API timeouts or rate limits (HTTP 429), **When** encountered, **Then** the worker pauses with jittered backoff and retries up to 3 times before recording an error in the job log.

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a pluggable `MetadataProvider` interface supporting OpenLibrary, Google Books, CrossRef, and Multimodal LLM adapters.
- **FR-002**: System MUST execute primary providers (OpenLibrary & Google Books) in parallel using `asyncio.gather`.
- **FR-003**: System MUST compute a normalized confidence score (0.00 to 1.00) based on ISBN match, title Levenshtein similarity, author overlap, and publication date consistency.
- **FR-004**: System MUST automatically commit enrichment changes if composite confidence >= 0.85 and no conflicting fields exist.
- **FR-005**: System MUST stage proposals with confidence < 0.85 or conflicting fields as ephemeral JSON files in `<library_root>/.vectors/staging/<proposal_id>.json`.
- **FR-006**: System MUST provide REST endpoints:
  - `POST /api/books/{id}/enrich`: trigger enrichment for a specific book.
  - `GET /api/proposals`: list pending review proposals.
  - `GET /api/proposals/{proposal_id}`: get side-by-side diff details for a proposal.
  - `POST /api/proposals/{proposal_id}/apply`: apply proposed fields (with optional field-level overrides) to `metadata.db` and write updated `metadata.opf`.
  - `POST /api/proposals/{proposal_id}/discard`: delete the staging proposal without modifying the book.
  - `POST /api/enrich/batch`: queue asynchronous batch enrichment across multiple books.
- **FR-007**: System MUST provide a pluggable `LLMClientAdapter` supporting Google Gemini (`gemini-2.0-flash`) and local Ollama (`llama3.2-vision`).
- **FR-008**: System MUST cache external API responses in `<library_root>/.vectors/cache/` (keyed by hash of query parameters) with a 7-day TTL to avoid duplicate upstream API calls.
- **FR-009**: System MUST update both SQLite `metadata.db` (Calibre tables: `books`, `authors`, `tags`, `identifiers`, `comments`) and filesystem `metadata.opf` atomically upon proposal approval.

### Non-Functional Requirements

- **NFR-001 (Portability)**: All staging files, caches, and vector assets MUST reside within `<library_root>/.vectors/`, ensuring the library remains completely self-contained.
- **NFR-002 (Performance)**: Single-book online lookup (OpenLibrary + Google Books) MUST complete in under 3.5 seconds on a standard broadband connection.
- **NFR-003 (Calibre Compatibility)**: All modifications to `metadata.db` MUST adhere strictly to Calibre 7.x table schemas and constraints with zero data loss.
- **NFR-004 (Graceful Degradation)**: If internet access is unavailable, the enrichment pipeline MUST fall back to local Ollama (if configured) or retain existing metadata without failing.

---

## Success Criteria

1. **Enrichment Accuracy**: Over 90% of commercial books with valid ISBNs achieve composite confidence >= 0.85 and enrich automatically without human intervention.
2. **Untagged PDF Recovery**: Scanned or untagged PDFs processed via LLM Vision achieve >= 80% extraction accuracy on Title, Author, and Publication Year.
3. **Zero Data Corruption**: 100% of approved proposals write valid Calibre `metadata.opf` files and SQLite records with zero foreign key violations or data loss.
4. **Interactive Responsiveness**: The side-by-side visual diff API responds in < 100ms.
