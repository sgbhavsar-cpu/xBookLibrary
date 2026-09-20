"""Unit tests for GoogleBooksProvider with respx HTTP mocking."""

from pathlib import Path

import pytest
import respx

from backend.providers.google_books import GoogleBooksProvider
from backend.services.http_cache import HttpCache


@pytest.mark.asyncio
@respx.mock
async def test_google_books_isbn_lookup(tmp_path: Path):
    cache = HttpCache(tmp_path / "cache")
    provider = GoogleBooksProvider(cache=cache)

    isbn = "9780441172719"
    mock_payload = {
        "items": [
            {
                "volumeInfo": {
                    "title": "Dune",
                    "subtitle": "Chronicles of Dune",
                    "authors": ["Frank Herbert"],
                    "publisher": "Chilton Books",
                    "publishedDate": "1965-08-01",
                    "description": "Set on the desert planet Arrakis.",
                    "categories": ["Science Fiction", "Classics"],
                    "industryIdentifiers": [{"type": "ISBN_13", "identifier": "9780441172719"}],
                    "imageLinks": {
                        "thumbnail": "http://books.google.com/books/content?id=123&zoom=1&edge=curl&source=gbs_api"
                    },
                }
            }
        ]
    }

    route = respx.get("https://www.googleapis.com/books/v1/volumes").respond(200, json=mock_payload)

    result = await provider.fetch_by_isbn(isbn)
    assert route.called
    assert result is not None
    assert result.title == "Dune: Chronicles of Dune"
    assert result.authors == ["Frank Herbert"]
    assert result.publisher == "Chilton Books"
    assert result.publication_year == 1965
    assert result.cover is not None
    # Verify URL was cleaned to HTTPS and zoom=2 without edge=curl
    assert "https://" in result.cover.url
    assert "zoom=2" in result.cover.url
    assert "edge=curl" not in result.cover.url


@pytest.mark.asyncio
@respx.mock
async def test_google_books_search_query():
    provider = GoogleBooksProvider()

    mock_search = {
        "items": [
            {
                "volumeInfo": {
                    "title": "Neuromancer",
                    "authors": ["William Gibson"],
                    "publisher": "Ace",
                    "publishedDate": "1984",
                    "categories": ["Cyberpunk"],
                }
            }
        ]
    }

    respx.get("https://www.googleapis.com/books/v1/volumes").respond(200, json=mock_search)

    results = await provider.fetch_by_query("Neuromancer", author="William Gibson")
    assert len(results) == 1
    assert results[0].title == "Neuromancer"
    assert results[0].authors == ["William Gibson"]
    assert results[0].publication_year == 1984
    assert "Cyberpunk" in results[0].tags
