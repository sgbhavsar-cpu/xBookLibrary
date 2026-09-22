# xBookLibrary v1.2.9.22 - Modern Calibre-Compatible Library & AI Platform

We are pleased to release **xBookLibrary v1.2.9.22**, a next-generation desktop and web eBook management system featuring 100% Calibre SQLite database (`metadata.db`) compatibility, modern React + Tailwind UI, AI-assisted reading and synthesis, and full feature parity with Calibre's core management workflows.

---

## 🚀 Key Highlights & What's New in v1.2.9.22

### 1. Complete Preferences & Admin Console
- **AI & LLM Configuration**: Directly configure and test connections for **Google Gemini**, **OpenAI**, and local **Ollama** (including custom endpoints and model selection).
- **Calibre Drop Folder (Auto-Import)**: Configure a monitored folder for automatic background book ingestion with support for custom polling intervals, file formats, and on-demand manual scans.
- **Sharing & OPDS Catalog**: Configure integrated OPDS 1.2 catalog settings, port, page size, and optional authentication.
- **UI & Default Formats**: Set default reading and conversion formats, default views (Grid vs. Table), and auto-save preferences.

### 2. Calibre Tag Browser & Hierarchical Tri-State Filtering
- Complete hierarchical taxonomy sidebar for **Authors**, **Series**, **Tags**, **Formats**, **Publishers**, **Languages**, and **Ratings**.
- **Tri-State Boolean Filtering**:
  - **Neutral (Gray)**: Not factored into filter.
  - **Included (Green)**: Filter books that have this tag/author/series.
  - **Excluded (Red)**: Filter out books that have this attribute.
- Category search filter and live book count badges with Calibre-style hierarchy parsing (`genre.subgenre`).

### 3. In-Place Grid & Table Metadata Editing
- Directly edit **Title**, **Authors**, **Series & Index**, **Rating**, and **Tags** inside the Table or Grid without opening a modal.
- Enter key saves instantly; Escape key cancels with zero lag.
- Full atomic updates to Calibre SQLite database and background `metadata.opf` synchronization.

### 4. Complete Single & Bulk Metadata Management
- **Single Book Editor**: Dual-column layout with tabbed metadata, custom tags, identifiers (ISBN, DOI, Goodreads, Google Books), Calibre-style cover viewer and replacement (from disk or clipboard), and online metadata scraping.
- **Bulk Metadata Editor**: Update multiple selected books simultaneously (add/remove tags, set series index, change rating, update author).
- **Online Metadata Scraping**: Live query across Google Books and Open Library with cover art preview and one-click field merging.

### 5. Multi-Format Conversion & Reader
- On-the-fly conversion between **EPUB, PDF, MOBI, AZW3, TXT, and CBZ**.
- Integrated EPUB/PDF reader with continuous scrolling, dark mode, font scaling, and full-text search.
- Native OPDS 1.2 catalog for e-readers (KOReader, Moon+ Reader, Apple Books).

### 6. User Manual & Documentation
- Comprehensive 12-section user guide available in [`docs/USER_MANUAL.md`](https://github.com/sgbhavsar-cpu/xBookLibrary/blob/master/docs/USER_MANUAL.md).

---

## 📦 Installation & Setup

Download and run the Windows installer below:
- **`xBookLibrary_Setup_v1.2.9.22.exe`** (Windows 10 / 11 64-bit installer built with Inno Setup)

Alternatively, run from source:
```bash
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python run_xBookLibrary.py

# Frontend (Dev)
cd frontend
npm install
npm run dev
```
