# Quickstart: In-Browser Web Reader & Reading Progress Sync

## Prerequisites
- Library initialized with books in EPUB, PDF, or CBZ/CBR formats.

## Testing Progress Sync
1. Open any book in the Web UI.
2. Click **Read Now**.
3. Advance pages or scroll through the reader.
4. Check backend:
   ```bash
   curl "http://localhost:8000/api/libraries/{lib_id}/books/{book_id}/progress?format=EPUB"
   ```
5. Notice `#read_status` is updated to `"reading"` in the book's details.
6. Advance past 98%: `#read_status` updates to `"completed"`.

## Testing Comic / Manga Reader
1. Ingest a `.cbz` comic file.
2. Open in Reader, toggle between Manga mode (Right-to-Left) and Webtoon mode (Continuous scroll).
3. Test thumbnail scrubbing and page jumps.
