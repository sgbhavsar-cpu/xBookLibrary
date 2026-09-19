<!--
Sync Impact Report:
- Version change: [CONSTITUTION_VERSION] -> 1.0.0
- Ratification: Initial constitution adopted for xBookLibrary.
- Principles established:
  * I. Self-Contained Portable Library Isolation (Calibre-style SQLite + LanceDB per library)
  * II. Clean Architecture & Pluggable Parser Strategy (Full format suite: EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ/CBR)
  * III. Agentic Enrichment & Human-in-the-Loop Safeguards (Multi-source metadata aggregation + diff review)
  * IV. Test-First Discipline (NON-NEGOTIABLE TDD)
  * V. Multi-Resolution Knowledge & Grounded RAG (Tiered summaries + citation-backed QA & synthesis)
  * VI. Modern Premium 3-Pane UI Excellence (Calibre reimagined: dark/light theme, cover grid, inspector & chat drawer)
- Technology Stack & Constraints Defined: FastAPI, React 19 + TypeScript + Vite, LanceDB, SQLite, Gemini API + Ollama.
-->

# xBookLibrary Constitution

## Core Principles

### I. Self-Contained Portable Library Isolation
Every library managed by xBookLibrary MUST be 100% self-contained and portable, adhering to the Calibre folder standard.
- Each library directory MUST contain its own `metadata.db` (SQLite) and `.vectors/` directory (LanceDB index).
- Moving or backing up a library directory MUST preserve all books, covers, metadata, summaries, and vector embeddings without breaking references.
- Central application state MUST only store library registry paths and global user preferences.

### II. Clean Architecture & Pluggable Parser Strategy
The core business and domain logic MUST remain strictly decoupled from external APIs, web frameworks, and storage drivers.
- Ingestion parsers MUST implement a unified `BookParserStrategy` interface.
- From Day 1, the system MUST support the complete format suite: EPUB, PDF, MOBI, AZW3, TXT, DOCX, and Comic archives (CBZ/CBR).
- Extracted book content MUST normalize into standard domain entities: Title, Authors, Identifiers (ISBN/DOI/ASIN), Publication Year, Table of Contents, Chapter Content, and Cover Art.

### III. Agentic Enrichment & Human-in-the-Loop Safeguards
Automated AI agents MUST assist but never silently corrupt or misplace user data.
- Pre-import metadata enrichment MUST query a multi-source aggregator: OpenLibrary API, Google Books API, CrossRef/arXiv for scholarly works, with LLM content extraction fallback (scanning title page, copyright page, and cover).
- AI classification MUST support Dual Taxonomy: standard library classification (BISAC / Dewey Decimal) alongside user-customizable hierarchical genres, dynamic tags, and collections.
- All agent-proposed metadata modifications and file renamings/relocations MUST be presented to the user as a clear visual diff requiring approval before physical disk operations are committed.

### IV. Test-First Discipline (NON-NEGOTIABLE TDD)
Quality and stability MUST be guaranteed through rigorous automated testing.
- Test-Driven Development (TDD) is mandatory for domain logic, parsers, metadata aggregators, and RAG chunking pipelines.
- Unit and contract tests MUST be written and verified to fail before implementation code is written.
- All pull requests and feature implementations MUST maintain green test suites with strict type checking.

### V. Multi-Resolution Knowledge & Grounded RAG
The intelligence layer MUST turn books into actionable, verifiable knowledge.
- The summarization engine MUST produce tiered, multi-resolution summaries:
  1. *Executive Snapshot*: 2-minute overview with core premise and thesis.
  2. *Chapter Synthesis*: Section-by-section breakdown preserving narrative or argumentative progression.
  3. *Conceptual Index*: Frameworks, core models, key quotes, and actionable takeaways.
- The Library-Wise RAG system (LanceDB embedded) MUST use hierarchical chunking (preserving chapter/section context) and hybrid retrieval.
- The Chatbot and Document Synthesizer MUST enforce strict grounding: every factual statement in answers or generated documents MUST include exact chapter/page citations. Hallucinations are considered critical bugs.

### VI. Modern Premium 3-Pane UI Excellence
The user interface MUST deliver a state-of-the-art, polished, and delightful user experience.
- The layout MUST feature a responsive modern 3-pane architecture:
  1. *Left Sidebar*: Library switcher, hierarchical category tree, author browser, and tag filter.
  2. *Center Stage*: High-density data table or visual cover grid with smooth sorting, instant fuzzy filtering, and multi-select actions.
  3. *Right Slide-Out Inspector*: Tabbed inspector housing book metadata diffs, multi-resolution summaries, built-in EPUB/PDF reader, and a live conversational RAG chat drawer.
- The design system MUST support curated dark and light themes, modern typography (Inter / Outfit), fluid micro-animations, and glassmorphism accents.

## Technology Stack & Architectural Constraints

- **Backend Framework**: Python 3.12+ with FastAPI, Pydantic v2 schemas, SQLAlchemy 2.0 (async), and `uv` package management.
- **Relational Storage**: Embedded SQLite per library (`metadata.db`) with Calibre-compatible `metadata.opf` export capability.
- **Vector Storage**: LanceDB embedded (Apache Arrow-based vector store stored under `<Library>/.vectors/`).
- **AI & Embedding Engine**: Hybrid multi-provider architecture: Google Gemini API (`google-genai` SDK with `gemini-2.5-flash` / `text-embedding-004`) as primary high-speed cloud engine, with local fallback to Ollama.
- **Frontend Framework**: React 19, TypeScript, Vite, Modern CSS / TailwindCSS tokens, Lucide icons, Virtualized grids for 10,000+ book performance, and packaging readiness for Tauri desktop deployment.
- **File System Organization**: Deterministic Calibre layout:
  ```
  <LibraryRoot>/
  ├── metadata.db
  ├── .vectors/
  └── <Author>/
      └── <Title> (<Year>)/
          ├── cover.jpg
          ├── metadata.opf
          ├── book.<ext>
          └── summary.json
  ```

## Development Workflow & Quality Gates

1. **Spec-Driven Lifecycle**:
   - Every feature MUST begin with a specification (`/speckit-specify`), undergo ambiguity de-risking (`/speckit-clarify`), technical blueprinting (`/speckit-plan`), checklist auditing (`/speckit-checklist`), atomic task breakdown (`/speckit-tasks`), and test-driven implementation (`/speckit-implement`).
2. **Code Quality Standards**:
   - Python code MUST pass `ruff check` and `ruff format` with zero errors.
   - Type hints are mandatory across all Python service signatures and Pydantic models.
   - Frontend TypeScript MUST pass `tsc --noEmit` with zero type errors.
3. **Continuous Verification**:
   - Tests MUST be automated using `pytest` for Python and `vitest` for the frontend.

## Governance

- The Constitution is the supreme design and architectural authority for xBookLibrary.
- Any architectural change, technology deviation, or principle modification requires an explicit amendment to this document with a semantic version increment.
- Semantic Versioning Rules:
  - **MAJOR**: Incompatible principle removal or architectural redefinition.
  - **MINOR**: Addition of new principles, formats, or substantial capabilities.
  - **PATCH**: Wording improvements, clarifications, or non-functional refinements.

**Version**: 1.0.0 | **Ratified**: 2026-09-20 | **Last Amended**: 2026-09-20
