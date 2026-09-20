# Quickstart & Verification Guide: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature**: 007 Library-Wise LanceDB RAG & Conversational QA Agent  
**Date**: 2026-09-20  

This guide provides end-to-end validation procedures for verifying the LanceDB vector indexing pipeline, hybrid search, and citation-backed conversational QA.

---

## 1. Prerequisites
- Python 3.12+ virtual environment managed by `uv`.
- Dependencies installed: `lancedb<=0.38.0`, `pyarrow>=25.0.0`, `fastapi`, `sqlalchemy`.

---

## 2. Unit & Contract Test Execution

### Run RAG Service Unit Tests
```bash
uv run pytest tests/unit/test_rag_service.py -v
```
**Expected**: Verifies hierarchical chunking, vector table creation in `<LibraryRoot>/.vectors/`, and cosine distance similarity ranking.

### Run Hybrid Search & Citation Tests
```bash
uv run pytest tests/unit/test_rag_search_and_qa.py -v
```
**Expected**: Verifies BM25 + vector reciprocal rank fusion and conversational QA response generation with structured citations.

### Run RAG API Contract Tests
```bash
uv run pytest tests/contract/test_rag_api.py -v
```
**Expected**: Verifies all REST endpoints (`/api/libraries/{id}/index`, `/api/libraries/{id}/search`, `/api/chat/sessions`, `/api/chat/sessions/{id}/messages`).

---

## 3. End-to-End Operational Validation

### Step 1: Index an EPUB Book
```bash
curl -X POST "http://localhost:8000/api/books/1/index"
```
**Output**:
```json
{
  "book_id": 1,
  "chunks_indexed": 48,
  "status": "indexed"
}
```

### Step 2: Query the Library via Hybrid Search
```bash
curl -X POST "http://localhost:8000/api/libraries/default/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "quantum computing entanglement", "top_k": 3}'
```
**Output**: Returns top 3 passages ranked by RRF score with chapter titles and author names.

### Step 3: Conversational Chat with Citations
```bash
# 1. Create a session
SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/chat/sessions" \
  -H "Content-Type: application/json" \
  -d '{"library_id": "default", "title": "Quantum Research"}' | jq -r .id)

# 2. Ask a question
curl -X POST "http://localhost:8000/api/chat/sessions/${SESSION_ID}/messages" \
  -H "Content-Type: application/json" \
  -d '{"content": "How does quantum entanglement prevent classical cloning?"}'
```
**Output**: Returns assistant markdown answer with citations:
```json
{
  "role": "assistant",
  "content": "According to the analysis in Chapter 4, quantum entanglement enforces the no-cloning theorem because... [Quantum Information, Chapter 4]",
  "citations": [
    {
      "book_id": 1,
      "book_title": "Quantum Information",
      "authors": "Nielsen & Chuang",
      "chapter_title": "Chapter 4: Quantum Mechanics and No-Cloning",
      "snippet": "...proves that an unknown quantum state cannot be duplicated...",
      "score": 0.89
    }
  ]
}
```
