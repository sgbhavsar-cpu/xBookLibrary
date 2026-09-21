# Reader & Progress Sync API Contract

## Endpoints

### 1. Reading Progress
- `GET /api/libraries/{library_id}/books/{book_id}/progress?format={format}`
  - Response `200 OK`: `ReadingProgress` or `null`
- `POST /api/libraries/{library_id}/books/{book_id}/progress`
  - Body: `ReadingProgressCreateRequest(format, location, progress_percent, reading_seconds_increment)`
  - Response `200 OK`: `ReadingProgress` (also updates `#read_status` in Calibre custom columns if present)

### 2. Annotations & Highlights
- `GET /api/libraries/{library_id}/books/{book_id}/annotations`
  - Response `200 OK`: `list[Annotation]`
- `POST /api/libraries/{library_id}/books/{book_id}/annotations`
  - Body: `AnnotationCreateRequest(format, location, selected_text, color, note_text, chapter_title)`
  - Response `201 Created`: `Annotation`
- `DELETE /api/libraries/{library_id}/books/{book_id}/annotations/{annotation_id}`
  - Response `204 No Content`
- `GET /api/libraries/{library_id}/books/{book_id}/annotations/export?format=markdown`
  - Response `200 OK`: Markdown text attachment

### 3. Bookmarks
- `GET /api/libraries/{library_id}/books/{book_id}/bookmarks`
  - Response `200 OK`: `list[Bookmark]`
- `POST /api/libraries/{library_id}/books/{book_id}/bookmarks`
  - Body: `BookmarkCreateRequest(format, location, title)`
  - Response `201 Created`: `Bookmark`
- `DELETE /api/libraries/{library_id}/books/{book_id}/bookmarks/{bookmark_id}`
  - Response `204 No Content`

### 4. Comic Streaming (CBZ/CBR)
- `GET /api/libraries/{library_id}/books/{book_id}/comic/manifest`
  - Response `200 OK`: `ComicManifest(book_id, total_pages, pages)`
- `GET /api/libraries/{library_id}/books/{book_id}/comic/pages/{page_index}`
  - Response `200 OK`: Image binary (`image/jpeg`, `image/png`, etc.)
