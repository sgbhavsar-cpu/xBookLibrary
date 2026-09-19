"""Domain entities for xBookLibrary."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BookFormat(BaseModel):
    id: Optional[int] = None
    book_id: Optional[int] = None
    format: str  # e.g., 'EPUB', 'PDF', 'MOBI'
    uncompressed_size: int
    name: str  # Filename without extension
    file_path: Optional[str] = None
    sha256: Optional[str] = None


class Author(BaseModel):
    id: Optional[int] = None
    name: str
    sort: Optional[str] = None
    link: str = ""


class Identifier(BaseModel):
    id: Optional[int] = None
    book_id: Optional[int] = None
    type: str  # 'isbn', 'doi', 'asin', etc.
    val: str


class TocNode(BaseModel):
    id: Optional[int] = None
    book_id: Optional[int] = None
    parent_id: Optional[int] = None
    title: str
    level: int = 0
    page_number: Optional[int] = None
    anchor_href: Optional[str] = None
    order_index: int = 0


class Book(BaseModel):
    id: Optional[int] = None
    title: str
    sort_title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    isbn: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    series_name: Optional[str] = None
    series_index: Optional[float] = 1.0
    path: str = ""  # Relative path under library root: Author/Title (Year)
    has_cover: bool = False
    formats: List[BookFormat] = Field(default_factory=list)
    toc: List[TocNode] = Field(default_factory=list)
    uuid: Optional[str] = None
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None


class Library(BaseModel):
    id: str
    name: str
    path: str
    is_calibre_adopted: bool = False
    auto_watch: bool = False
    auto_import_folder: Optional[str] = None
    book_count: int = 0
    created_at: Optional[datetime] = None


class IngestionJob(BaseModel):
    id: str
    status: IngestionStatus = IngestionStatus.PENDING
    source_path: Optional[str] = None
    book_id: Optional[int] = None
    error_message: Optional[str] = None
    total_files: int = 0
    processed_files: int = 0
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
