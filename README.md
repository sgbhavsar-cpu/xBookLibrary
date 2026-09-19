# xBookLibrary

A next-generation Calibre-style digital book library featuring:
- **Calibre In-Place Adoption & Portability**: 100% portable per-library SQLite (`metadata.db`) and directory layout.
- **Pluggable Multi-Format Parser Strategy**: EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ, CBR.
- **Agentic Pre-Import Metadata Enrichment**: Multi-source aggregation (OpenLibrary, Google Books, CrossRef/arXiv, LLM fallback) with visual diff review.
- **AI Dual-Taxonomy Classification & Auto-Sorting**: BISAC / Dewey Decimal + Custom Collections.
- **Multi-Resolution AI Book Summarization**: Executive Snapshot, Chapter Outline, Conceptual Framework.
- **Library-Wise RAG & Document Synthesis**: Isolated LanceDB vector stores per library with citation-backed QA and cross-book research synthesis.
- **Modern 3-Pane UI**: Dark/light themes, cover gallery, high-density table, slide-out inspector, built-in reader, and interactive chat drawer.

## Quickstart

```bash
# Sync dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run FastAPI backend server
uv run uvicorn backend.main:app --reload --port 8000
```
