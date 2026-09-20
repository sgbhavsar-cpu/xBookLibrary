# Data Model: 008 Multi-Book Document Synthesis & Knowledge Brief Studio

**Feature**: 008 Multi-Book Document Synthesis & Knowledge Brief Studio  
**Date**: 2026-09-20  
**Status**: Completed  

---

## 1. Relational Table Schema (SQLite: `metadata.db`)

### Table: `x_synthesis_documents`
Stores synthesized research documents generated from one or more library books.

```sql
CREATE TABLE IF NOT EXISTS x_synthesis_documents (
    id TEXT PRIMARY KEY,
    library_id TEXT NOT NULL,
    title TEXT NOT NULL,
    template_type TEXT NOT NULL,
    topic_prompt TEXT NOT NULL,
    outline_json TEXT NOT NULL DEFAULT '[]',
    content_markdown TEXT NOT NULL,
    sources_json TEXT NOT NULL DEFAULT '[]',
    word_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_x_synthesis_documents_library ON x_synthesis_documents (library_id);
```

---

## 2. Domain Models (Pydantic v2: `backend/domain/synthesis.py`)

### `SynthesisSection`
```python
class SynthesisSection(BaseModel):
    title: str
    content: str
    citations: list[str] = Field(default_factory=list)
```

### `SynthesisSource`
```python
class SynthesisSource(BaseModel):
    book_id: int
    book_title: str
    authors: str
    chapters_cited: list[str] = Field(default_factory=list)
```

### `SynthesisDocument`
```python
class SynthesisDocument(BaseModel):
    id: str
    library_id: str
    title: str
    template_type: Literal["topic_brief", "literature_review", "executive_summary", "custom_research"]
    topic_prompt: str
    outline: list[str] = Field(default_factory=list)
    content_markdown: str
    sources: list[SynthesisSource] = Field(default_factory=list)
    word_count: int = 0
    created_at: datetime
    updated_at: datetime
```

### `SynthesisJobStatus`
```python
class SynthesisJobStatus(BaseModel):
    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    stage: str
    percent_complete: int
    document_id: str | None = None
    error: str | None = None
```
