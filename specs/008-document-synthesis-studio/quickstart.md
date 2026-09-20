# Quickstart & Verification Guide: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature**: 008 Multi-Book Document Synthesis & Knowledge Brief Studio  
**Date**: 2026-09-20  

This guide explains how to generate, inspect, and export multi-book synthesized research documents.

---

## 1. Automated Test Execution

### Run Domain & Synthesis Service Unit Tests
```bash
uv run pytest tests/unit/test_synthesis_service.py -v
```
**Expected**: Verifies outline generation, targeted sectional retrieval, section drafting with citations, and document assembly.

### Run Exporter Unit Tests
```bash
uv run pytest tests/unit/test_synthesis_exporter.py -v
```
**Expected**: Verifies Markdown and styled HTML formatting, bibliography injection, and file system writing under `<LibraryRoot>/.synthesis/`.

### Run Contract Tests
```bash
uv run pytest tests/contract/test_synthesis_api.py -v
```
**Expected**: Verifies all endpoints (`/api/synthesis/generate`, `/api/synthesis/documents`, `/api/synthesis/documents/{id}/export`).

---

## 2. API Usage Examples

### Step 1: Generate a Multi-Book Literature Review
```bash
curl -X POST "http://localhost:8000/api/synthesis/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Quantum Error Correction & Fault Tolerance",
    "topic_prompt": "Compare topological codes vs surface codes across selected quantum literature.",
    "template_type": "literature_review",
    "book_ids": [1, 2],
    "wait": true
  }'
```

### Step 2: Export as Styled HTML
```bash
curl "http://localhost:8000/api/synthesis/documents/{id}/export?format=html" \
  -o "quantum_brief.html"
```
