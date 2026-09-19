"""Unit tests for MobiParser."""

from pathlib import Path

from backend.parsers.mobi_parser import MobiParser
from tests.fixtures.generators import create_sample_mobi


def test_mobi_parser_extraction(tmp_path: Path):
    mobi_path = tmp_path / "androids.mobi"
    create_sample_mobi(
        mobi_path, title="Do Androids Dream of Electric Sheep?", author="Philip K. Dick"
    )

    parser = MobiParser()
    payload = parser.parse(mobi_path)

    assert "Androids Dream" in payload.title
    assert "Philip K. Dick" in payload.authors
    assert payload.raw_format == "MOBI"
