# Quickstart: 009 Modern 3-Pane Calibre Web UI & Reader

This guide walks through starting and developing the xBookLibrary web interface.

---

## 1. Prerequisites
- **Node.js**: >= 20.0.0
- **npm** or **pnpm**
- **Python**: 3.12 (with `uv` virtual environment active)

---

## 2. Launching the Backend Server

From the repository root (`c:\sac\progs\xBookLibrary`):
```bash
uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI backend runs at `http://127.0.0.1:8000`.

---

## 3. Launching the Frontend Development Server

From the `frontend/` directory:
```bash
cd frontend
npm install
npm run dev
```
The Vite development server runs at `http://localhost:5173`.
All `/api/*` and `/covers/*` calls are automatically proxied to the backend at `http://127.0.0.1:8000`.

---

## 4. Key User Journeys to Test

1. **3-Pane Library Exploration**:
   - Filter by Taxonomy on the left sidebar.
   - Click a book in the central cover grid.
   - Inspect high-res cover, AI BISAC/DDC tags, and formats on the right pane.

2. **Reading a Book (`/read/:id`)**:
   - Click "Read Book" in the inspector.
   - Adjust font size and switch themes (Dark, Sepia, Black).
   - Click the AI Assistant icon on the top right to open the conversational sidebar.

3. **Document Synthesis Studio**:
   - Click the "AI Studio" button in the global toolbar.
   - Select books, choose "Literature Review", and click "Generate Synthesis".
   - Watch the multi-stage progress bar and preview the generated document.
