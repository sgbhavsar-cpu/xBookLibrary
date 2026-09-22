# Implementation Plan: Audiobook Hub & Whisper Transcription (Feature 014)

## Architecture Overview
Feature 014 adheres strictly to the Constitution:
- **Calibre Compatibility**: Audiobooks reside in standard `<LibraryRoot>/<Author>/<Title> (<Year>)/<Title> - <Author>.{m4b,mp3}` directories. Records are saved in standard `books` and `data` tables with format="M4B" or "MP3".
- **Clean Extension**: Spoken-audio metadata is stored in `x_audiobook_metadata`, listening state in `x_reading_progress` / `AudioListeningProgress`, and transcripts in `x_audio_transcripts`.
- **Grounded Intelligence**: Whisper transcripts are indexed into `.vectors/` (LanceDB) by `RAGIndexer`, so conversational RAG can cite spoken audio timestamps directly.

## Phasing & Execution Order
1. **Phase 1: Domain & Database**:
   - `backend/domain/audiobook.py`
   - `backend/database/schema.py`
2. **Phase 2: Format Parsing**:
   - `backend/parsers/audio_parser.py` (Mutagen)
   - `backend/parsers/__init__.py`
3. **Phase 3: Core Services**:
   - `backend/services/audiobook_service.py` (Metadata, Range streaming, Progress)
   - `backend/services/transcription_service.py` (Whisper/Gemini, VTT/SRT/MD export, LanceDB sync)
4. **Phase 4: API Endpoints & Contract Tests**:
   - `backend/api/audiobooks_router.py`
   - `backend/main.py`
   - `tests/contract/test_audiobooks_api.py`
5. **Phase 5: Frontend Experience**:
   - Types, API client, Zustand store
   - `AudiobookPlayer.tsx`, `PersistentAudioBar.tsx`
   - `ReaderView.tsx`, `DetailInspector.tsx`, `App.tsx`
6. **Phase 6: Quality Verification & Commit**:
   - Complete `pytest` suite execution (100% pass)
   - TypeScript and Vite production build verification
