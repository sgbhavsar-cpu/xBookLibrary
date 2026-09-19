# Quickstart: Core Library Model & Ingestion

**Feature Branch**: `001-core-library-ingestion`  
**Date**: 2026-09-20  

## Prerequisites
- Python 3.12+
- `uv` package manager (installed)
- Git (configured)

---

## 1. Environment Setup

Initialize the Python virtual environment and install core dependencies using `uv`:
```bash
# Sync dependencies via uv
uv sync

# Alternatively, run via uv directly
uv run pytest
```

---

## 2. Running Automated Tests

Run the complete test suite:
```bash
# Run all unit and contract tests
uv run pytest tests/ -v

# Run format-specific parser tests
uv run pytest tests/unit/parsers/ -v

# Run Calibre in-place adoption test
uv run pytest tests/unit/test_calibre_adoption.py -v
```

---

## 3. Starting the Backend Service

Start the FastAPI application with live reload:
```bash
uv run uvicorn backend.main:app --reload --port 8000
```
- Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/libraries`

---

## 4. Verifying Feature Capabilities

### A. Adopting an Existing Calibre Library
```bash
curl -X POST http://localhost:8000/api/libraries \
  -H "Content-Type: application/json" \
  -d '{"name": "My Calibre Books", "path": "C:/path/to/calibre/library", "adopt_existing_calibre": true}'
```

### B. Uploading and Ingesting Books
```bash
curl -X POST http://localhost:8000/api/books/upload \
  -F "files=@sample.epub" \
  -F "files=@sample.pdf"
```

### C. Checking Ingestion Job Progress
```bash
curl http://localhost:8000/api/jobs/{job_id}
```
