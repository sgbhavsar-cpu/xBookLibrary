# Research: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

## 1. OPDS Standards & Ecosystem Benchmark

### OPDS 1.2 (Atom XML)
- **Root Element**: `<feed xmlns="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opds="http://opds-spec.org/2010/catalog">`
- **MIME Type**: `application/atom+xml;profile=opds-catalog;kind=navigation` or `kind=acquisition`.
- **Navigation Feed**: Contains `<entry>` elements representing catalog branches:
  - All Books (`rel="subsection"`)
  - Recent Additions (`rel="http://opds-spec.org/sort/new"`)
  - By Author (`rel="subsection"`)
  - By Taxonomy / Category (`rel="subsection"`)
  - OpenSearch Description (`rel="search"`, `type="application/opensearchdescription+xml"`)
- **Acquisition Feed**: Contains `<entry>` elements representing individual book publications:
  - `<dc:identifier>`: Unique URI (e.g. `urn:xbook:book:{id}`)
  - `<dc:title>`, `<dc:creator>`, `<updated>`
  - `<link rel="http://opds-spec.org/image" href="/covers/{id}.jpg" type="image/jpeg" />`
  - `<link rel="http://opds-spec.org/image/thumbnail" href="/covers/{id}.jpg" type="image/jpeg" />`
  - `<link rel="http://opds-spec.org/acquisition" href="/api/books/{id}/download?format=EPUB" type="application/epub+zip" />`
  - `<link rel="http://opds-spec.org/acquisition" href="/api/books/{id}/download?format=PDF" type="application/pdf" />`

### OPDS 2.0 (Readium JSON)
- **MIME Type**: `application/opds+json`.
- **Structure**:
  - `metadata`: `{"title": "xBookLibrary", "updated": "..."}`
  - `navigation`: Array of Link objects `{ "rel": "self", "href": "...", "type": "...", "title": "..." }`
  - `publications`: Array of Readium Publication Manifests containing `metadata`, `links`, `images`.

### OpenSearch 1.1 Specification
- Root XML: `<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">`
- URL template: `<Url type="application/atom+xml;profile=opds-catalog;kind=acquisition" template="/opds/search?q={searchTerms}" />`

---

## 2. Format Conversion Strategy

### Tier 1: Calibre `ebook-convert` CLI Auto-Detect
- Calibre ships with `ebook-convert <input_file> <output_file> [options]`.
- If `shutil.which("ebook-convert")` is detected, invoke subprocess asynchronously with progress monitoring.
- High-fidelity conversion across MOBI, AZW3, EPUB, PDF, TXT, DOCX.

### Tier 2: Pure-Python Converters (Zero External Dependencies)
1. **TXT / Markdown ➔ EPUB**:
   - Native Python `markdown` + EPUB file assembly using `zipfile` and Open Container Format (OCF) standard or `ebooklib`.
2. **CBZ (Comic Archive) ➔ PDF**:
   - Extracts sequential JPEG/PNG images from ZIP archive into memory, and converts into a single continuous vector/raster PDF using `Pillow` or `pypdf`.
3. **EPUB ➔ TXT / Markdown**:
   - Uses `EPUBParser` (Feature 002) to extract structured chapter HTML/text and writes clean markdown/text output.
4. **MOBI ➔ EPUB (Direct Python Extraction)**:
   - Uses `MOBIParser` PalmDOC and HTML record stream extraction to generate a clean EPUB container.
