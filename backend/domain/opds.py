from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class OPDSEntry(BaseModel):
    id: str = Field(..., description="Unique URI identifier for book")
    title: str = Field(..., description="Book title")
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    authors: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    acquisition_links: List[Dict[str, str]] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)


class OPDSLink(BaseModel):
    rel: str
    href: str
    type: str
    title: Optional[str] = None


class OPDSFeed(BaseModel):
    id: str
    title: str
    updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author_name: str = "xBookLibrary"
    icon_url: Optional[str] = None
    links: List[OPDSLink] = Field(default_factory=list)
    entries: List[OPDSEntry] = Field(default_factory=list)
