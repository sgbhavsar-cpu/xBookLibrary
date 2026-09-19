# Implementation Plan: Core Library Model, Calibre Storage & Multi-Format Ingestion Strategy

**Branch**: `001-core-library-ingestion` | **Date**: 2026-09-20 | **Spec**: [specs/001-core-library-ingestion/spec.md](file:///c:/sac/progs/xBookLibrary/specs/001-core-library-ingestion/spec.md)

## Summary

This feature establishes the foundational data, storage, and ingestion layer of xBookLibrary. It implements a fully Calibre-compatible library architecture with portable per-library SQLite storage (`metadata.db`), zero-copy in-place adoption of existing Calibre directories, pluggable parser strategies covering the full format suite (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ/CBR), smart multi-format deduplication/merging, an asynchronous background watcher, and a high-performance FastAPI REST API.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Pydantic v2, SQLAlchemy 2.0 (async SQLite), `uv`, `watchfiles`, `ebooklib`, `pypdf`, `pypdfium2`, `python-docx`  
**Storage**: Embedded SQLite per library (`metadata.db`) + local filesystem folder hierarchy (`<LibraryRoot>/<Author>/<Title> (<Year>)/`)  
**Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (API testing)  
**Target Platform**: Windows, macOS, Linux (Cross-platform local server accessible via web browser and packaging-ready for Tauri)  
**Project Type**: Web-first service (FastAPI backend + REST endpoints + async job worker)  
**Performance Goals**: < 2.0s ingestion per book for EPUB/PDF; in-place Calibre adoption of 1,000 books in < 5.0s  
**Constraints**: 100% Calibre `metadata.db` backward compatibility; deterministic file path sanitization (< 240 chars, no invalid OS characters); strict TDD for all parsers  
**Scale/Scope**: Up to 50,000 books per library without UI or SQLite query degradation  

## Constitution Check

*GATE: All principles from xBookLibrary Constitution v1.0.0 verified.*

- **Principle I: Self-Contained Portable Library Isolation**  
  *PASS*: Each library folder holds its own `metadata.db` and `.vectors/` directory. Moving the library folder preserves 100% of data.
- **Principle II: Clean Architecture & Pluggable Parser Strategy**  
  *PASS*: The `BookParserStrategy` abstract base class isolates format parsing (EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ/CBR) behind a uniform `ParsedBookPayload` contract.
- **Principle III: Agentic Enrichment & Human-in-the-Loop Safeguards**  
  *PASS*: Local parsers extract rich text samples, TOC, and cover images to feed downstream agent enrichment without modifying raw source files prematurely.
- **Principle IV: Test-First Discipline (NON-NEGOTIABLE TDD)**  
  *PASS*: All parser implementations and Calibre adoption routines will have red-failing unit tests before code implementation.
- **Principle V: Multi-Resolution Knowledge & Grounded RAG**  
  *PASS*: Ingestion extracts full hierarchical TOC nodes and sample text required for future tiered summaries and LanceDB vector indexing.
- **Principle VI: Modern Premium 3-Pane UI Excellence**  
  *PASS*: REST API provides structured endpoints for high-density book grids, cover streaming, and real-time ingestion job tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-core-library-ingestion/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Research on Calibre schema & parser libraries
├── data-model.md        # Relational SQLite schema & extension tables
├── quickstart.md        # Testing and execution guide
└── contracts/
    ├── openapi.yaml     # OpenAPI 3.1 REST API specification
    └── parsers.py       # Python domain contracts for book parsers
```

### Source Code Architecture

```text
backend/
├── pyproject.toml
├── main.py                     # FastAPI application entry point
├── config.py                   # Global configuration & registry (~/.xbooklibrary/config.json)
├── domain/                     # Core domain entities & interfaces
│   ├── entities.py             # Book, Author, Format, Identifier, TocNode
│   └── parsers.py              # BookParserStrategy & ParsedBookPayload contracts
├── parsers/                    # Pluggable parser strategy implementations
│   ├── base.py                 # Abstract parser base
│   ├── epub_parser.py          # EPUB parser (ebooklib + lxml)
│   ├── pdf_parser.py           # PDF parser (pypdf + pypdfium2 cover rendering)
│   ├── mobi_parser.py          # MOBI/AZW3 parser (PalmDOC / EXTH records)
│   ├── comic_parser.py         # CBZ/CBR parser (ComicInfo.xml + cover image)
│   ├── docx_parser.py          # DOCX parser (python-docx)
│   └── text_parser.py          # TXT / Markdown parser (chardet)
├── services/                   # Application services
│   ├── library_manager.py      # Library creation, switching, and Calibre in-place adoption
│   ├── storage_service.py      # Calibre folder layout, path sanitizer, cover & OPF writer
│   ├── ingestion_service.py    # Ingestion pipeline, multi-format merging & deduplication
│   └── watcher_service.py      # Background directory watcher (watchfiles)
├── database/                   # Persistence layer
│   ├── connection.py           # Dynamic per-library SQLite engine & session factory
│   └── schema.py               # Calibre schema + x_ extension tables
└── api/                        # FastAPI routers & controllers
    ├── libraries_router.py     # /api/libraries
    ├── books_router.py         # /api/books
    └── jobs_router.py          # /api/jobs

tests/
├── conftest.py                 # Pytest fixtures, mock libraries, temp directories
├── fixtures/                   # Sample test files (.epub, .pdf, .mobi, .cbz, .docx, .txt)
├── unit/
│   ├── test_path_sanitizer.py
│   ├── test_calibre_adoption.py
│   ├── test_parsers.py
│   └── test_format_merging.py
└── integration/
    └── test_ingestion_api.py
```

## Implementation Phases

### Phase 1: Foundation & Parser TDD
1. Setup Python `pyproject.toml` with `uv`, defining all core dependencies.
2. Build domain models (`entities.py`) and abstract parser contracts (`domain/parsers.py`).
3. Implement unit test suite with mock sample files for all 7 formats.
4. Implement concrete parsers: `EpubParser`, `PdfParser`, `MobiParser`, `ComicParser`, `DocxParser`, `TextParser`.
5. Verify green test runs across all parsers.

### Phase 2: Storage & Calibre In-Place Adoption
1. Implement `storage_service.py` with filename/path sanitization, Calibre directory layout generator, cover optimizer, and `metadata.opf` writer.
2. Implement `database/schema.py` and `database/connection.py` supporting dynamic per-library SQLite connections.
3. Implement `library_manager.py` with in-place Calibre `metadata.db` introspection and adoption.
4. Test library creation, portability, and zero-copy adoption.

### Phase 3: Ingestion Pipeline & Deduplication
1. Implement `ingestion_service.py` with SHA-256 byte deduplication and smart multi-format merging.
2. Implement asynchronous ingestion worker and job tracking (`x_ingestion_jobs`).
3. Implement `watcher_service.py` with `watchfiles` for automated directory scanning.

### Phase 4: REST API & Integration Verification
1. Implement FastAPI routes: `/api/libraries`, `/api/books`, `/api/jobs`.
2. Implement cover streaming endpoint (`/api/books/{id}/cover`).
3. Add integration test suite validating end-to-end multipart upload, parsing, and database queries.
