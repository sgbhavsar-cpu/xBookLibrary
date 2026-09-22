# Implementation Plan: Core Library Operations, In-Place Metadata Editor & Multi-Format Ingestion

**Feature**: `015-core-metadata-editor-and-import`

---

## 1. Architecture Overview

Feature 015 introduces a comprehensive metadata editing and catalog management subsystem into both backend and frontend layers:

```mermaid
graph TD
    UI[Frontend Catalog Grid / Table / Inspector] -->|Open Single Edit 'E'| EMM[EditMetadataModal.tsx]
    UI -->|Multi-Select 'Bulk Edit'| BEM[BulkEditModal.tsx]
    UI -->|Drag & Drop / Add Format| IM[IngestionModal / Format Actions]
    
    EMM -->|Search Online| OMS_UI[Online Metadata Search Drawer]
    
    EMM -->|PUT /api/books/{id}/metadata| API_BE[books_router.py]
    EMM -->|POST /api/books/{id}/cover| API_BE
    OMS_UI -->|POST /api/books/{id}/online-metadata/query| API_BE
    BEM -->|POST /api/books/bulk-update| API_BE
    IM -->|POST /api/books/{id}/formats| API_BE
    IM -->|DELETE /api/books/{id}/formats/{fmt}| API_BE
    
    API_BE --> MES[MetadataEditorService]
    API_BE --> ONL[OnlineMetadataService]
    API_BE --> INS[IngestionService / CalibreSyncService]
    
    MES --> SQLITE[(metadata.db)]
    MES --> OPF[metadata.opf Generator]
    MES --> DISK[Cover & Format Files on Disk]
```

---

## 2. File Organization & Component Responsibilities

### Backend (Python / FastAPI)
- **Domain Entities**:
  - [`backend/domain/metadata_editor.py`](file:///c:/sac/progs/xBookLibrary/backend/domain/metadata_editor.py): `BookMetadataUpdateRequest`, `OnlineMetadataCandidate`, `BulkMetadataUpdateRequest`.
- **Services**:
  - [`backend/services/metadata_editor_service.py`](file:///c:/sac/progs/xBookLibrary/backend/services/metadata_editor_service.py):
    - Single book update with transactional SQLite commits across `books`, `authors`, `tags`, `series`, `identifiers`, and `comments`.
    - Cover art saving (file upload or remote URL download, normalization to JPEG, thumbnail cache bust).
    - `metadata.opf` generation and atomic writing.
    - Format attachment (`data` table insertion, file copy) and format deletion.
    - Bulk metadata operations (set author/publisher/rating, add/remove tags, auto-increment series index).
  - [`backend/services/online_metadata_service.py`](file:///c:/sac/progs/xBookLibrary/backend/services/online_metadata_service.py):
    - Concurrent queries to Google Books and OpenLibrary.
    - Result normalization and confidence scoring.
- **Routers**:
  - [`backend/api/books_router.py`](file:///c:/sac/progs/xBookLibrary/backend/api/books_router.py):
    - `PUT /api/books/{book_id}/metadata`
    - `POST /api/books/{book_id}/cover`
    - `POST /api/books/{book_id}/online-metadata/query`
    - `POST /api/books/{book_id}/formats`
    - `DELETE /api/books/{book_id}/formats/{format}`
    - `POST /api/books/bulk-update`

### Frontend (React 19 / TypeScript / Vite)
- **Types**:
  - [`frontend/src/types/index.ts`](file:///c:/sac/progs/xBookLibrary/frontend/src/types/index.ts): Add editor models and candidate types.
- **API Client**:
  - [`frontend/src/api/client.ts`](file:///c:/sac/progs/xBookLibrary/frontend/src/api/client.ts): Add API call functions for all metadata and format operations.
- **Store**:
  - [`frontend/src/store/useStore.ts`](file:///c:/sac/progs/xBookLibrary/frontend/src/store/useStore.ts): Add `selectedBookIds: number[]`, `isEditMetadataOpen: boolean`, `isBulkEditOpen: boolean`, `toggleSelectBookId`, `selectAllBooks`, `clearSelectedBooks`.
- **UI Components**:
  - [`frontend/src/components/metadata/EditMetadataModal.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/metadata/EditMetadataModal.tsx): Full Calibre-style metadata editor modal with cover preview, paste listener, tag chip editor, rating stars, comments rich editor, custom column inputs, and "Download Metadata" trigger.
  - [`frontend/src/components/metadata/OnlineMetadataDrawer.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/metadata/OnlineMetadataDrawer.tsx): Side-by-side online candidate inspector and selective field merger.
  - [`frontend/src/components/metadata/BulkEditModal.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/metadata/BulkEditModal.tsx): Modal for updating multiple selected books.
  - [`frontend/src/components/metadata/BulkActionBar.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/metadata/BulkActionBar.tsx): Floating bottom bar when $\ge 1$ books are selected.
  - [`frontend/src/components/DetailInspector.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/DetailInspector.tsx): Add "Edit Metadata" primary button, keyboard shortcut indicator (`E`), and format "+ Add" / "Delete" actions.
  - [`frontend/src/components/BookTable.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/BookTable.tsx) & [`BookGrid.tsx`](file:///c:/sac/progs/xBookLibrary/frontend/src/components/BookGrid.tsx): Multi-selection checkboxes and keyboard modifiers.
