"""Unit tests for DocxParser and TextParser."""

from pathlib import Path

from backend.parsers.docx_parser import DocxParser
from backend.parsers.text_parser import TextParser
from tests.fixtures.generators import create_sample_docx, create_sample_txt


def test_docx_parser_extraction(tmp_path: Path):
    docx_path = tmp_path / "notes.docx"
    create_sample_docx(docx_path, title="Pitchblende Research", author="Marie Curie")

    parser = DocxParser()
    payload = parser.parse(docx_path)

    assert payload.title == "Pitchblende Research"
    assert "Marie Curie" in payload.authors
    assert len(payload.table_of_contents) >= 2
    assert "Introduction" in payload.table_of_contents[0].title
    assert "radioactive" in payload.sample_text.lower()


def test_text_parser_extraction(tmp_path: Path):
    txt_path = tmp_path / "manifesto.txt"
    create_sample_txt(txt_path, title="The Cyberpunk Manifesto")

    parser = TextParser()
    payload = parser.parse(txt_path)

    assert "Cyberpunk Manifesto" in payload.title
    assert len(payload.table_of_contents) >= 2
    assert any("electronic minds" in toc.title.lower() for toc in payload.table_of_contents)
    assert "digital wanderers" in payload.sample_text.lower()
