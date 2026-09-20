# Tasks: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

**Feature**: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine  
**Branch**: `010-opds-server-and-format-conversion`  
**Status**: Ready  

---

## Phase 1: Data Models & Conversion Framework Foundation (Priority: P1)

**Goal**: Define Pydantic domain models for OPDS XML/JSON feeds and conversion jobs.

- [x] T001 Define conversion domain models (`ConversionJob`, `ConversionStatus`, `ConversionRequest`, `ConversionEngineUsed`) in `backend/domain/conversion.py`.
- [x] T002 Define OPDS feed and entry models in `backend/domain/opds.py`.
- [x] T003 Implement unit test suite `tests/unit/test_conversion_domain.py` verifying model validation and status transitions.

---

## Phase 2: OPDS 1.2 & 2.0 Feed Generator (Priority: P1)

**Goal**: Build Atom XML and Readium JSON serialization service for catalog feeds.

- [x] T004 Implement `OPDSService` in `backend/services/opds_service.py` with Atom XML feed builder, Dublin Core elements, and acquisition links.
- [x] T005 Implement OpenSearch 1.1 description generator and query search feed in `backend/services/opds_service.py`.
- [x] T006 Implement OPDS 2.0 Readium JSON catalog serializer in `backend/services/opds_service.py`.
- [x] T007 Implement unit tests `tests/unit/test_opds_generator.py` testing Atom XML validity, MIME types, and entry serialization.

---

## Phase 3: Background Format Conversion Engine (Priority: P2)

**Goal**: Implement tiered format conversion engine (Calibre `ebook-convert` auto-detect + native Python fallback).

- [x] T008 Implement `ConversionService` in `backend/services/conversion_service.py` with Calibre CLI executor and process management.
- [x] T009 Implement native pure-Python converters in `backend/services/converters/`:
  - `TxtToEpubConverter`: Markdown/text to structured EPUB.
  - `CBZToPdfConverter`: Image archive extraction and sequential PDF assembly.
- [x] T010 Implement Calibre storage synchronization upon successful conversion (storing file under `<Author>/<Title> (<id>)/` and updating SQLite `data` table).
- [x] T011 Implement unit tests `tests/unit/test_format_converters.py` testing pure-Python TXT ➔ EPUB and CBZ ➔ PDF conversions.

---

## Phase 4: API Endpoints & Contract Testing (Priority: P1)

**Goal**: Expose FastAPI routers for OPDS feeds and conversion job management.

- [x] T012 Implement `backend/api/opds_router.py` handling `/opds`, `/opds/books`, `/opds/recent`, `/opds/taxonomies`, `/opds/opensearch.xml`, `/opds/search`, and `/api/opds/v2.0`.
- [x] T013 Implement `backend/api/conversion_router.py` handling `POST /api/convert` and `GET /api/convert/jobs/{id}`.
- [x] T014 Register routers in `backend/main.py`.
- [x] T015 Implement contract tests `tests/contract/test_opds_api.py` verifying HTTP responses, headers, and XML payloads.
- [x] T016 Implement contract tests `tests/contract/test_conversion_api.py` verifying asynchronous job submission and polling.

---

## Phase 5: Frontend Integration & E-Reader Experience (Priority: P2)

**Goal**: Connect conversion actions and OPDS feed sharing into the modern web UI.

- [x] T017 Add "Convert Format" button and format selector in `frontend/src/components/DetailInspector.tsx` for non-EPUB/PDF books.
- [x] T018 Add "Copy OPDS Feed URL" quick action button in `frontend/src/components/HeaderToolbar.tsx` with modal instructions for KOReader and Moon+ Reader.
- [x] T019 Update frontend types in `frontend/src/types/index.ts` and API client in `frontend/src/api/client.ts`.

---

## Phase 6: Full Verification & Git Commit (Priority: P3)

**Goal**: Validate full test suite, verify clean build, and commit Feature 010.

- [x] T020 Run `uv run pytest --cov=backend` to verify all backend unit and contract tests pass.
- [x] T021 Run `npm run build` in `frontend/` to verify zero TypeScript errors and production bundle.
- [x] T022 Commit Feature 010 to git.
