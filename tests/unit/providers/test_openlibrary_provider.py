"""Unit tests for OpenLibraryProvider with respx HTTP mocking."""

from pathlib import Path

import pytest
import respx

from backend.providers.openlibrary import OpenLibraryProvider
from backend.services.http_cache import HttpCache


@pytest.mark.asyncio
@respx.mock
async def test_openlibrary_isbn_lookup(tmp_path: Path):
    cache = HttpCache(tmp_path / "cache")
    provider = OpenLibraryProvider(cache=cache)

    isbn = "9780441172719"
    mock_payload = {
        "ISBN:9780441172719": {
            "title": "Dune",
            "authors": [{"name": "Frank Herbert"}],
            "publishers": [{"name": "Ace Books"}],
            "publish_date": "1965",
            "description": "Epic science fiction novel set on the desert planet Arrakis.",
            "subjects": [{"name": "Science Fiction"}, {"name": "Desert Planets"}],
            "cover": {
                "large": "https://covers.openlibrary.org/b/id/12345-L.jpg",
            },
            "identifiers": {"isbn_13": ["9780441172719"]},
        }
    }

    route = respx.get(
        "https://openlibrary.org/api/books",
        params={"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"},
    ).respond(200, json=mock_payload)

    result = await provider.fetch_by_isbn(isbn)
    assert route.called
    assert result is not None
    assert result.title == "Dune"
    assert result.authors == ["Frank Herbert"]
    assert result.publisher == "Ace Books"
    assert result.publication_year == 1965
    assert result.cover is not None
    assert "12345-L.jpg" in result.cover.url
    assert "Science Fiction" in result.tags

    # Second call should hit the cache without calling HTTP route
    respx.clear()
    cached_result = await provider.fetch_by_isbn(isbn)
    assert cached_result is not None
    assert cached_result.title == "Dune"


@pytest.mark.asyncio
@respx.mock
async def test_openlibrary_search_query(tmp_path: Path):
    provider = OpenLibraryProvider()

    mock_search = {
        "docs": [
            {
                "title": "Foundation",
                "author_name": ["Isaac Asimov"],
                "publisher": ["Gnome Press"],
                "first_publish_year": 1951,
                "isbn": ["9780553293357"],
                "cover_i": 9876,
            }
        ]
    }

    respx.get("https://openlibrary.org/search.json").respond(200, json=mock_search)

    results = await provider.fetch_by_query("Foundation", author="Isaac Asimov")
    assert len(results) == 1
    assert results[0].title == "Foundation"
    assert results[0].authors == ["Isaac Asimov"]
    assert results[0].publication_year == 1951
    assert results[0].cover is not None
    assert "9876-L.jpg" in results[0].cover.url
