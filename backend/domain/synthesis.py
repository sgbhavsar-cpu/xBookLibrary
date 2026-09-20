"""Domain models for Multi-Book Document Synthesis & Knowledge Brief Studio."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SynthesisSection(BaseModel):
    """An individual section within a synthesized brief."""

    title: str
    content: str
    citations: list[str] = Field(default_factory=list)


class SynthesisSource(BaseModel):
    """A book source cited within the synthesized document."""

    book_id: int
    book_title: str
    authors: str
    chapters_cited: list[str] = Field(default_factory=list)


class SynthesisDocument(BaseModel):
    """A completed multi-book synthesized research document."""

    id: str
    library_id: str
    title: str
    template_type: Literal[
        "topic_brief", "literature_review", "executive_summary", "custom_research"
    ]
    topic_prompt: str
    outline: list[str] = Field(default_factory=list)
    content_markdown: str
    sources: list[SynthesisSource] = Field(default_factory=list)
    word_count: int = 0
    created_at: datetime
    updated_at: datetime


class SynthesisJobStatus(BaseModel):
    """Status tracker for asynchronous document synthesis generation."""

    job_id: str
    status: Literal["queued", "running", "completed", "failed"]
    stage: str
    percent_complete: int
    document_id: str | None = None
    error: str | None = None
