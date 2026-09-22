# xBookLibrary — User Manual & Operations Guide

**Version**: `1.2.9.22`  
**Platform**: Windows 10 / 11 (64-bit) & Cross-Platform Web  
**Compatibility**: 100% Calibre `metadata.db` schema backward-compatibility  

---

## 1. Introduction & Architecture

**xBookLibrary** is a modern, high-performance, AI-augmented personal ebook and audiobook library manager built to provide full desktop feature parity with **Calibre** while integrating state-of-the-art AI capabilities (RAG semantic chat, chapter summarization, multi-book synthesis, and Whisper transcription).

### Key Architectural Highlights
- **Zero-Schema-Drift Calibre Compatibility**: Operates directly on standard Calibre `metadata.db` SQLite databases, matching all standard tables (`books`, `authors`, `data`, `tags`, `series`, `publishers`, `ratings`, `identifiers`, `custom_columns`).
- **Dual-Database Design**: Library books and metadata remain strictly portable in `metadata.db`, while isolated application features (reading progress, annotations, RAG vector embeddings, AI jobs) reside in isolated extension tables.
- **Universal Multi-Format Engine**: Native support for `EPUB`, `PDF`, `MOBI`, `AZW3`, `TXT`, `DOCX`, `CBZ`, and `MP3`/`M4B` audiobooks.
- **Local-First AI & RAG**: LanceDB vector database with support for offline local CPU embeddings (`all-MiniLM-L6-v2`), local Ollama models, or cloud providers (Google Gemini, OpenAI).

---

## 2. Quick Start & Installation

### Option A: Windows Installer (Recommended)
1. Download `xBookLibrary_Setup_v1.2.9.22.exe` from the GitHub Releases page.
2. Run the installer and follow the setup wizard.
3. Launch **xBookLibrary** from the Start Menu or Desktop shortcut.

### Option B: Running from Source
Prerequisites: Python 3.12+ (managed by `uv`) and Node.js 20+.
```bash
# 1. Start backend server
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Start frontend dev server
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5180
```
Open [http://localhost:5180](http://localhost:5180) in your web browser.

---

## 3. Managing Libraries

### Switching Active Libraries
- In the top header bar, click the library dropdown next to the xBookLibrary logo.
- Select any registered library to instantly switch active collections without restarting the application.

### Adopting an Existing Calibre Library
1. Click the **Folder+** button in the header toolbar.
2. Select the **"Adopt Calibre Library"** tab.
3. Enter or browse to the directory containing an existing `metadata.db` file.
4. Click **"Adopt Library in Place"**. Your entire Calibre catalog, covers, authors, and custom columns are loaded instantly with zero file copying.

### Creating a New Library
1. Click the **Folder+** button in the header toolbar.
2. Select the **"Create New Library"** tab.
3. Provide a library name and target filesystem directory.
4. Click **"Create Library"** to initialize a pristine, portable Calibre-compliant database.

---

## 4. The Calibre Tag Browser & Tri-State Filtering

Located on the left sidebar, the **Tag Browser** organizes all dimensions of your library into collapsible drawers:
- 👤 **Authors** (with individual book counts)
- 📚 **Series** (with series title and volume count)
- 🏷️ **Tags** (with hierarchical folder expanders)
- 💾 **Formats** (`EPUB`, `PDF`, `MOBI`, `AZW3`, `TXT`, etc.)
- 🏛️ **Publishers**
- ⭐ **Rating** (`5 Stars`, `4 Stars`, `3 Stars`, `2 Stars`, `1 Star`, `Unrated`)
- 🆔 **Identifiers** (`isbn`, `goodreads`, `amazon`, `doi`)
- ⚙️ **Custom Calibre Columns** (`#read_status`, `#genre`, etc.)
- 📑 **Taxonomies** (Academic BISAC / DDC hierarchy)

### The Tri-State Filtering Engine
Every row in the Tag Browser cycles through three states upon clicking:
$$\text{Neutral (default)} \longrightarrow \text{Include (+ Green)} \longrightarrow \text{Exclude (- Red)} \longrightarrow \text{Neutral}$$

- **Positive Inclusion (`+`)**: Restricts the catalog to books matching this attribute.
- **Negative Exclusion (`-`)**: Excludes any books having this attribute from the catalog.
- **Multi-Category Conjunction**: You can combine multiple criteria simultaneously:
  - *Example*: Include Author `Frank Herbert` `[+]`, Exclude Tag `Non-Fiction` `[-]`, Include Format `EPUB` `[+]`.
- **Hierarchical Tag Sub-Trees**:
  - Tags with dots or slashes (`Fiction.Sci-Fi.Space Opera`) are automatically parsed into nested folder trees.
  - Clicking a parent folder matches all descendant child tags.
- **Tree Quick-Search**:
  - Type in the `Filter categories / tags...` box to dynamically filter visible tree nodes on the fly.
- **Sort Modes & Controls**:
  - Click the Sort toggle to switch between Alphabetical (`A-Z`) and Frequency (`Count`).
  - Use the Expand All and Collapse All buttons for quick navigation.
  - Dismiss active filters individually via the chip bar or click **Clear All**.

---

## 5. Catalog Navigation & In-Place Metadata Editing

### Grid & Table Views
- **Grid View**: Visual cover flow layout with responsive card sizing, reading badges, and quick-action buttons.
- **Table View**: Dense Calibre-style data table with sortable columns for Title, Authors, Formats, Series, Rating, and Tags.

### In-Place Grid & Table Editing
1. **Double-click** any book card in the Grid or any row in the Table view.
2. The card/row transforms into interactive editing controls:
   - Edit **Title**
   - Edit **Authors** (comma-separated)
   - Edit **Series** and **Series Number**
   - Change **Rating** (0 to 5 stars)
3. Press <kbd>Enter</kbd> or click the green Check button to commit and save immediately to `metadata.db`.
4. Press <kbd>Esc</kbd> or click the red Cancel button to discard changes.

### Comprehensive Metadata Modal Editor
- Press <kbd>E</kbd> or click **"Edit Metadata"** on the right Detail Inspector.
- **Online Metadata & Cover Search**: Query Google Books, Open Library, and CrossRef simultaneously to fetch book descriptions, high-resolution covers, publication dates, and ISBNs.
- **Format Attachment & Removal**: Add or remove format files directly from the book folder.
- **OPF Synchronization**: Generates and syncs standard Calibre `metadata.opf` files alongside book files.

### Bulk Metadata Operations & Deletion
- **Multi-Book Selection**: Hold <kbd>Ctrl</kbd> or click checkboxes on book cards/table rows.
- **Bulk Edit**: Mass-assign authors, series, ratings, or add/remove tags across all selected books.
- **Bulk Delete**: Permanently removes selected books, cascades foreign keys, cleans up orphaned authors/tags in `metadata.db`, drops vector embeddings in LanceDB, and removes book directories from disk.

---

## 6. Format Conversion & Save to Disk

### Format Conversion Dialog
- Press <kbd>C</kbd> or click **"Convert"** in the top toolbar or Detail Inspector.
- Supports single and bulk conversions between `EPUB`, `PDF`, `MOBI`, `AZW3`, `TXT`, and `DOCX`.
- Automatically detects input format and selects the recommended target format.
- Live progress bar and terminal log stream powered by real-time Server-Sent Events (SSE).

### Save to Disk / Directory Export
- In the Detail Inspector, click **"Export to Folder"**.
- Packages the format files, `cover.jpg`, and standard Calibre `metadata.opf` into the selected export folder.

---

## 7. Drop Folder & Automated Ingestion

xBookLibrary includes Calibre-compatible **Automatic Adding**:
1. Open **Preferences** (<kbd>Ctrl+,</kbd> or the gear icon in the header).
2. Go to the **"Drop Folder / Import"** tab.
3. Specify your intake directory (e.g. `C:\Users\YourName\Downloads\eBooks Intake`).
4. Enable the **Background File System Watcher** checkbox.
5. Choose duplicate handling:
   - `Merge`: Attaches new formats to existing books automatically.
   - `Create New`: Always creates a new entry.
   - `Skip`: Skips duplicates.
6. Click **"Scan Drop Folder Now"** for an immediate intake scan.

---

## 8. Built-in Reader & Audiobook Studio

### E-Book Reader Workspace
- Click **"Read"** or press <kbd>V</kbd> to enter the dedicated full-screen reader workspace.
- **EPUB Engine**:
  - Themes: Light, Sepia, Dark, OLED Black.
  - Typography: Font size, line spacing, margins.
  - Layout: Paginated dual-page or vertical scrolled mode.
  - Annotations: Highlight text in yellow, green, blue, or purple; add personal notes.
  - Bookmarks & Table of Contents navigation.
- **PDF Engine**:
  - Dual rendering via PDF.js.
  - Page thumbnail sidebar, zoom in/out, fit-to-width, and direct page jump.
- **Comic Reader**:
  - Native CBZ/CBR reader supporting Left-to-Right, Right-to-Left (Manga), and continuous Webtoon scrolling.

### Audiobook Player & Whisper Transcription
- Play MP3 and M4B audiobooks with chapter navigation and variable playback speed ($0.75\times$ to $2.5\times$).
- Mini-Player bar stays docked at the bottom of the screen while you browse your catalog.
- **Whisper AI Transcription**: Generate searchable, time-stamped text transcripts of audiobook chapters automatically.

---

## 9. AI & Knowledge Discovery

### RAG Conversational Library Chat
- Click **"Library Chat"** in the header toolbar.
- Ask questions about your books in natural language:
  - *"What are the core principles of spice ecology in Dune?"*
  - *"Summarize the political structure of the Foundation universe."*
- Responses include direct, clickable **chapter citations** that open the book directly to the referenced passage.

### Synthesis Studio
- Click **"Synthesis Studio"** in the header.
- Select multiple books across your collection.
- Generate comparative research briefs, thematic overviews, and executive summaries across your library.

---

## 10. Device Sync & Network Sharing

### OPDS Catalog Server
- Built-in OPDS 1.2 catalog server running on port `8000`.
- Feed URL: `http://127.0.0.1:8000/opds`
- Compatible with **Moon+ Reader**, **KOReader**, **Apple Books**, **Thorium**, and **KyBook**.

### Wireless Device Sync
- **KOReader Kosync**: Wireless reading position and progress synchronization at `http://127.0.0.1:8000/api/kosync`.
- **Kobo USB Sync**: Auto-detects connected Kobo e-readers and generates Kobo Kepub format files.
- **Kindle Delivery**: One-click email delivery over SMTP.

---

## 11. Preferences & Admin Console

Access the Preferences dialog via the gear icon in the top header or shortcut <kbd>Ctrl+,</kbd>:
1. **AI & LLM Models**:
   - Select between Google Gemini, OpenAI, or Ollama (Local LLM).
   - Enter API keys or configure local Ollama endpoint (`http://localhost:11434`).
   - Click **"Test AI Connection"** to verify model connectivity and view available models.
2. **Drop Folder / Import**:
   - Set automated intake path, background watcher toggle, and duplicate resolution rule.
3. **Sharing & OPDS**:
   - View OPDS and Kosync server URLs with quick-copy buttons.
4. **Defaults & UI**:
   - Configure default conversion target format, catalog fetch limit, and theme.

---

## 12. Keyboard Shortcuts Reference

| Shortcut | Action | Scope |
|:---:|---|---|
| <kbd>E</kbd> | Edit Metadata (or Bulk Edit if multiple selected) | Main Catalog |
| <kbd>C</kbd> | Convert Book Format(s) | Main Catalog |
| <kbd>V</kbd> | View / Read Selected Book | Main Catalog |
| <kbd>Esc</kbd> | Deselect All Books / Cancel in-place edit | Main Catalog |
| <kbd>Enter</kbd> | Save in-place metadata edit | In-Place Edit |
| <kbd>Ctrl</kbd> + Click | Multi-select books for batch actions | Main Catalog |
| <kbd>Ctrl</kbd> + <kbd>,</kbd> | Open Preferences & Admin Console | Global |
