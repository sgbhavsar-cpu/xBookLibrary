"""Unit tests for ComicParser."""

from pathlib import Path

from backend.parsers.comic_parser import ComicParser
from tests.fixtures.generators import create_sample_cbz


def test_comic_parser_extraction(tmp_path: Path):
    cbz_path = tmp_path / "saga_01.cbz"
    create_sample_cbz(cbz_path, title="Saga Volume 1", series="Saga")

    parser = ComicParser()
    payload = parser.parse(cbz_path)

    assert payload.title == "Saga Volume 1"
    assert "Brian K. Vaughan" in payload.authors
    assert payload.series_name == "Saga"
    assert payload.series_index == 1.0
    assert payload.publication_year == 2012
    assert payload.publisher == "Image Comics"
    assert payload.cover_bytes is not None
    assert len(payload.cover_bytes) > 0
    assert "galactic war" in payload.description.lower()
