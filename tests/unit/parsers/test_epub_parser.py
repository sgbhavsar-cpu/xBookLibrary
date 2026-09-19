"""Unit tests for EpubParser."""

from pathlib import Path

from backend.parsers.epub_parser import EpubParser
from tests.fixtures.generators import create_sample_epub


def test_epub_parser_extraction(tmp_path: Path):
    epub_path = tmp_path / "holmes.epub"
    create_sample_epub(
        epub_path, title="The Adventures of Sherlock Holmes", author="Arthur Conan Doyle"
    )

    parser = EpubParser()
    payload = parser.parse(epub_path)

    assert payload.title == "The Adventures of Sherlock Holmes"
    assert "Arthur Conan Doyle" in payload.authors
    assert payload.publication_year == 1892
    assert payload.publisher == "George Newnes"
    assert (
        "9781234567890" in payload.identifiers.values()
        or "urn:isbn:9781234567890" in payload.identifiers.values()
    )
    assert "Mystery" in payload.tags
    assert payload.cover_bytes is not None
    assert len(payload.cover_bytes) > 0
    assert payload.cover_mime_type == "image/jpeg"
    assert len(payload.table_of_contents) >= 2
    assert "Scandal in Bohemia" in payload.table_of_contents[0].title
    assert "Sherlock Holmes" in payload.sample_text
