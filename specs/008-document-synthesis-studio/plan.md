# Implementation Plan: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature**: 008 Multi-Book Document Synthesis & Knowledge Brief Studio  
**Branch**: `008-document-synthesis-studio`  
**Date**: 2026-09-20  
**Status**: Ready for Implementation  

---

## Technical Context

Feature 008 implements multi-book document synthesis, turning collections of books into structured, citation-backed literature reviews, topic briefs, and executive summaries.
1. **Schema & Persistence**: Table `x_synthesis_documents` in SQLite (`metadata.db`) and markdown files under `<LibraryRoot>/.synthesis/<id>.md`.
2. **Multi-Stage Synthesis Pipeline**:
   - `generate_outline(prompt, template, books)`: Produces structured sections and targeted search terms.
   - `retrieve_section_evidence(keywords, scoped_books)`: Uses `RAGSearchService` over LanceDB to retrieve evidence chunks.
   - `draft_section(section_info, evidence_chunks)`: Synthesizes analytical text with strict inline citations (`[Book Title, Chapter Title]`).
   - `assemble_document(...)`: Merges sections, injects Executive Overview, and generates a structured Bibliography.
3. **Format Exporters**: Markdown, self-contained styled HTML with modern typography, and JSON.
4. **Background Tracking**: Asynchronous job worker support with stage and percent completion.
5. **REST API**: Mounted under `/api/synthesis`.

---

## Constitution Check

- **Principle I: Self-Contained Portable Library Isolation**:
  - *Pass*: Synthesized documents are stored in `<LibraryRoot>/metadata.db` and `<LibraryRoot>/.synthesis/`.
- **Principle II: Clean Architecture**:
  - *Pass*: Domain entities and synthesis logic are decoupled from web routes.
- **Principle IV: Test-First Discipline**:
  - *Pass*: Unit, exporter, and API contract tests written first.
- **Principle V: Multi-Resolution Knowledge & Grounded RAG**:
  - *Pass*: Grounded synthesis with mandatory inline chapter citations and verified bibliographies. Zero hallucinations.

---

## Phase Breakdown

### Phase 1: Foundational Schema & Domain Models (Priority: P1)
- Add `x_synthesis_documents` table to `backend/database/schema.py`.
- Implement domain models in `backend/domain/synthesis.py`.
- Tests: `tests/unit/test_synthesis_domain.py`.

### Phase 2: Multi-Stage Document Synthesis Engine (Priority: P1)
- Implement `DocumentSynthesisService` in `backend/services/document_synthesis_service.py`:
  - Outline generation with sub-questions and keyword extraction.
  - Section-level evidence retrieval using `RAGSearchService`.
  - Analytical section drafting with strict inline citations.
  - Full document assembly with Executive Summary and Bibliography.
- Tests: `tests/unit/test_synthesis_service.py`.

### Phase 3: Exporters & Document Persistence (Priority: P2)
- Implement `SynthesisExporter` in `backend/services/synthesis_exporter.py`:
  - GitHub-flavored Markdown generator.
  - Standalone styled HTML generator with responsive typography and print CSS.
  - Local file persistence under `<LibraryRoot>/.synthesis/<doc_id>.md`.
- Tests: `tests/unit/test_synthesis_exporter.py`.

### Phase 4: REST API Endpoints & Background Jobs (Priority: P3)
- Implement `synthesis_router.py` in `backend/api/synthesis_router.py`.
- Mount `synthesis_router` in `backend/main.py`.
- Contract tests in `tests/contract/test_synthesis_api.py`.

### Phase 5: Polish & Verification
- `ruff check` and `ruff format` verification.
- Full regression test suite execution asserting 100% green tests.
