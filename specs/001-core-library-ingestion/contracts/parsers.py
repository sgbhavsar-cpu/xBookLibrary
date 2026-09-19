"""Domain interface and contracts for book parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class TocItem:
    title: str
    level: int = 0
    page_number: Optional[int] = None
    anchor_href: Optional[str] = None
    children: List["TocItem"] = field(default_factory=list)


@dataclass
class ParsedBookPayload:
    title: str
    authors: List[str] = field(default_factory=list)
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    identifiers: Dict[str, str] = field(default_factory=dict)  # isbn, doi, asin, etc.
    tags: List[str] = field(default_factory=list)
    series_name: Optional[str] = None
    series_index: Optional[float] = None
    cover_bytes: Optional[bytes] = None
    cover_mime_type: Optional[str] = None
    table_of_contents: List[TocItem] = field(default_factory=list)
    sample_text: str = ""  # First ~2,000 words extracted for downstream AI analysis
    raw_format: str = ""  # EPUB, PDF, MOBI, AZW3, TXT, DOCX, CBZ, CBR


class BookParserStrategy(ABC):
    """Abstract interface for format-specific book parsers."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedBookPayload:
        """Parse a book file into a standardized domain payload.

        Args:
            file_path: Absolute path to the book file on disk.

        Returns:
            ParsedBookPayload with normalized metadata, TOC, cover, and sample text.

        Raises:
            CorruptedBookError: If the file header or archive is unreadable.
            DrmProtectedError: If the content is encrypted with proprietary DRM.
        """
        pass
