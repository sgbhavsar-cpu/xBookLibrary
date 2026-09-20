# Research: Agentic Metadata Enrichment & Multimodal Reconciliation

**Feature Branch**: `004-agentic-metadata-enrichment`  
**Date**: 2026-09-20  

---

## 1. Upstream Bibliographic Providers

### 1.1 OpenLibrary Books API
- **ISBN Lookup**: `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`
- **Title / Author Search**: `https://openlibrary.org/search.json?title={title}&author={author}&limit=5`
- **Covers**: `https://covers.openlibrary.org/b/id/{cover_id}-L.jpg`
- **Rate Limit & Policy**: ~1 request per second. Send descriptive `User-Agent: xBookLibrary/0.1.0`.

### 1.2 Google Books API
- **Query Endpoint**: `https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}` or `https://www.googleapis.com/books/v1/volumes?q=intitle:{title}+inauthor:{author}`
- **High-Resolution Covers**: Replace `zoom=1` with `zoom=2` or `zoom=3` and remove `&edge=curl` in `imageLinks.thumbnail` to obtain pristine high-definition covers.
- **Rate Limits**: 1,000 requests/day unauthenticated; 60 requests/minute authenticated with optional `GOOGLE_BOOKS_API_KEY`.

### 1.3 CrossRef API (Academic Works & DOIs)
- **DOI Lookup**: `https://api.crossref.org/works/{doi}`
- **Bibliographic Search**: `https://api.crossref.org/works?query.bibliographic={title}&query.author={author}&rows=3`
- **Polite Pool**: CrossRef guarantees high-speed responses if `User-Agent` includes a contact email: `xBookLibrary/0.1.0 (https://github.com/sac/xBookLibrary; mailto:support@example.com)`.

---

## 2. LiteLLM Multimodal Vision Integration

`litellm` provides unified completion across Gemini, Ollama, OpenAI, and Claude:

### 2.1 Google Gemini 2.0 Flash (`gemini/gemini-2.0-flash`)
- Uses standard `GEMINI_API_KEY`.
- Latency: ~700–1200ms per request.
- Handles base64 encoded JPEG pages (Cover, Title Page, Copyright Page).

### 2.2 Local Ollama Vision (`ollama/llama3.2-vision`)
- Uses `OLLAMA_HOST` (default: `http://localhost:11434`).
- Zero cloud egress; ideal for offline or sensitive documents.

### 2.3 Prompt Strategy & Structured Extraction
Prompt requests pure JSON output adhering to the schema:
```json
{
  "title": "Clean book title",
  "authors": ["Author One", "Author Two"],
  "publisher": "Publishing House",
  "publication_year": 1984,
  "isbn": "978...",
  "description": "Short synopsis or description extracted from blurb",
  "confidence": 0.95
}
```

---

## 3. Decision Matrix: Strict ISBN vs. Staged Review

| Condition | Action | Storage |
|:---|:---|:---|
| Exact 100% ISBN Match (OpenLibrary / Google Books) | **Auto-Apply** | Direct commit to `metadata.db` & `metadata.opf` |
| Title/Author Search Match | **Stage for Review** | Save `.vectors/staging/<proposal_id>.json` |
| Multimodal LLM Vision Extraction | **Stage for Review** | Save `.vectors/staging/<proposal_id>.json` |
| Conflicting Fields between Providers | **Stage for Review** | Save `.vectors/staging/<proposal_id>.json` |
