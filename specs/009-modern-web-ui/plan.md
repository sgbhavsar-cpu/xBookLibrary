# Implementation Plan: 009 Modern 3-Pane Calibre Web UI & Reader

**Feature**: 009 Modern 3-Pane Calibre Web UI & Reader  
**Branch**: `009-modern-web-ui`  
**Status**: Ready  

---

## Technical Approach & Architecture

We build a high-performance web interface inside `frontend/` powered by **React 19**, **Vite**, **TypeScript**, and **Zustand**, styled using a **pure Modern Vanilla CSS design token system**. The UI communicates seamlessly with the existing FastAPI backend (`http://localhost:8000`) through Vite proxying.

### Architectural Principles Alignment
- **Clean Architecture & Separation of Concerns**:
  - `frontend/src/api/`: Typed REST client functions for all backend endpoints.
  - `frontend/src/store/`: Zustand state stores for library, active book, reader, chat, and synthesis.
  - `frontend/src/components/`: Reusable, modular UI components utilizing design tokens.
  - `frontend/src/views/`: Primary views (`LibraryView`, `ReaderView`).
- **Aesthetic Excellence & Rich Aesthetics**:
  - Glassmorphic panels, CSS custom properties, seamless dark/light modes, micro-animations, and responsive layout.
- **Strict Verification & Zero Flakiness**:
  - Component tests with Vitest / Testing Library, TypeScript strict mode, and full production build verification (`npm run build`).

---

## Phase Breakdown

### Phase 1: Project Setup & Design System Foundation (Priority: P1)
- Scaffold `frontend/` directory with Vite + React 19 + TypeScript.
- Configure `vite.config.ts` proxy for `/api` and `/covers`.
- Implement `frontend/src/styles/tokens.css` with CSS custom properties, dark/light themes, and glassmorphism.
- Define TypeScript domain types in `frontend/src/types/`.
- Implement API client layer in `frontend/src/api/client.ts`.
- Set up Zustand stores in `frontend/src/store/`.

### Phase 2: 3-Pane Main View & Virtualized Book Grid (Priority: P1)
- Build `HeaderToolbar` (library switcher, search bar, upload button, theme toggle, AI studio launcher).
- Build `FilterSidebar` (taxonomy tree with book counts, authors list, formats badges).
- Build `BookGrid` with `@tanstack/react-virtual` for smooth 60fps virtualization across thousands of books.
- Build `BookCard` with book cover, title, authors, rating stars, and format chips.
- Build `TableView` for classic dense Calibre view.
- Build `StatusBar` displaying active library statistics and background tasks.

### Phase 3: Detail Inspector Pane & AI Insights (Priority: P1)
- Build `DetailInspector` sliding panel on the right:
  - High-res cover with zoom preview.
  - Metadata badges: BISAC / DDC classification with confidence indicator.
  - Format launcher buttons ("Read EPUB", "Read PDF", download).
  - Summarization tabs (Executive Summary, Chapter-by-Chapter, Key Takeaways).
  - Vector indexing trigger with real-time status indicator.
  - Proposal review button if pending enrichment proposals exist.

### Phase 4: Dedicated Full-Screen Reader Workspace (`/read/:book_id`) (Priority: P2)
- Implement `ReaderView` route:
  - Header with Back button, book title, progress bar, font/theme controls.
  - Reflowable EPUB viewer with theme and typography injection.
  - Continuous PDF viewer with zoom and page controls.
  - LocalStorage progress persistence (`xbook_reading_progress_${id}`).
  - Collapsible In-Reader AI Assistant drawer with book-scoped RAG QA.

### Phase 5: Global Modals & AI Studio Drawers (Priority: P2)
- Build `RAGChatDrawer`: Multi-turn conversational QA with expandable citation snippets.
- Build `SynthesisStudioModal`: Multi-stage document synthesis wizard, live stage tracker, and Markdown/HTML preview with download buttons.
- Build `IngestionModal`: File drag-and-drop uploader with live progress bar and metadata proposal diffs.

### Phase 6: Polish, Verification & Production Build (Priority: P3)
- Verify responsive layout across desktop and tablet screen sizes.
- Verify 100% TypeScript type check (`tsc --noEmit`).
- Verify production build bundle (`npm run build`).
- End-to-end integration test with live backend.
