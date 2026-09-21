from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ReadingProgress(BaseModel):
    id: Optional[int] = None
    book_id: int = Field(..., description="Target book ID")
    format: str = Field(..., description="Format being read, e.g. EPUB, PDF, CBZ")
    location: str = Field(..., description="CFI string or page number")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage 0.0-100.0")
    total_seconds: int = Field(default=0, ge=0, description="Total seconds spent reading")
    last_read_at: Optional[datetime] = None


class ReadingProgressCreateRequest(BaseModel):
    format: str = Field(..., description="Format being read, e.g. EPUB, PDF, CBZ")
    location: str = Field(..., description="Current CFI or page location")
    progress_percent: float = Field(default=0.0, ge=0.0, le=100.0, description="Completion percentage")
    seconds_increment: int = Field(default=0, ge=0, description="Seconds elapsed since last heartbeat/progress sync")


class Annotation(BaseModel):
    id: str = Field(..., description="Unique UUID for annotation")
    book_id: int = Field(..., description="Target book ID")
    format: str = Field(..., description="EPUB, PDF, etc.")
    location: str = Field(..., description="CFI or page number")
    selected_text: str = Field(..., description="Excerpt highlighted")
    color: str = Field(default="yellow", description="Highlight color: yellow, green, blue, pink, purple")
    note_text: Optional[str] = Field(default=None, description="Optional user comment or thought")
    chapter_title: Optional[str] = Field(default=None, description="Chapter or section heading")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AnnotationCreateRequest(BaseModel):
    format: str = Field(..., description="Format: EPUB, PDF, etc.")
    location: str = Field(..., description="CFI or page number")
    selected_text: str = Field(..., min_length=1, description="Highlighted text")
    color: str = Field(default="yellow", description="Color code or name")
    note_text: Optional[str] = None
    chapter_title: Optional[str] = None


class Bookmark(BaseModel):
    id: str = Field(..., description="Unique UUID for bookmark")
    book_id: int = Field(..., description="Target book ID")
    format: str = Field(..., description="Format: EPUB, PDF, CBZ")
    location: str = Field(..., description="CFI or page number")
    title: str = Field(..., description="User label or chapter title")
    created_at: Optional[datetime] = None


class BookmarkCreateRequest(BaseModel):
    format: str = Field(..., description="Format: EPUB, PDF, CBZ")
    location: str = Field(..., description="CFI or page number")
    title: str = Field(..., min_length=1, description="Bookmark label")


class ComicPageInfo(BaseModel):
    index: int = Field(..., description="0-indexed page sequence")
    filename: str = Field(..., description="Internal image filename inside archive")
    url: str = Field(..., description="Streaming image endpoint URL")


class ComicManifest(BaseModel):
    book_id: int
    total_pages: int
    pages: List[ComicPageInfo] = Field(default_factory=list)
    series_name: Optional[str] = None
    issue_number: Optional[float] = None
