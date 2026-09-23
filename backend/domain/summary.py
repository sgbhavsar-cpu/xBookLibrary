"""Domain models for multi-resolution AI book summarization."""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, computed_field


class ExecutiveSnapshot(BaseModel):
    """Top-level 2-minute synthesis capturing the essence of the book."""

    hook: str  # Engaging one-sentence overview
    core_thesis: str  # Central argument, problem solved, or primary premise
    target_audience: str  # Intended readership or field
    key_arguments: List[str] = Field(default_factory=list)  # 3 to 5 primary arguments
    estimated_reading_time_minutes: int = 0  # Estimated minutes to read full work


class ChapterSummary(BaseModel):
    """Granular analytical breakdown of an individual chapter or section."""

    chapter_index: int  # Sequential chapter index (1-based)
    chapter_title: str  # Heading or title of the chapter/section
    summary: str  # Narrative synthesis of chapter progression
    key_takeaways: List[str] = Field(default_factory=list)  # Specific learnings/takeaways
    important_quotes: List[str] = Field(default_factory=list)  # Direct quotes or notable excerpts

    @computed_field
    def key_points(self) -> List[str]:
        return self.key_takeaways


class ConceptualIndex(BaseModel):
    """Conceptual frameworks, mental models, quotes, and practical action steps."""

    frameworks: List[str] = Field(default_factory=list)  # Named theories or mental models
    key_takeaways: List[str] = Field(default_factory=list)  # Overarching high-impact insights
    quotable_moments: List[Dict[str, str]] = Field(
        default_factory=list
    )  # List of {"quote": str, "source": str}
    action_items: List[str] = Field(default_factory=list)  # Practical applications or action items


class SummaryMetadata(BaseModel):
    """Execution metadata and audit trail for the generated summary."""

    model_name: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0
    word_count: int = 0
    prompt_version: str = "v1.0"
    custom_instructions: Optional[str] = None


class BookSummary(BaseModel):
    """Aggregate root entity representing a complete multi-resolution book summary."""

    id: Optional[int] = None
    book_id: int
    executive_snapshot: ExecutiveSnapshot
    chapters: List[ChapterSummary] = Field(default_factory=list)
    conceptual_index: ConceptualIndex
    metadata: SummaryMetadata

    # Backward compatibility fields for frontend clients
    @computed_field
    def executive_summary(self) -> str:
        snap = self.executive_snapshot
        args = "\n".join(f"• {a}" for a in snap.key_arguments)
        if args:
            return f"{snap.hook}\n\n{snap.core_thesis}\n\nKey Arguments:\n{args}"
        return f"{snap.hook}\n\n{snap.core_thesis}"

    @computed_field
    def detailed_summary(self) -> str:
        return self.executive_snapshot.core_thesis

    @computed_field
    def key_takeaways(self) -> List[str]:
        return self.conceptual_index.key_takeaways

    @computed_field
    def chapter_summaries(self) -> List[ChapterSummary]:
        return self.chapters

    @computed_field
    def is_stale(self) -> bool:
        return False

    @computed_field
    def model_used(self) -> str:
        return self.metadata.model_name

    @computed_field
    def generated_at(self) -> str:
        return self.metadata.generated_at.isoformat()

