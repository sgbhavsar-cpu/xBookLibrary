# Implementation Plan: Feature 012 In-Browser Web Reader & Reading Progress Sync

## Summary
Implement a high-fidelity, distraction-free in-browser reading suite for EPUB, PDF, and Comic/Manga archives (`.cbz`/`.cbr`) with cross-device reading progress synchronization to Calibre custom columns, persistent text highlights, notes, bookmarks, and contextual AI assistance.

## Architecture

```
                               ┌─────────────────────────────────────────┐
                               │       Modern Web Reader Suite           │
                               │  (EpubReader / PdfReader / ComicReader) │
                               └────────────────────┬────────────────────┘
                                                    │
                 ┌──────────────────────────────────┴──────────────────────────────────┐
                 ▼                                                                     ▼
     ┌───────────────────────┐                                             ┌───────────────────────┐
     │  Reading Progress     │                                             │ Highlights & Notes    │
     │  & Resume Engine      │                                             │ & Comic Streamer      │
     └───────────┬───────────┘                                             └───────────┬───────────┘
                 │                                                                     │
                 ▼                                                                     ▼
     ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
     │                             FastAPI Reader & Comic Router                                   │
     │  GET /progress, POST /progress, GET/POST /annotations, GET/POST /bookmarks, /comic/pages    │
     └──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                    │
                                                    ▼
     ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
     │                  ReadingService, ComicService & CustomColumnsService                        │
     │    - SQLite `reading_progress`, `annotations`, `bookmarks` tables                           │
     │    - Automatic Calibre `#read_status` / `#pages` update upon progress sync                  │
     │    - CBZ ZIP image streaming & fast prefetch                                                │
     └─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Phased Implementation

1. **Phase 1: Domain Models & Unit Tests**:
   - `backend/domain/reading.py`: `ReadingProgress`, `Annotation`, `Bookmark`, `ComicManifest`, etc.
   - `tests/unit/test_reading_domain.py`: Validate models, serialization, and constraints.
2. **Phase 2: Database Storage & Services**:
   - `backend/database/schema.py`: Append `reading_progress`, `annotations`, and `bookmarks` tables.
   - `backend/services/reading_service.py`: Reading progress, Calibre custom column sync, annotations CRUD, bookmarks CRUD, markdown export.
   - `backend/services/comic_service.py`: CBZ/CBR image enumeration, natural sorting, image extraction.
   - `tests/unit/test_reading_service.py`: Service tests.
3. **Phase 3: API Endpoints & Contract Tests**:
   - `backend/api/reader_router.py`: REST endpoints for progress, annotations, bookmarks, comic streaming.
   - Register router in `backend/main.py`.
   - `tests/contract/test_reader_api.py`: Contract tests.
4. **Phase 4: Frontend UI & Reader Suite**:
   - `frontend/src/types/index.ts`: Update TypeScript types.
   - `frontend/src/api/client.ts`: Add reader API methods.
   - `frontend/src/store/useStore.ts`: Add reader state, active progress, annotations.
   - `frontend/src/components/reader/ComicReader.tsx`: Comic/Manga viewer (L-to-R, Manga R-to-L, Webtoon).
   - `frontend/src/components/reader/AnnotationsDrawer.tsx`: Highlights & bookmarks drawer.
   - Update `frontend/src/components/reader/EpubReader.tsx` and `PdfReader.tsx` with highlights, bookmarks, and auto-sync.
   - Update `frontend/src/App.tsx` / `DetailInspector.tsx` reader trigger to handle EPUB, PDF, CBZ/CBR format selection.
5. **Phase 5: Verification & Completion**:
   - Build frontend (`npm run build`).
   - Run full pytest test suite (`uv run pytest`).
   - Git commit.
