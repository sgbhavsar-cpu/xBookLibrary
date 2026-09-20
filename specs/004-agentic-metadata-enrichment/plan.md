# Implementation Plan: Agentic Metadata Enrichment & Multimodal Reconciliation

**Feature Branch**: `004-agentic-metadata-enrichment`  
**Date**: 2026-09-20  
**Spec**: [specs/004-agentic-metadata-enrichment/spec.md](file:///c:/sac/progs/xBookLibrary/specs/004-agentic-metadata-enrichment/spec.md)  
**Data Model**: [specs/004-agentic-metadata-enrichment/data-model.md](file:///c:/sac/progs/xBookLibrary/specs/004-agentic-metadata-enrichment/data-model.md)  
**Contracts**: [specs/004-agentic-metadata-enrichment/contracts/openapi.yaml](file:///c:/sac/progs/xBookLibrary/specs/004-agentic-metadata-enrichment/contracts/openapi.yaml)  

---

## 1. Architecture Overview

Feature 004 implements an intelligent, multi-stage metadata enrichment cascade:

```
[Book / Ingestion Pipeline]
           │
           ▼
[EnrichmentOrchestrator]
   ├── 1. Parallel Fast-Lookup (asyncio.gather)
   │     ├── OpenLibraryProvider
   │     └── GoogleBooksProvider
   │
   ├── 2. Academic / Technical Fallback (if DOI or academic publisher)
   │     └── CrossRefProvider
   │
   └── 3. Multimodal LLM Vision Fallback (if no match or confidence < 0.70)
         └── LiteLLMClientAdapter (Gemini 2.0 Flash / Ollama)
           │
           ▼
[Reconciliation & Safeguards]
   ├── Exact 100% ISBN Match?
   │     ├── YES ──► Auto-Apply to metadata.db & rewrite metadata.opf
   │     └── NO  ──► Stage Ephemeral Proposal in .vectors/staging/<id>.json
   │
   └── Visual Diff Review API (/api/proposals) ──► 1-Click Human Approval
```

---

## 2. Planned Phases

### Phase 1: Setup & Dependencies
- Add `litellm>=1.50.0` to `pyproject.toml` via `uv add litellm`.
- Ensure environment configuration handles `GEMINI_API_KEY`, `OPENAI_API_KEY`, and `OLLAMA_HOST` seamlessly.

### Phase 2: Domain Entities & Ephemeral Staging Storage
- Define `CandidateMetadata`, `CoverCandidate`, `ProposedField`, and `MetadataProposal` in `backend/domain/enrichment.py`.
- Implement `ProposalManager` in `backend/services/proposal_manager.py` to persist and load ephemeral staging JSON files inside `<library_root>/.vectors/staging/`.

### Phase 3: Bibliographic Providers & HTTP Caching
- Implement `MetadataProvider` abstract base class in `backend/providers/base.py`.
- Implement `OpenLibraryProvider` in `backend/providers/openlibrary.py`.
- Implement `GoogleBooksProvider` in `backend/providers/google_books.py` (with high-res zoom=2 cover extraction).
- Implement `CrossRefProvider` in `backend/providers/crossref.py`.
- Implement 7-day TTL file cache in `backend/services/http_cache.py`.

### Phase 4: LiteLLM Multimodal Vision Adapter
- Implement `LiteLLMClientAdapter` in `backend/providers/llm_adapter.py`.
- Render PDF page 1 (cover), page 2 (title page), and page 3 (copyright page) as in-memory base64 JPEG images.
- Issue structured prompt via `litellm.completion` to extract `title`, `authors`, `publisher`, `publication_year`, and `description`.

### Phase 5: Enrichment Orchestrator & Reconciliation Strategy
- Implement `EnrichmentOrchestrator` in `backend/services/enrichment_orchestrator.py`.
- Execute parallel fetch, calculate field comparisons, and enforce strict decision policy (Exact ISBN = auto-apply; Fuzzy/LLM = stage in review queue).
- Apply approved updates to Calibre SQLite tables (`books`, `authors`, `tags`, `comments`, `identifiers`) and call `StorageService.write_metadata_opf()`.

### Phase 6: REST API Endpoints
- Implement `proposals_router.py`:
  - `POST /api/books/{id}/enrich`
  - `GET /api/proposals`
  - `GET /api/proposals/{id}`
  - `POST /api/proposals/{id}/apply`
  - `POST /api/proposals/{id}/discard`
- Mount `proposals_router` in `backend/main.py`.

### Phase 7: Verification & Test Suite
- Unit tests for each provider with mocked HTTP responses (`pytest-asyncio`, `respx`).
- Unit tests for `ProposalManager` file staging and cleanup.
- Contract tests for `/api/books/{id}/enrich` and `/api/proposals`.
- Ruff linting and format checks.
