"""Domain models for in-place metadata editing, online metadata retrieval, and format management."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BookMetadataUpdateRequest(BaseModel):
    """Request payload for updating a single book's metadata."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    sort_title: Optional[str] = Field(default=None, max_length=500)
    authors: Optional[List[str]] = Field(default=None)
    author_sort: Optional[str] = Field(default=None, max_length=500)
    publisher: Optional[str] = Field(default=None, max_length=255)
    pubdate: Optional[str] = Field(default=None)  # ISO date string or year
    rating: Optional[int] = Field(default=None, ge=0, le=5)
    tags: Optional[List[str]] = Field(default=None)
    series_name: Optional[str] = Field(default=None, max_length=255)
    series_index: Optional[float] = Field(default=None, ge=0.0)
    isbn: Optional[str] = Field(default=None, max_length=50)
    identifiers: Optional[Dict[str, str]] = Field(default=None)
    comments: Optional[str] = Field(default=None)  # Rich text / HTML / Markdown description
    custom_values: Optional[Dict[str, Any]] = Field(default=None)


class OnlineMetadataCandidate(BaseModel):
    """Candidate record returned from external book metadata providers."""

    source: str = Field(description="'google_books' or 'openlibrary'")
    title: str
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)
    cover_url: Optional[str] = None
    rating: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class OnlineMetadataSearchRequest(BaseModel):
    """Query payload for fetching online metadata."""

    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None


class BulkMetadataUpdateRequest(BaseModel):
    """Request payload for batch-updating multiple books."""

    book_ids: List[int] = Field(min_length=1)
    add_tags: List[str] = Field(default_factory=list)
    remove_tags: List[str] = Field(default_factory=list)
    set_author: Optional[str] = None
    set_publisher: Optional[str] = None
    set_rating: Optional[int] = Field(default=None, ge=0, le=5)
    set_series: Optional[str] = None
    auto_increment_series: bool = False
    series_start_index: float = Field(default=1.0, ge=0.0)


class BulkMetadataUpdateResult(BaseModel):
    """Result summary of a bulk metadata update operation."""

    total_requested: int
    updated_count: int
    failed_ids: List[int] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class FormatAddResponse(BaseModel):
    """Response returned when an additional format is attached to a book."""

    book_id: int
    format: str
    file_path: str
    uncompressed_size: int
    formats: List[str]


class FormatDeleteResponse(BaseModel):
    """Response returned when a format is removed from a book."""

    book_id: int
    deleted_format: str
    remaining_formats: List[str]


class BookDeleteResponse(BaseModel):
    """Response returned when a book is completely deleted from the library and disk."""

    book_id: int
    title: str
    deleted_from_disk: bool
    status: str = "deleted"


class BulkDeleteRequest(BaseModel):
    """Request payload for bulk book deletion."""

    book_ids: List[int] = Field(min_length=1)


class BulkDeleteResult(BaseModel):
    """Summary of bulk book deletion results."""

    total_requested: int
    deleted_count: int
    failed_ids: List[int] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

