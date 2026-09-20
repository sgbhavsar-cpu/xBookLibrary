# UI to Backend REST API Contract: 009 Modern Web UI

This document details all REST endpoints consumed by the React 19 web application.

---

## 1. Libraries & Workspace Management
- `GET /api/libraries`: List adopted and native libraries.
- `POST /api/libraries/create`: Create a new Calibre library.
- `POST /api/libraries/adopt`: Adopt an existing Calibre library.
- `POST /api/libraries/{id}/switch`: Switch active workspace library.

---

## 2. Catalog & Books
- `GET /api/books?library_id={id}&page={n}&limit={m}&query={q}`: Paginated book list.
- `GET /api/books/{id}`: Detailed book metadata, available formats, and classification.
- `GET /covers/{book_id}.jpg`: High-res cover image stream with caching.
- `GET /api/books/{id}/download/{format}`: Stream EPUB/PDF file for reading or downloading.
- `POST /api/books/upload`: Ingest EPUB/PDF/MOBI/CBZ files via multipart form.

---

## 3. Metadata Proposals (Feature 004)
- `POST /api/books/{id}/enrich`: Run agentic metadata enrichment across OpenLibrary, Google Books, Crossref.
- `GET /api/proposals`: List pending metadata proposals with diff previews.
- `POST /api/proposals/{id}/apply`: Apply proposal into Calibre database and update OPF.
- `POST /api/proposals/{id}/reject`: Discard proposal.

---

## 4. Taxonomies & Classifications (Feature 005)
- `GET /api/taxonomies/tree`: Retrieve hierarchical taxonomy tree with book counts.
- `GET /api/books/{id}/classification`: Retrieve BISAC, DDC codes, confidence, and reasoning.
- `POST /api/taxonomies`: Create custom taxonomy node.
- `PUT /api/books/{id}/taxonomy`: Assign book to taxonomy path.

---

## 5. Multi-Resolution Summaries (Feature 006)
- `GET /api/books/{id}/summary`: Fetch executive summary, detailed summary, key takeaways, and chapter summaries.
- `POST /api/books/{id}/summary/generate`: Trigger AI summarization.
- `GET /api/books/{id}/summary/export?format={md|html|json}`: Export formatted summary.

---

## 6. Library RAG Hybrid Search & Chat (Feature 007)
- `POST /api/books/{id}/index`: Index book chunks into LanceDB vector store.
- `GET /api/libraries/{id}/index/status`: Get library vector indexing progress and chunk metrics.
- `POST /api/libraries/{id}/search`: Execute hybrid dense + BM25 search across book chunks.
- `POST /api/chat/sessions`: Create chat session (library-scoped or book-scoped).
- `GET /api/chat/sessions/{id}`: Get session message history and citations.
- `POST /api/chat/sessions/{id}/messages`: Send question, receive answer with chapter citations.

---

## 7. Document Synthesis Studio (Feature 008)
- `POST /api/synthesis/generate`: Trigger multi-book brief synthesis (sync `wait=true` or async `wait=false`).
- `GET /api/synthesis/jobs/{job_id}`: Poll synthesis stage and percent complete.
- `GET /api/synthesis/documents`: List synthesized research documents.
- `GET /api/synthesis/documents/{id}`: Get full document details and markdown.
- `GET /api/synthesis/documents/{id}/export?format={markdown|html|json}`: Download export file.
- `DELETE /api/synthesis/documents/{id}`: Delete synthesized brief.
