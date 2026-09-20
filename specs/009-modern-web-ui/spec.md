# Feature Specification: 009 Modern 3-Pane Calibre Web UI & Reader

**Feature**: 009 Modern 3-Pane Calibre Web UI & Reader  
**Status**: Draft  
**Branch**: `009-modern-web-ui`  
**Created**: 2026-09-20  
**Updated**: 2026-09-20  

---

## 1. Executive Summary & Vision

xBookLibrary brings the desktop-class organization of Calibre into a modern, aesthetic web application. Feature 009 delivers a **fluid 3-Pane Calibre-style workspace**, a **virtualized catalog grid/cover flow**, an **intelligent detail inspector**, a **dedicated full-screen reading environment (`/read/:book_id`)**, and integrated access to our AI features: **Agentic Metadata Enrichment (004)**, **Taxonomy Sorting (005)**, **Multi-Resolution Summarization (006)**, **Library-Wise RAG Chat (007)**, and **Multi-Book Document Synthesis Studio (008)**.

The interface is built with **React 19**, **Vite**, **TypeScript**, and a **Modern Vanilla CSS design token system** featuring rich dark/light modes, glassmorphic floating panels, and 60fps micro-animations without external CSS framework overhead.

---

## 2. User Scenarios & Personas

### Persona: Dr. Aris (Researcher & Bibliophile)
- **Goal**: Manages a library of 10,000+ technical and academic books.
- **Workflow**:
  1. Opens xBookLibrary in browser; immediately sees the 3-pane layout loaded with active library metrics.
  2. Filters books by taxonomy hierarchy (`Computer Science > Quantum Computing`) in the left filter pane.
  3. Clicks a book in the virtualized grid; the right inspector animates into view displaying high-res cover, BISAC/DDC badges, formats, and multi-resolution AI summaries.
  4. Clicks "Read Book"; navigates to `/read/:book_id` full-screen reader with dark theme, customizable typography, and progress tracking.
  5. Opens the slide-over AI assistant sidebar inside the reader to ask questions about the current chapter with inline citations.
  6. Navigates back to library and opens the Document Synthesis Studio to generate a comparative literature review across 4 selected books.

---

## 3. UI/UX Architecture & Layout System

### 3.1 The 3-Pane Main View
```
+--------------------------------------------------------------------------------------------------+
| Header & Global Toolbar: Library Selector | Search Bar | Ingestion Upload | AI Studio | Theme     |
+----------------------+----------------------------------------------------+----------------------+
| Left Filter Sidebar  | Center: Virtualized Book Grid / Table View         | Right Inspector Pane |
|                      |                                                    |                      |
| [Taxonomies Tree]    | [Sort by: Title, Date, Rating] [Grid / List View]  | [Cover Image]        |
| - Computer Science   |                                                    | Title & Authors      |
|   - AI & ML (142)    | +---------+  +---------+  +---------+              | Star Rating / Tags   |
|   - Quantum (38)     | | Book 1  |  | Book 2  |  | Book 3  |              | Formats: [EPUB] [PDF]|
| - Physics (89)       | | Cover   |  | Cover   |  | Cover   |              | [Read Now] [Enrich]  |
|                      | +---------+  +---------+  +---------+              | AI Classification    |
| [Authors Filter]     | +---------+  +---------+  +---------+              | Summary Tabs:        |
| [Series Filter]      | | Book 4  |  | Book 5  |  | Book 6  |              | [Exec][Detailed][Chap|
| [Format Badges]      | +---------+  +---------+  +---------+              | RAG Index Status     |
+----------------------+----------------------------------------------------+----------------------+
| Bottom Status Bar: Total Books: 1,420 | Indexed: 1,420 (100%) | Active Task: Idle                 |
+--------------------------------------------------------------------------------------------------+
```

### 3.2 The Dedicated Reader Workspace (`/read/:book_id`)
- **Full-Screen Responsive Reader**: Header with Back button, book title, chapter title, reading progress bar (%), and toolbar.
- **Renderer**:
  - EPUB: Reflowable reader powered by `epubjs` with pagination, font-family selector (Serif, Sans-serif, Dyslexic), font-size slider, line-height, and margins.
  - PDF: Continuous-scroll canvas renderer with zoom controls, page jump, and thumbnail sidebar.
- **Collapsible AI Assistant Sidebar**:
  - Slides out from right edge without disrupting reading.
  - Pre-scoped to the active book or entire library.
  - Displays streaming answers with verifiable chapter citations and instant quote verification.

### 3.3 Slide-Over / Modal Drawers
- **Library RAG Chat Panel**: Persistent drawer for conversational multi-turn library QA.
- **Document Synthesis Studio Modal**: Multi-stage wizard for topic brief generation, live stage tracker, and interactive Markdown/HTML preview with export downloads.
- **Ingestion & Metadata Proposal Modal**: Drag-and-drop file uploader with real-time progress, diff review before metadata merge, and Calibre sync confirmation.

---

## 4. Functional Requirements (FR)

### Navigation & State
- **FR-001**: Application MUST maintain active library state with instant switching between adopted and native Calibre libraries.
- **FR-002**: Filter selections (taxonomy node, author, format, search query) MUST update the URL query parameters for bookmarkable search states.
- **FR-003**: Dedicated reader route (`/read/:book_id`) MUST preserve reading progress in localStorage and sync with backend metadata.

### Catalog Grid & Virtualization
- **FR-004**: Book grid MUST support virtualization to handle 10,000+ items smoothly at 60fps without DOM bloat.
- **FR-005**: User MUST be able to toggle between "Cover Flow / Visual Grid" and "Dense Calibre Table" views.
- **FR-006**: Book search MUST support real-time debounced query filtering across titles, authors, tags, and BISAC/DDC categories.

### Detail Inspector Pane
- **FR-007**: Right pane MUST display high-resolution book cover, author links, publication metadata, ratings, and download/open buttons for all available formats.
- **FR-008**: Inspector MUST display AI metadata enrichment status with a 1-click "Trigger Agentic Enrichment" action.
- **FR-009**: Inspector MUST render multi-resolution summaries (executive, chapter-by-chapter, analytical) with copy/export actions.
- **FR-010**: Inspector MUST show RAG vector indexing status with a 1-click "Index for RAG" button.

### In-Browser Reader
- **FR-011**: Reader MUST support reflowable EPUB reading with custom font families, font sizes, line height, and color schemes (Light, Sepia, Dark, OLED Black).
- **FR-012**: Reader MUST render PDF documents with smooth page navigation, zoom, and continuous scrolling.
- **FR-013**: Reader MUST embed a collapsible AI Chat Assistant allowing the reader to ask questions about the current page, chapter, or book.

### AI Studio & RAG Integration
- **FR-014**: Global RAG Chat Drawer MUST provide multi-turn conversational chat with book citations and session history.
- **FR-015**: Document Synthesis Studio MUST allow selecting multiple books, picking a template, triggering synthesis, polling stage progress, and exporting Markdown/HTML.

---

## 5. Non-Functional Requirements (NFR)

- **NFR-001 (Performance)**: First Contentful Paint (FCP) < 1.0s; Time to Interactive (TTI) < 1.5s on desktop broadband.
- **NFR-002 (Responsiveness)**: Fluid layout down to 1024px desktop and tablet landscape; collapsible sidebars for compact screens.
- **NFR-003 (Aesthetics)**: Modern glassmorphic theme with CSS variables, dark/light modes, accessible contrast (WCAG AA), and subtle hover transitions.
- **NFR-004 (Portability)**: Zero reliance on external SaaS CDNs; all assets, icons (Lucide / SVG), and fonts bundled locally.
- **NFR-005 (Reliability)**: Graceful offline handling; optimistic UI updates for library actions.

---

## 6. Verification Criteria

- [ ] Responsive 3-pane layout functions cleanly with resizable or collapsible left/right panels.
- [ ] Virtualized grid smoothly scrolls 1,000+ mock/real books without stutter or memory leaks.
- [ ] Search & filter bar updates grid in real time (< 50ms UI response).
- [ ] Detail inspector displays book metadata, formats, summaries, and indexing status.
- [ ] `/read/:book_id` successfully opens EPUB and PDF books with reading progress saved.
- [ ] AI assistant panel streams answers and renders verifiable citations.
- [ ] Document Synthesis modal triggers multi-book brief generation and exports Markdown/HTML.
