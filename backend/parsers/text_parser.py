"""Plain text and Markdown format parser implementation."""

import re
from pathlib import Path
from typing import List

import chardet

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
    TocItem,
)


class TextParser(BookParserStrategy):
    """Extracts title, headers as TOC, and content from text and markdown files."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        try:
            raw_bytes = file_path.read_bytes()
        except Exception as e:
            raise CorruptedBookError(f"Cannot read file: {e}") from e

        # Detect encoding
        detected = chardet.detect(raw_bytes[:10000])
        encoding = detected.get("encoding") or "utf-8"

        try:
            text = raw_bytes.decode(encoding, errors="replace")
        except Exception:
            text = raw_bytes.decode("utf-8", errors="ignore")

        lines = [line.strip() for line in text.splitlines()]
        non_empty = [line for line in lines if line]

        # Infer title
        title = file_path.stem
        if non_empty:
            first_line = non_empty[0]
            # Strip markdown # header if present
            clean_first = re.sub(r"^#+\s*", "", first_line).strip()
            if clean_first and len(clean_first) < 120:
                title = clean_first

        # Extract Markdown/Section headings as TOC
        table_of_contents: List[TocItem] = []
        for line in non_empty:
            if line.startswith("#"):
                match = re.match(r"^(#+)\s*(.*)", line)
                if match:
                    hashes, heading_text = match.groups()
                    level = len(hashes)
                    table_of_contents.append(TocItem(title=heading_text.strip(), level=level))
            elif re.match(r"^(chapter|part|section)\s+\d+", line, re.IGNORECASE):
                table_of_contents.append(TocItem(title=line, level=1))

        sample_text = "\n\n".join(non_empty[:30])[:3000]

        return ParsedBookPayload(
            title=title,
            authors=["Unknown Author"],
            table_of_contents=table_of_contents,
            sample_text=sample_text,
            raw_format="TXT" if file_path.suffix.lower() == ".txt" else "MD",
        )
