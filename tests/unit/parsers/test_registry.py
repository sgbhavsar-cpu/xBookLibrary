"""Unit tests for ParserRegistry."""

from pathlib import Path

import pytest

from backend.domain.parsers import CorruptedBookError
from backend.parsers import (
    AudiobookParser,
    ComicParser,
    DocxParser,
    EpubParser,
    MobiParser,
    ParserRegistry,
    PdfParser,
    TextParser,
)


def test_parser_registry_resolution():
    assert isinstance(ParserRegistry.get_parser(Path("book.epub")), EpubParser)
    assert isinstance(ParserRegistry.get_parser(Path("manual.pdf")), PdfParser)
    assert isinstance(ParserRegistry.get_parser(Path("novel.mobi")), MobiParser)
    assert isinstance(ParserRegistry.get_parser(Path("novel.azw3")), MobiParser)
    assert isinstance(ParserRegistry.get_parser(Path("comic.cbz")), ComicParser)
    assert isinstance(ParserRegistry.get_parser(Path("document.docx")), DocxParser)
    assert isinstance(ParserRegistry.get_parser(Path("notes.txt")), TextParser)
    assert isinstance(ParserRegistry.get_parser(Path("readme.md")), TextParser)
    assert isinstance(ParserRegistry.get_parser(Path("audio.m4b")), AudiobookParser)
    assert isinstance(ParserRegistry.get_parser(Path("audio.mp3")), AudiobookParser)

    with pytest.raises(CorruptedBookError):
        ParserRegistry.get_parser(Path("unsupported.xyz"))
