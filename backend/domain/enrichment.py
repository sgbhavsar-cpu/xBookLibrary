"""Domain entities and value objects for agentic metadata enrichment."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISCARDED = "DISCARDED"


class CoverCandidate(BaseModel):
    url: Optional[str] = None
    bytes_data: Optional[bytes] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: str = "image/jpeg"
    source: str


class CandidateMetadata(BaseModel):
    source: str  # "openlibrary" | "google_books" | "crossref" | "litellm_vision"
    isbn: Optional[str] = None
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    language: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    series_name: Optional[str] = None
    series_index: Optional[float] = None
    cover: Optional[CoverCandidate] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class ProposedField(BaseModel):
    field_name: str
    current_value: Optional[Any] = None
    proposed_value: Optional[Any] = None
    source: str
    confidence: float = 1.0
    is_conflicting: bool = False


class MetadataProposal(BaseModel):
    id: str
    book_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ProposalStatus = ProposalStatus.PENDING
    is_exact_isbn: bool = False
    composite_confidence: float = 1.0
    fields: Dict[str, ProposedField] = Field(default_factory=dict)
    candidate_covers: List[CoverCandidate] = Field(default_factory=list)
