# Feature Specification: Multi-Resolution AI Book Summarization Engine

**Feature**: `006-book-summarization-engine`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: Multi-resolution AI book summarization engine producing tiered summaries (Executive Snapshot, Chapter-by-Chapter breakdown, Conceptual Index, and Actionable Takeaways) with local portable storage (`summary.json`) and database indexing.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Resolution Summary Generation (Priority: P1)

As a reader or researcher, I want the library system to generate multi-resolution, structured summaries of any imported book so that I can quickly understand the book's core premise, chapter-by-chapter progression, and key concepts at different depths.

**Why this priority**: Core value proposition. Readers need fast overviews (2 minutes) as well as deep chapter-by-chapter analytical reference notes without manually reading or searching through hundreds of pages.

**Independent Test**: Can be tested by triggering summarization on a multi-chapter book (e.g., EPUB or PDF) and verifying the generated output contains:
1. An Executive Snapshot (thesis, target audience, core arguments).
2. A Chapter Synthesis (sequential breakdown per chapter/section).
3. A Conceptual Index (frameworks, core mental models, actionable takeaways).

**Acceptance Scenarios**:

1. **Given** an ingested book with chapters in the active library,  
   **When** the user requests a multi-resolution summary,  
   **Then** the system produces a structured summary with Executive Snapshot, Chapter Outlines, and Key Concepts, and records generation metrics (model used, token count, generation duration).
2. **Given** a book that only has raw text without an explicit Table of Contents,  
   **When** summarization is requested,  
   **Then** the system automatically detects logical section boundaries or breaks into uniform semantic segments, generating section-level summaries seamlessly.

---

### User Story 2 - Calibre-Isolated Portability & Instant Cache Retrieval (Priority: P2)

As a library owner who synchronizes and backs up book collections across computers, I want summaries to be stored both inside the book's directory (`summary.json`) and in the library's `metadata.db` database so that summaries travel with the physical book files and load instantaneously without re-calling the LLM.

**Why this priority**: Adheres to Constitution Principle I (Self-Contained Portable Library Isolation). Summary data must never be locked in an ephemeral cache or centralized database; if a library folder is copied to a flash drive or another PC, the summaries must remain intact.

**Independent Test**: Can be tested by generating a summary, verifying that `summary.json` is created in `<Library>/<Author>/<Title> (<Year>)/summary.json`, verifying `x_summaries` table in `metadata.db` has the record, and confirming subsequent summary requests return cached data in under 50ms without invoking the AI engine.

**Acceptance Scenarios**:

1. **Given** a generated summary for a book,  
   **When** the summarization process finishes,  
   **Then** the summary is saved to physical disk as `<Author>/<Title> (<Year>)/summary.json` and inserted into `x_summaries` in `metadata.db`.
2. **Given** an existing `summary.json` in a book's folder during library scan/adoption,  
   **When** the library is opened or ingested,  
   **Then** the system imports the summary into `metadata.db` without needing to re-summarize.
3. **Given** an already summarized book,  
   **When** a user views the book's summary,  
   **Then** the cached summary is served immediately from database/disk with zero LLM API calls.

---

### User Story 3 - Asynchronous Progress & Long-Book Processing (Priority: P3)

As a reader importing large volumes or academic textbooks (100,000+ words), I want summarization to run in the background with real-time chapter progress updates so that the application remains responsive and I can monitor processing status.

**Why this priority**: Processing 20–50 chapters through an LLM can take from 30 seconds to several minutes depending on model and book size. A blocking synchronous call would freeze the user interface or cause HTTP request timeouts.

**Independent Test**: Can be tested by enqueuing a large book summarization task, polling or streaming job status via `/api/jobs/{job_id}`, and observing progress increment chapter by chapter until completion.

**Acceptance Scenarios**:

1. **Given** a user initiates summarization on a large book,  
   **When** the job begins,  
   **Then** a job record is returned with status `running`, and progress updates report current chapter number and percentage completed.
2. **Given** a running summarization job,  
   **When** a chapter fails due to transient LLM rate-limiting,  
   **Then** the system retries with exponential backoff and continues processing subsequent chapters without failing the entire book.

---

### User Story 4 - Summary Customization, Regeneration & Multi-Format Export (Priority: P4)

As a researcher or student, I want to customize summary parameters (focus on specific topics, adjust detail level) and export the summary to Markdown, JSON, or formatted HTML, and optionally sync the executive summary into Calibre's book description.

**Why this priority**: Flexibility for varied user workflows (exporting to Obsidian/Logseq notes, printing cheat sheets, or enhancing Calibre metadata).

**Independent Test**: Can be tested by submitting custom summarization instructions (e.g. "Focus on technical architecture and code patterns"), regenerating the summary, exporting as Markdown, and syncing to Calibre `comments`/`<dc:description>`.

**Acceptance Scenarios**:

1. **Given** an existing summary,  
   **When** the user provides custom prompt instructions and clicks "Regenerate",  
   **Then** the system updates the summary according to the specified instructions, updates `summary.json`, and records the custom prompt in the summary metadata.
2. **Given** a generated summary,  
   **When** the user requests a Markdown or HTML export,  
   **Then** the system formats the tiered summary into clean, human-readable Markdown or styled HTML document ready for download or copy-to-clipboard.

---

### Edge Cases

- **Empty or DRM-Protected Text**: If a book format cannot be parsed for text content (e.g., image-only PDF without OCR or DRM encryption), the system clearly reports that text extraction is unavailable and offers to fall back to bibliographic metadata/description summarization.
- **Ultra-Short Book or Article**: If a book has fewer than 2,000 words total, the system collapses chapter synthesis and executive summary into a unified single-pass summary rather than creating artificial 1-sentence chapters.
- **Massive Omnibuses (1,000+ Pages)**: When processing extremely long books, the chapter-level map-reduce pipeline processes chapters sequentially or in small concurrency batches (e.g., concurrency=3) to respect provider rate limits.
- **Model Disconnection / Offline Mode**: If no internet access or API key is available and Ollama is running locally, the system routes summarization to local Ollama; if neither is available, it gracefully returns a descriptive error with configuration guidance.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract structured text by chapter or semantic section using `BookParserStrategy` for all supported formats (EPUB, PDF, MOBI, DOCX, TXT).
- **FR-002**: System MUST produce an **Executive Snapshot** containing: One-Sentence Hook, Core Thesis, Target Audience, 3–5 Primary Takeaways, and Estimated Reading Time.
- **FR-003**: System MUST produce a **Chapter Synthesis** containing: Chapter Title, Sequential Index, Summary Narrative, Key Examples/Arguments, and Chapter Key Takeaway.
- **FR-004**: System MUST produce a **Conceptual Index** containing: Core Mental Models/Frameworks, Direct Notable Quotes (with chapter references), and Practical Applications/Action Items.
- **FR-005**: System MUST store generated summaries in physical file `<LibraryRoot>/<Author>/<Title> (<Year>)/summary.json` adhering to portable Calibre conventions.
- **FR-006**: System MUST persist summary records in SQLite table `x_summaries` in `metadata.db` with columns for fast retrieval, full-text search, and versioning.
- **FR-007**: System MUST support background asynchronous execution with job tracking (`status`, `progress_percent`, `current_chapter`, `total_chapters`).
- **FR-008**: System MUST support user-driven regeneration with customizable prompts, focus areas, and resolution levels.
- **FR-009**: System MUST support exporting summaries to formatted Markdown, JSON, and HTML.
- **FR-010**: System MUST provide an option to sync the executive summary into Calibre's standard `comments` column and `metadata.opf` `<dc:description>` tag without corrupting existing user notes.

---

### Key Entities

- **BookSummary**: Root domain model holding:
  - `book_id`: Identifier of the associated book.
  - `executive_snapshot`: `ExecutiveSnapshot` object.
  - `chapters`: List of `ChapterSummary` objects.
  - `conceptual_index`: `ConceptualIndex` object.
  - `metadata`: `SummaryMetadata` object (model name, generated_at, duration_seconds, word_count, prompt_version).
- **ExecutiveSnapshot**:
  - `hook`: Engaging one-sentence overview.
  - `core_thesis`: Central argument or premise of the book.
  - `target_audience`: Intended readership.
  - `key_arguments`: List of 3–5 overarching arguments.
  - `estimated_reading_time_minutes`: Estimated minutes to read full book.
- **ChapterSummary**:
  - `chapter_index`: Sequential chapter number (1-based).
  - `chapter_title`: Name/heading of the chapter.
  - `summary`: Narrative synthesis of the chapter.
  - `key_takeaways`: Bulleted key takeaways.
  - `important_quotes`: List of quotes referenced in this chapter.
- **ConceptualIndex**:
  - `frameworks`: List of named frameworks or models introduced in the book.
  - `key_takeaways`: Overarching actionable takeaways.
  - `quotable_moments`: Highlighted memorable quotes with chapter attribution.
  - `action_items`: Practical exercises, advice, or steps.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Cached summaries load in the user interface and API in under 50ms.
- **SC-002**: Chapter-by-chapter summarization maintains 100% chapter fidelity without skipping chapters in books with standard Tables of Contents.
- **SC-003**: 100% of generated summaries are verified to exist on physical disk (`summary.json`) and in SQLite (`x_summaries`).
- **SC-004**: System successfully processes books ranging from short essays (5,000 words) to extensive volumes (250,000 words) without running out of memory or timing out.
- **SC-005**: All generated Markdown and HTML exports conform to clean formatting standards with zero raw JSON leakage.

---

## Assumptions

- Users have configured an LLM provider (Google Gemini API via `GEMINI_API_KEY` or local Ollama) as supported by `LiteLLMClientAdapter`.
- Books ingested into xBookLibrary have readable text extracted by our format parsers (EPUB, PDF, DOCX, TXT, MOBI).
- Chapter titles and hierarchies extracted by `backend/parsers/` will serve as the structural backbone for chapter-level synthesis; where missing, the engine falls back to uniform token chunking.
