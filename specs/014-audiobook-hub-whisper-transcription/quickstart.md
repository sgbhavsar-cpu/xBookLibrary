# Quickstart Guide: Audiobook Hub & Whisper Transcription (Feature 014)

## Running Unit & Contract Tests
```powershell
uv run pytest tests/unit/parsers/test_audio_parser.py
uv run pytest tests/unit/test_audiobook_service.py
uv run pytest tests/unit/test_transcription_service.py
uv run pytest tests/contract/test_audiobooks_api.py
```

## Running Full Regression Test Suite
```powershell
uv run pytest
```

## Verifying Frontend Compilation
```powershell
cd frontend
npm run build
```

## API Testing Examples

### 1. Fetching Audiobook Metadata
```bash
curl http://localhost:8000/api/libraries/default/books/1/audio/metadata
```

### 2. Audio Streaming with Range Header (Seeking)
```bash
curl -H "Range: bytes=0-1048575" -i http://localhost:8000/api/libraries/default/books/1/audio/stream
```

### 3. Requesting Chapter Transcription
```bash
curl -X POST http://localhost:8000/api/libraries/default/books/1/audio/transcribe \
  -H "Content-Type: application/json" \
  -d '{"book_id": 1, "chapter_index": 0}'
```

### 4. Exporting Transcripts (VTT / SRT / Markdown)
```bash
curl http://localhost:8000/api/libraries/default/books/1/audio/transcripts/export?format=vtt
```
