# Feature Specification: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature Branch**: `008-document-synthesis-studio`  
**Created**: 2026-09-20  
**Status**: Draft  
**Input**: User description: "create library wise RAG so that chat bot agent can answer questions from books of that library or create new document based on that knowledge."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Multi-Book Structured Synthesis Generation (Priority: P1)

As a researcher and avid reader, I want to select multiple books (or a specific bookshelf/category) and generate a comprehensive, structured knowledge brief or literature review on a chosen topic, so that I can synthesize perspectives, compare arguments, and extract actionable insights across different authors without manual copy-pasting.

**Why this priority**: An AI book library must go beyond single-turn question answering; synthesizing cohesive new knowledge documents across collections is the defining high-value research capability.

**Independent Test**: Can be tested by selecting 2 indexed books with overlapping themes, requesting a "Literature Review" document on a central question, and verifying that the generated document produces distinct sections comparing both works with accurate inline citations.

**Acceptance Scenarios**:
1. **Given** 2 or more indexed books in a library, **When** a user requests a topic synthesis document with a title and prompt, **Then** the system formulates an outline, retrieves evidence passages across the selected books, drafts coherent sections, and returns a structured document with an Executive Summary and Bibliography.
2. **Given** a synthesis request scoped to a specific bookshelf or taxonomy tag, **When** executing retrieval, **Then** only books belonging to that bookshelf/tag are queried for evidence.

---

### User Story 2 - Grounded Synthesis with Verifiable Citations (Priority: P2)

As a scholar, I want every factual claim, thesis comparison, and quoted framework in the synthesized document to include verifiable citations referencing exact book titles and chapters, so that the document is authoritative, trustworthy, and free from hallucinations.

**Why this priority**: Unsubstantiated AI claims undermine scholarly and professional work. Grounded citations allow readers to verify claims directly against the source books.

**Independent Test**: Can be tested by asserting that all generated sections contain inline citation tokens (`[Book Title, Chapter Title]`) mapping to a populated bibliography of source books.

**Acceptance Scenarios**:
1. **Given** a generated document, **When** examining any analytical claim or quote, **Then** an inline citation is present referencing the source book and chapter.
2. **Given** a bibliography in the generated document, **When** cross-checked, **Then** every cited item corresponds to a verified book in the library.

---

### User Story 3 - Multi-Format Export & Document Management (Priority: P3)

As a knowledge worker, I want to save synthesized research documents inside the library, view previously generated documents, and export them as GitHub-flavored Markdown or styled HTML, so that I can share them with colleagues or publish them into my personal notes (e.g. Obsidian, Notion).

**Why this priority**: Users need to preserve their research outputs inside their portable Calibre library folder and export them in standardized, publication-ready formats.

**Independent Test**: Can be tested by retrieving a saved synthesis document via API and verifying export endpoints (`?format=markdown` and `?format=html`).

**Acceptance Scenarios**:
1. **Given** a completed synthesis document, **When** requesting an HTML export, **Then** a standalone, beautifully styled HTML document is returned with typographic styles and formatted citations.
2. **Given** a library, **When** listing synthesis documents, **Then** all generated documents are returned with metadata (title, word count, template type, source book count, created timestamp).

---

### User Story 4 - Background Document Synthesis & Progress Tracking (Priority: P4)

As a user generating an in-depth 3,000+ word research brief, I want the generation to run as an asynchronous background job with visible stage progression (e.g. "generating outline" -> "retrieving evidence" -> "drafting section 2 of 4" -> "assembling bibliography"), so that the application remains responsive and I can monitor progress.

**Why this priority**: Multi-stage document synthesis involves multiple LLM and vector retrieval steps that can take 15–45 seconds. Transparent progress keeps the user informed.

**Independent Test**: Can be tested by dispatching a document generation request, receiving a `202 Accepted` with a `job_id`, and polling progress until status reaches `completed`.

**Acceptance Scenarios**:
1. **Given** an asynchronous document generation job, **When** polling its status, **Then** the response provides the current stage and percentage complete.
2. **Given** an unexpected failure in one section, **When** handled, **Then** the job reports the error gracefully without leaving orphan locks.

---

### Edge Cases

- **Conflicting Author Viewpoints**: When two books take contradictory stances on a topic, the synthesis prompt must highlight the disagreement rather than smoothing over differences or picking a side.
- **Irrelevant Books in Scope**: If a user selects 5 books but only 2 discuss the query topic, the retrieval stage must filter out irrelevant texts without hallucinating fake relevance for the remaining 3.
- **Large Book Selections (>20 books)**: Evidence retrieval must cap candidate chunks per section (e.g. top 3 chunks per book or top 10 chunks overall) to avoid prompt window overflow.
- **Offline / Rate Limit Handling**: Exponential backoff on API rate limits with fallback to cached evidence.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support multi-book synthesis scoped to specific `book_ids`, a `bookshelf_id`, or the entire library.
- **FR-002**: System MUST support predefined synthesis templates: `topic_brief`, `literature_review`, `executive_summary`, and `custom_research`.
- **FR-003**: System MUST execute a multi-stage synthesis pipeline: Outline Generation -> Sectional Evidence Retrieval -> Section Drafting -> Assembly & Bibliography.
- **FR-004**: System MUST enforce strict citation grounding: every section MUST contain verifiable citations formatted as `[Book Title, Chapter Title]`.
- **FR-005**: System MUST persist synthesized documents in SQLite (`x_synthesis_documents`) and save the raw Markdown artifact under `<LibraryRoot>/.synthesis/<doc_id>.md`.
- **FR-006**: System MUST export synthesized documents in Markdown, styled HTML, and JSON formats.
- **FR-007**: System MUST provide asynchronous background execution for document synthesis with granular progress updates.
- **FR-008**: System MUST expose REST API endpoints for document generation, listing, retrieval, deletion, and multi-format export.

---

### Key Entities

- **SynthesisDocument**: Represents a completed synthesized research document. Key attributes: `id`, `library_id`, `title`, `template_type`, `topic_prompt`, `outline_json`, `content_markdown`, `sources_json`, `word_count`, `created_at`.
- **SynthesisSection**: An individual section within a synthesized brief. Key attributes: `section_title`, `content`, `cited_sources`.
- **SynthesisSource**: A book referenced in the synthesis. Key attributes: `book_id`, `book_title`, `authors`, `chapters_cited`.
- **SynthesisJob**: Background tracking record. Key attributes: `job_id`, `status`, `stage`, `percent_complete`, `document_id`, `error`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Multi-book synthesis for 2–5 books completes in under 45 seconds under standard LLM response times.
- **SC-002**: 100% of generated factual claims in synthesized sections include inline source citations.
- **SC-003**: Exported HTML documents render cleanly in all modern browsers without external font/CSS CDN dependencies.
- **SC-004**: Incremental document persistence guarantees zero data loss if an export is interrupted.
- **SC-005**: 100% test pass rate across unit, integration, and API contract tests with zero regressions on existing features.

---

## Assumptions

- Source books have been parsed and indexed in LanceDB (via Feature 007).
- If unindexed books are included in the selection, the system can perform lightweight fallback parsing or notify the user to index them.
- Calibre library portability is preserved because `.synthesis/` is stored directly inside the library directory.
