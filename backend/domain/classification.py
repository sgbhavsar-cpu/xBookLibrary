"""Domain models for AI classification, dual taxonomies, and virtual bookshelves."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    """Represents bibliographic subject classification output."""

    book_id: int
    bisac_code: str  # e.g., 'COM051010'
    bisac_heading: str  # e.g., 'COMPUTERS / Programming / Software Development'
    ddc_code: str  # e.g., '005.1'
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    suggested_tags: List[str] = Field(default_factory=list)
    secondary_bisac: Optional[str] = None
    secondary_ddc: Optional[str] = None
    reasoning: Optional[str] = None
    applied: bool = False
    proposal_id: Optional[str] = None


class TaxonomyNode(BaseModel):
    """Represents a category in a user-defined hierarchical category tree."""

    id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str
    path: str  # Materialized path, e.g. '/Computer Science/Artificial Intelligence'
    description: Optional[str] = None
    order_index: int = 0
    children: List["TaxonomyNode"] = Field(default_factory=list)


class Bookshelf(BaseModel):
    """Represents a manual or rule-based virtual bookshelf collection."""

    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_smart: bool = False
    rule_expression: Optional[str] = None  # e.g. 'ddc:005.*'
    book_count: int = 0
    created_at: Optional[datetime] = None
