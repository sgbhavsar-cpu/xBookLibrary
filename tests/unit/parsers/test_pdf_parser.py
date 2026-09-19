"""Unit tests for PdfParser."""

from pathlib import Path

from backend.parsers.pdf_parser import PdfParser
from tests.fixtures.generators import create_sample_pdf


def test_pdf_parser_extraction(tmp_path: Path):
    pdf_path = tmp_path / "foundation.pdf"
    create_sample_pdf(pdf_path, title="Foundation", author="Isaac Asimov")

    parser = PdfParser()
    payload = parser.parse(pdf_path)

    assert payload.title == "Foundation"
    assert "Isaac Asimov" in payload.authors
    assert payload.cover_bytes is not None
    assert len(payload.cover_bytes) > 0
    assert payload.cover_mime_type == "image/jpeg"
    assert len(payload.table_of_contents) >= 1
    assert "Psychohistorians" in payload.table_of_contents[0].title
