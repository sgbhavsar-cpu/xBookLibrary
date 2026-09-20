# Implementation Plan: AI Classification & Taxonomy Sorting

**Branch**: `005-ai-classification-sorting` | **Date**: 2026-09-20 | **Spec**: [specs/005-ai-classification-sorting/spec.md](file:///c:/sac/progs/xBookLibrary/specs/005-ai-classification-sorting/spec.md)

**Input**: Feature specification from `/specs/005-ai-classification-sorting/spec.md`

---

## Summary

Feature 005 adds automatic bibliographic classification (BISAC Subject Codes and Dewey Decimal numbers) alongside a user-customizable hierarchical taxonomy tree and virtual bookshelves. It uses `LiteLLMClientAdapter` for zero-shot structured classification with an embedded offline keyword heuristic fallback. High-confidence classifications (>= 0.85) auto-apply tags and categories, while low-confidence classifications stage visual diff proposals in `.vectors/staging/` before writing to SQLite and `metadata.opf`.

---

## Technical Context

**Language/Version**: Python 3.12.10  
**Primary Dependencies**: FastAPI 0.115+, Pydantic 2.10+, aiosqlite 0.20+, litellm 1.100+  
**Storage**: SQLite 3 (`metadata.db` isolated extension tables `x_classifications`, `x_taxonomies`, `x_bookshelves`, `x_books_taxonomies_link`, `x_books_bookshelves_link`), Calibre `metadata.opf` XML  
**Testing**: pytest 9.1+, pytest-asyncio, respx, coverage  
**Target Platform**: Windows / Linux / macOS (Calibre 7.x compatible)  
**Project Type**: Core Backend Web Service & Local Library Storage  
**Performance Goals**: < 2.5s for cached/offline classification, < 7s with LLM extraction  
**Constraints**: 100% Calibre 7.x table compatibility; zero data loss; offline functional  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Self-Contained Portable Library Isolation)**: PASSED. All classification records, category trees, and virtual bookshelf links reside inside the target library's `metadata.db` and `.vectors/` cache.
- **Principle II (Clean Architecture & Pluggable Parsers)**: PASSED. Classifier engine consumes normalized `Book` entities and samples TOC/content via established parser strategies.
- **Principle III (Agentic Enrichment & Human-in-the-Loop Safeguards)**: PASSED. Dual taxonomy (BISAC + DDC) + custom taxonomy. Low confidence (< 0.85) requires explicit user approval via staging proposals.
- **Principle IV (Test-First Discipline - TDD)**: PASSED. Complete unit and contract test suites written and verified before implementation.

---

## Project Structure

### Documentation (this feature)

```text
specs/005-ai-classification-sorting/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Architecture decisions & trade-offs
├── data-model.md        # Pydantic entities and SQL DDL
├── contracts/
│   └── openapi.yaml     # REST API endpoint contracts
└── tasks.md             # Work tasks breakdown (to be generated next)
```

### Source Code

```text
backend/
├── api/
│   └── taxonomies_router.py           # REST endpoints for classification, categories, shelves
├── data/
│   └── bisac_ddc_reference.py         # Embedded standard taxonomy dictionary (offline fallback)
├── database/
│   └── schema.py                      # Extension tables for classifications & bookshelves
├── domain/
│   └── classification.py              # ClassificationResult, TaxonomyNode, Bookshelf
└── services/
    ├── classification_service.py      # LLM + offline heuristic classification orchestrator
    └── taxonomy_service.py            # Hierarchical taxonomy tree and bookshelf operations

tests/
├── contract/
│   └── test_taxonomies_api.py         # Contract tests for classification & taxonomy endpoints
└── unit/
    ├── test_classification_service.py # Unit tests for BISAC/DDC assignment & offline fallback
    └── test_taxonomy_service.py       # Unit tests for hierarchy CRUD & bookshelf assignment
```
