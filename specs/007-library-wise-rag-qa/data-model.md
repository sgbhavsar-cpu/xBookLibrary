# Data Model: 007 Library-Wise LanceDB RAG & Conversational QA Agent

**Feature**: 007 Library-Wise LanceDB RAG & Conversational QA Agent  
**Date**: 2026-09-20  
**Status**: Completed  

---

## 1. Vector Store Schema (LanceDB: `<LibraryRoot>/.vectors/book_chunks`)

Table Name: `book_chunks`

| Field | Type | Description |
|---|---|---|
| `chunk_id` | `string` (Primary Key) | Deterministic ID: `{book_id}_c{chunk_index}` |
| `book_id` | `int64` | Calibre book ID in `metadata.db` |
| `library_id` | `string` | Library identifier (matches library registry) |
| `book_title` | `string` | Full title of the book |
| `authors` | `string` | Comma-separated authors |
| `chapter_index` | `int32` | Index of the chapter within the book |
| `chapter_title` | `string` | Title or heading of the containing chapter |
| `content` | `string` | Complete text passage with breadcrumbs |
| `vector` | `list<float32>[768]` | 768-dimensional normalized embedding vector |
| `token_count` | `int32` | Approximate token length of the chunk |
| `created_at` | `string` (ISO 8601) | Timestamp of embedding generation |

### Indexes
- Vector Index: IVF-PQ or flat cosine distance index on `vector`.
- Scalar Indexes: Filter indices on `book_id`, `chapter_index`.

---

## 2. Relational Metadata Tables (SQLite: `metadata.db`)

### Table: `x_index_status`
Tracks the indexing status, timestamps, and checksums for incremental updates.

```sql
CREATE TABLE IF NOT EXISTS x_index_status (
    book_id INTEGER PRIMARY KEY,
    library_id TEXT NOT NULL,
    indexed_at TIMESTAMP NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    checksum TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'indexed',
    error_message TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_x_index_status_library ON x_index_status(library_id);
```

### Table: `x_chat_sessions`
Stores conversational chat threads scoped to a library or book.

```sql
CREATE TABLE IF NOT EXISTS x_chat_sessions (
    id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL,
    book_id INTEGER,
    title TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_x_chat_sessions_library ON x_chat_sessions(library_id);
```

### Table: `x_chat_messages`
Stores individual conversation turns with structured source citations.

```sql
CREATE TABLE IF NOT EXISTS x_chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (session_id) REFERENCES x_chat_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_x_chat_messages_session ON x_chat_messages(session_id);
```

---

## 3. Domain Models (Pydantic v2: `backend/domain/rag.py`)

### `VectorChunk`
```python
class VectorChunk(BaseModel):
    chunk_id: str
    book_id: int
    library_id: str
    book_title: str
    authors: str
    chapter_index: int
    chapter_title: str
    content: str
    vector: list[float] | None = None
    token_count: int
    created_at: datetime
```

### `Citation`
```python
class Citation(BaseModel):
    book_id: int
    book_title: str
    authors: str
    chapter_index: int
    chapter_title: str
    snippet: str
    score: float
```

### `SearchResult`
```python
class SearchResult(BaseModel):
    chunk_id: str
    book_id: int
    book_title: str
    authors: str
    chapter_index: int
    chapter_title: str
    content: str
    score: float
    match_type: Literal["vector", "keyword", "hybrid"]
```

### `ChatMessage` & `ChatSession`
```python
class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime

class ChatSession(BaseModel):
    id: str
    library_id: str
    book_id: int | None = None
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
```

### `IndexStatus`
```python
class IndexStatus(BaseModel):
    total_books: int
    indexed_books: int
    pending_books: int
    total_chunks: int
    last_indexed_at: datetime | None = None
```
