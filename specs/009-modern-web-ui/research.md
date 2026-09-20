# Research & Architecture: 009 Modern 3-Pane Calibre Web UI & Reader

## 1. Frontend Technology Stack Decisions

### 1.1 React 19 + TypeScript + Vite
- **Rationale**: React 19 provides fast hydration, clean async hooks, and strict type safety. Vite provides sub-second HMR and instant local development builds.
- **Proxy Configuration**:
  ```ts
  // vite.config.ts
  export default defineConfig({
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/covers': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
      },
    },
  });
  ```

---

## 2. Vanilla CSS Design Token System & Glassmorphism

### 2.1 CSS Variables Design Tokens
A pure Vanilla CSS design system with CSS custom properties avoids heavy CSS runtime overhead while delivering a rich aesthetic:
```css
:root {
  /* Colors - Light Theme */
  --bg-app: #f8fafc;
  --bg-surface: #ffffff;
  --bg-surface-glass: rgba(255, 255, 255, 0.82);
  --bg-card: #ffffff;
  --border-subtle: rgba(226, 232, 240, 0.8);
  --border-glass: rgba(255, 255, 255, 0.6);
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --accent-primary: #3b82f6;
  --accent-hover: #2563eb;
  --accent-surface: #eff6ff;
  --accent-glow: rgba(59, 130, 246, 0.25);
  
  /* Layout & Sizing */
  --sidebar-width: 260px;
  --inspector-width: 360px;
  --header-height: 64px;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-full: 9999px;
  
  /* Shadows & Glass */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  --shadow-glass: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
  --backdrop-blur: blur(12px);
}

[data-theme="dark"] {
  /* Colors - Dark Theme */
  --bg-app: #090d16;
  --bg-surface: #0f172a;
  --bg-surface-glass: rgba(15, 23, 42, 0.75);
  --bg-card: #131d31;
  --border-subtle: rgba(51, 65, 85, 0.6);
  --border-glass: rgba(255, 255, 255, 0.08);
  --text-primary: #f8fafc;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent-primary: #60a5fa;
  --accent-hover: #3b82f6;
  --accent-surface: rgba(96, 165, 250, 0.12);
  --accent-glow: rgba(96, 165, 250, 0.3);
  
  --shadow-glass: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}
```

---

## 3. High-Performance Catalog Grid Virtualization

- **Requirement**: Display libraries with up to 10,000+ books without browser slowdown.
- **Solution**: Use `@tanstack/react-virtual` for virtualized rendering of grid items or virtual table rows.
- **Benefits**:
  - Dynamically computes visible item window.
  - Keeps DOM element count < 100 regardless of catalog size.
  - Supports variable card heights, responsive columns, and scroll-to-item.

---

## 4. Full-Screen Reader Architecture (`/read/:book_id`)

### 4.1 EPUB Renderer
- Utilizes `epubjs` with an isolated reflowable display iframe.
- Injects CSS custom properties into iframe body matching active reading theme (Light, Warm Sepia, Charcoal Dark, Pure OLED Black).
- Listens to `relocated` events to extract current CFI, chapter title, and percentage read.
- LocalStorage key: `xbook_reading_progress_${bookId}`.

### 4.2 PDF Renderer
- Utilizes modern HTML5 iframe/object or PDF canvas rendering with fit-to-width, zoom controls, and thumbnail drawer.

### 4.3 Collapsible In-Reader AI Assistant
- Docked as a slide-over panel on the right.
- Pre-populated with active book context.
- Calls `/api/chat/sessions` and `/api/chat/sessions/{id}/messages` with `book_id` filter.
- Renders streaming messages, citation callouts, and quote references.

---

## 5. Zustand State Management Slices

```ts
// Store Structure
interface AppState {
  // Library Slice
  libraries: Library[];
  activeLibraryId: string | null;
  books: Book[];
  filteredBooks: Book[];
  totalBooks: number;
  searchQuery: string;
  selectedTaxonomyPath: string | null;
  selectedAuthor: string | null;
  selectedFormat: string | null;
  
  // Inspector Slice
  selectedBookId: number | null;
  selectedBook: Book | null;
  bookSummaries: BookSummaryResponse | null;
  ragIndexStatus: BookIndexStatus | null;
  
  // UI Slice
  theme: 'light' | 'dark';
  isRAGChatOpen: boolean;
  isSynthesisModalOpen: boolean;
  viewMode: 'grid' | 'table';
  
  // Reader Slice
  readerBookId: number | null;
  readerTheme: 'light' | 'sepia' | 'dark' | 'black';
  readerFontSize: number;
  isReaderAIOpen: boolean;
}
```
