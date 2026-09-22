# Tasks: Audiobook Hub & Whisper Transcription (Feature 014)

## Phase 1: Setup & Domain Models
- [x] T001: Define domain models and schemas (`AudioChapter`, `AudiobookMetadata`, `AudioListeningProgress`, `AudioTranscriptSegment`, `AudioChapterTranscript`, `TranscriptionRequest`, `TranscriptExportFormat`) in `backend/domain/audiobook.py`.
- [x] T002: Update `backend/database/schema.py` to add `x_audiobook_metadata` and `x_audio_transcripts` to `CALIBRE_SCHEMA_DDL`.

## Phase 2: Format Parsers & Tests
- [x] T003: Implement `backend/parsers/audio_parser.py` using `mutagen` to extract M4B and MP3 metadata, duration, cover art, and chapter markers.
- [x] T004: Register `.m4b` and `.mp3` in `backend/parsers/__init__.py`.
- [x] T005: Create unit tests in `tests/unit/parsers/test_audio_parser.py`.

## Phase 3: Core Services & Unit Tests
- [x] T006: Implement `backend/services/audiobook_service.py` for metadata caching, HTTP Range partial content generation, and listening progress synchronization.
- [x] T007: Create unit tests for `AudiobookService` in `tests/unit/test_audiobook_service.py`.
- [x] T008: Implement `backend/services/transcription_service.py` with pluggable providers, VTT/SRT/Markdown export, and LanceDB vector indexing integration.
- [x] T009: Create unit tests for `TranscriptionService` in `tests/unit/test_transcription_service.py`.

## Phase 4: API Endpoints & Contract Tests
- [x] T010: Implement `backend/api/audiobooks_router.py` with metadata, streaming, progress, transcription, and export endpoints.
- [x] T011: Mount `audiobooks_router` in `backend/main.py`.
- [x] T012: Create contract tests in `tests/contract/test_audiobooks_api.py`.

## Phase 5: Frontend Experience
- [x] T013: Add audiobook TypeScript interfaces to `frontend/src/types/index.ts`.
- [x] T014: Add audiobook API methods to `frontend/src/api/client.ts`.
- [x] T015: Add audiobook playback and transcript actions to `frontend/src/store/useStore.ts`.
- [x] T016: Build `frontend/src/components/audiobook/AudiobookPlayer.tsx` with scrubber, chapters, speed, sleep timer, live transcript sync, and Whisper transcription trigger.
- [x] T017: Build `frontend/src/components/audiobook/PersistentAudioBar.tsx` for background listening in library view.
- [x] T018: Connect `ReaderView.tsx`, `DetailInspector.tsx`, and `App.tsx` to audiobook player and inspector actions.

## Phase 6: Verification & Delivery
- [x] T019: Execute full backend test suite (`uv run pytest`) and verify 100% pass rate.
- [x] T020: Validate production frontend build (`tsc -b && vite build`).
