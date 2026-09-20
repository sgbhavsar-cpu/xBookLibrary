# Tasks: 009 Modern 3-Pane Calibre Web UI & Reader

**Feature**: 009 Modern 3-Pane Calibre Web UI & Reader  
**Branch**: `009-modern-web-ui`  
**Status**: Ready  

---

## Phase 1: Foundation, Design Tokens & API Client (Priority: P1)

**Goal**: Establish the React 19 + TypeScript + Vite project in `frontend/`, implement the Modern Vanilla CSS design system with design tokens, glassmorphism, and theme switching, declare domain types, and configure API clients with Zustand stores.

- [x] T001 Initialize React 19 + TypeScript + Vite project in `frontend/` with proxy configuration for `/api` and `/covers` in `frontend/vite.config.ts`.
- [x] T002 Implement design tokens, typography, dark/light themes, and glassmorphic utilities in `frontend/src/styles/tokens.css` and `frontend/src/styles/index.css`.
- [x] T003 Define TypeScript interfaces for Books, Taxonomies, Summaries, RAG Chat, and Synthesis in `frontend/src/types/index.ts`.
- [x] T004 Implement typed API client service in `frontend/src/api/client.ts` consuming backend REST endpoints.
- [x] T005 Implement Zustand state store in `frontend/src/store/useStore.ts` with slices for library, catalog, active book, reader, chat, and synthesis.

---

## Phase 2: Core 3-Pane Calibre Layout & Virtualized Catalog (Priority: P1)

**Goal**: Build the responsive 3-pane Calibre layout featuring a global toolbar, hierarchical taxonomy filter sidebar, virtualized book cover grid with `@tanstack/react-virtual`, classic table toggle, and bottom status bar.

- [x] T006 Implement `HeaderToolbar` component with library selector, real-time search input, view toggle (grid/table), upload trigger, AI studio trigger, and dark/light theme switch in `frontend/src/components/HeaderToolbar.tsx`.
- [x] T007 Implement `FilterSidebar` component with hierarchical taxonomy tree, author quick-filters, and format badges in `frontend/src/components/FilterSidebar.tsx`.
- [x] T008 Implement `BookCard` component with cover image, title, authors, star ratings, format chips, and hover glow micro-animations in `frontend/src/components/BookCard.tsx`.
- [x] T009 Implement `BookGrid` virtualized catalog view using `@tanstack/react-virtual` in `frontend/src/components/BookGrid.tsx`.
- [x] T010 Implement `BookTable` dense data table view for classic Calibre users in `frontend/src/components/BookTable.tsx`.
- [x] T011 Implement `StatusBar` component with total book counts, indexing status, and active background tasks in `frontend/src/components/StatusBar.tsx`.

---

## Phase 3: Detail Inspector Pane & AI Insights (Priority: P1)

**Goal**: Build the rich right-hand inspector displaying high-res covers, metadata badges, multi-resolution summary tabs, format launchers, RAG indexing actions, and proposal diffs.

- [x] T012 Implement `DetailInspector` component with cover preview, BISAC/DDC category badges, format action buttons, and synopsis in `frontend/src/components/DetailInspector.tsx`.
- [x] T013 Implement `SummaryTabs` inside inspector displaying Executive Summary, Key Takeaways, and Chapter Summaries with generate/export triggers in `frontend/src/components/SummaryTabs.tsx`.
- [x] T014 Implement RAG vector indexing action button and status badge in `DetailInspector`.

---

## Phase 4: Dedicated Full-Screen Reader Workspace (`/read/:book_id`) (Priority: P2)

**Goal**: Implement the dedicated reader view with reflowable EPUB rendering, continuous PDF viewing, reader settings (themes, fonts), progress tracking, and collapsible AI assistant.

- [x] T015 Implement `ReaderView` page with header toolbar, reading progress indicator, and theme controls in `frontend/src/views/ReaderView.tsx`.
- [x] T016 Implement `EpubReader` component with `epubjs` reflowable renderer, theme injection, and location CFI persistence in `frontend/src/components/reader/EpubReader.tsx`.
- [x] T017 Implement `PdfReader` component with canvas rendering, zoom controls, and page navigation in `frontend/src/components/reader/PdfReader.tsx`.
- [x] T018 Implement `ReaderAIAssistant` collapsible sidebar allowing readers to query the active book with inline citations in `frontend/src/components/reader/ReaderAIAssistant.tsx`.

---

## Phase 5: Global AI Studio Modals & Drawers (Priority: P2)

**Goal**: Implement the Library RAG Chat drawer, Document Synthesis Studio wizard, and Ingestion Upload modal.

- [x] T019 Implement `RAGChatDrawer` component for conversational multi-turn library QA with citation expansion in `frontend/src/components/RAGChatDrawer.tsx`.
- [x] T020 Implement `SynthesisStudioModal` component for multi-book brief generation, stage tracker, and Markdown/HTML export in `frontend/src/components/SynthesisStudioModal.tsx`.
- [x] T021 Implement `IngestionModal` drag-and-drop file uploader with live progress and metadata proposal diffs in `frontend/src/components/IngestionModal.tsx`.

---

## Phase 6: Polish, Verification & Production Build (Priority: P3)

**Goal**: Verify responsive layout, zero TypeScript errors, successful production build, and full end-to-end integration.

- [x] T022 Assemble `LibraryView` and route switching between Library and Reader in `frontend/src/App.tsx`.
- [x] T023 Run `tsc --noEmit` and verify zero TypeScript compilation errors.
- [x] T024 Run `npm run build` and verify production bundle creation in `frontend/dist/`.
- [x] T025 Commit Feature 009 to git.
