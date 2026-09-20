"""Domain models for Library-Wise RAG, Vector Search, and Conversational QA."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class VectorChunk(BaseModel):
    """Represents a discrete semantic text chunk stored in LanceDB."""

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


class Citation(BaseModel):
    """Verifiable source citation grounding an assistant response."""

    book_id: int
    book_title: str
    authors: str
    chapter_index: int
    chapter_title: str
    snippet: str
    score: float


class SearchResult(BaseModel):
    """Result of hybrid or vector search across the library."""

    chunk_id: str
    book_id: int
    book_title: str
    authors: str
    chapter_index: int
    chapter_title: str
    content: str
    score: float
    match_type: Literal["vector", "keyword", "hybrid"] = "hybrid"


class ChatMessage(BaseModel):
    """An individual message in a conversational RAG session."""

    id: str
    session_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    citations: list[Citation] = Field(default_factory=list)
    created_at: datetime


class ChatSession(BaseModel):
    """A conversational chat thread scoped to a library or specific book."""

    id: str
    library_id: str
    book_id: int | None = None
    title: str
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class IndexStatus(BaseModel):
    """Indexing statistics and health metrics for a library."""

    total_books: int
    indexed_books: int
    pending_books: int
    total_chunks: int
    last_indexed_at: datetime | None = None
