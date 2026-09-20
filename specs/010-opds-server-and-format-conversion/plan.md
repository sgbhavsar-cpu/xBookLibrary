# Implementation Plan: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

## 1. Architectural Strategy

- **OPDS Service Layer (`backend/services/opds_service.py`)**:
  - Generates valid Atom 1.0 XML compliant with the OPDS 1.2 Catalog Specification.
  - Implements OpenSearch 1.1 template generation and XML serialization.
  - Implements OPDS 2.0 Readium JSON catalog serialization.
  - Generates navigation feeds (catalogs, categories, authors) and acquisition feeds (with covers and downloads).

- **Format Conversion Engine (`backend/services/conversion_service.py`)**:
  - Tiered conversion coordinator:
    - Checks for Calibre's `ebook-convert` executable on `PATH`.
    - Native Python converters:
      - `CBZToPdfConverter`: Extracts images from CBZ ZIP archives, processes with `Pillow`/`pypdf`, compiles into PDF.
      - `TxtToEpubConverter`: Parses markdown/text, structures chapters, compiles into valid EPUB with OCF container.
      - `EpubToPdfConverter`: Converts EPUB text/chapters into printable PDF format.
  - Attaches converted output files back to the book's Calibre directory and registers the format in SQLite `data` table.

- **FastAPI Routers**:
  - `backend/api/opds_router.py`: Handles `/opds`, `/opds/books`, `/opds/recent`, `/opds/taxonomies`, `/opds/opensearch.xml`, `/opds/search`, and `/api/opds/v2.0`.
  - `backend/api/conversion_router.py`: Handles `POST /api/convert` and `GET /api/convert/jobs/{id}`.

- **Frontend Integration**:
  - Add "Convert Format" button in `DetailInspector.tsx` for books with formats like MOBI or CBZ that don't yet have an EPUB or PDF.
  - Show conversion progress modal or indicator.
  - Display the OPDS feed URL in `HeaderToolbar.tsx` or library settings modal with a quick "Copy OPDS Feed URL" button for e-readers.

---

## 2. Test-Driven Development (TDD) Strategy

- **Contract Tests**:
  - `tests/contract/test_opds_api.py`: Verify `/opds` returns valid Atom XML, `/opds/opensearch.xml` returns OpenSearch XML, and `/opds/search` filters correctly.
  - `tests/contract/test_conversion_api.py`: Verify `POST /api/convert` returns 202 Accepted and job tracking returns accurate progress.
- **Unit Tests**:
  - `tests/unit/test_opds_generator.py`: Verify XML generation, Dublin Core tags, acquisition links, and pagination.
  - `tests/unit/test_format_converters.py`: Verify pure-Python conversion of TXT ➔ EPUB and CBZ ➔ PDF.
