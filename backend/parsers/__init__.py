"""Pluggable parser registry and factory."""

from pathlib import Path
from typing import Dict, Set

from backend.domain.parsers import BookParserStrategy, CorruptedBookError
from backend.parsers.comic_parser import ComicParser
from backend.parsers.docx_parser import DocxParser
from backend.parsers.epub_parser import EpubParser
from backend.parsers.mobi_parser import MobiParser
from backend.parsers.pdf_parser import PdfParser
from backend.parsers.text_parser import TextParser


class ParserRegistry:
    """Factory and registry mapping file extensions to parser strategies."""

    _parsers: Dict[str, BookParserStrategy] = {
        ".epub": EpubParser(),
        ".pdf": PdfParser(),
        ".mobi": MobiParser(),
        ".azw": MobiParser(),
        ".azw3": MobiParser(),
        ".cbz": ComicParser(),
        ".cbr": ComicParser(),
        ".docx": DocxParser(),
        ".txt": TextParser(),
        ".md": TextParser(),
    }

    @classmethod
    def get_supported_extensions(cls) -> Set[str]:
        return set(cls._parsers.keys())

    @classmethod
    def get_parser(cls, file_path: Path) -> BookParserStrategy:
        ext = file_path.suffix.lower()
        if ext not in cls._parsers:
            supported = ", ".join(sorted(cls.get_supported_extensions()))
            raise CorruptedBookError(
                f"Unsupported file format '{ext}'. Supported formats: {supported}"
            )
        return cls._parsers[ext]


__all__ = [
    "ParserRegistry",
    "EpubParser",
    "PdfParser",
    "MobiParser",
    "ComicParser",
    "DocxParser",
    "TextParser",
]
