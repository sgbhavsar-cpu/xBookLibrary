"""DOCX format parser implementation."""

from pathlib import Path
from typing import List

import docx

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
    TocItem,
)


class DocxParser(BookParserStrategy):
    """Extracts metadata, headings as outline, and text from DOCX documents."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        try:
            doc = docx.Document(str(file_path))
        except Exception as e:
            raise CorruptedBookError(f"Unable to read DOCX file: {e}") from e

        # Metadata from core properties
        props = doc.core_properties
        title = props.title.strip() if props.title and props.title.strip() else file_path.stem
        authors = (
            [props.author.strip()] if props.author and props.author.strip() else ["Unknown Author"]
        )
        pub_year = props.created.year if props.created else None

        # Outline & Sample Text from paragraphs
        table_of_contents: List[TocItem] = []
        sample_paragraphs = []

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style and p.style.name else ""
            if "heading 1" in style_name:
                table_of_contents.append(TocItem(title=text, level=1))
            elif "heading 2" in style_name:
                table_of_contents.append(TocItem(title=text, level=2))
            elif "heading 3" in style_name:
                table_of_contents.append(TocItem(title=text, level=3))

            if len(sample_paragraphs) < 20:
                sample_paragraphs.append(text)

        sample_text = "\n\n".join(sample_paragraphs)[:3000]

        return ParsedBookPayload(
            title=title,
            authors=authors,
            publication_year=pub_year,
            table_of_contents=table_of_contents,
            sample_text=sample_text,
            raw_format="DOCX",
        )
