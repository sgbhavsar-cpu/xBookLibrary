# Implementation Plan: Multi-Resolution AI Book Summarization Engine

**Branch**: `006-book-summarization-engine` | **Date**: 2026-09-20 | **Spec**: [specs/006-book-summarization-engine/spec.md](file:///c:/sac/progs/xBookLibrary/specs/006-book-summarization-engine/spec.md)

**Input**: Multi-resolution AI book summarization engine producing tiered summaries (Executive Snapshot, Chapter-by-Chapter breakdown, Conceptual Index, and Actionable Takeaways) with local portable storage (`summary.json`) and database indexing.

---

## Summary

Feature 006 introduces a multi-resolution AI book summarization engine capable of synthesizing full-length books into structured tiers: a 2-minute Executive Snapshot, a granular Chapter-by-Chapter synthesis, and a Conceptual Index with mental models and quotes. It employs a hierarchical map-reduce pipeline with chapter-aware parsing, dual persistence (in physical `<Author>/<Title> (<Year>)/summary.json` and SQLite `x_summaries`), background job execution via `JobWorker`, and multiple export formatters (Markdown, HTML, JSON, and Calibre OPF `<dc:description>` sync).

---

## Technical Context

**Language/Version**: Python 3.12.10  
**Primary Dependencies**: FastAPI 0.115+, Pydantic 2.10+, aiosqlite 0.20+, litellm 1.100+  
**Storage**: Embedded SQLite 3 (`metadata.db` table `x_summaries`), local filesystem (`summary.json`), Calibre `metadata.opf`  
**Testing**: pytest 9.1+, pytest-asyncio, respx, pytest-cov  
**Target Platform**: Windows / Linux / macOS (Calibre 7.x compatible)  
**Project Type**: Core Backend Web Service & Local Storage  
**Performance Goals**: < 50ms for cached summary retrieval, streaming progress events for background chapter summarization  
**Constraints**: 100% Calibre 7.x table compatibility; zero data loss; portable folder layout  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Self-Contained Portable Library Isolation)**: PASSED. Summaries are stored in `<LibraryRoot>/<Author>/<Title> (<Year>)/summary.json` alongside `book.<ext>` and `metadata.opf`, plus cached in SQLite `x_summaries`. Moving a library folder retains all summaries.
- **Principle II (Clean Architecture & Pluggable Parsers)**: PASSED. Summarizer extracts chapter text using existing `BookParserStrategy` implementations without coupling to format details.
- **Principle III (Agentic Enrichment & Human-in-the-Loop Safeguards)**: PASSED. Regenerations, prompt overrides, and Calibre metadata syncing are user-driven and non-destructive.
- **Principle IV (Test-First Discipline - TDD)**: PASSED. Complete unit, integration, and contract test suites written and verified before service implementation.
- **Principle V (Multi-Resolution Knowledge & Grounded RAG)**: PASSED. Full compliance with Tier 1 (Executive Snapshot), Tier 2 (Chapter Synthesis), and Tier 3 (Conceptual Index).

---

## Project Structure

### Documentation (this feature)

```text
specs/006-book-summarization-engine/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Architecture decisions & trade-offs
├── data-model.md        # Pydantic entities and SQL DDL
├── contracts/
│   └── openapi.yaml     # REST API endpoint contracts
└── tasks.md             # Work tasks breakdown
```

### Source Code

```text
backend/
├── api/
│   └── summaries_router.py            # REST endpoints for summaries, exports, and sync
├── database/
│   └── schema.py                      # Extension table x_summaries in metadata.db
├── domain/
│   └── summary.py                     # BookSummary, ExecutiveSnapshot, ChapterSummary, etc.
└── services/
    ├── summarization_service.py       # Map-reduce pipeline, LLM prompt engineering, dual-storage
    └── summary_exporter.py            # Markdown, HTML, JSON formatters, Calibre OPF sync

tests/
├── contract/
│   └── test_summaries_api.py          # API contract tests for endpoints
└── unit/
    ├── test_summarization_service.py  # Map-reduce, chapter extraction, prompt formatting
    ├── test_summary_storage.py        # summary.json & SQLite x_summaries persistence
    └── test_summary_exporter.py       # Markdown/HTML formatting and Calibre OPF sync
```
