"""Unit tests for OnlineMetadataService."""

import pytest
import respx
import httpx

from backend.services.online_metadata_service import OnlineMetadataService


@pytest.mark.asyncio
@respx.mock
async def test_search_metadata_mocked_providers():
    """Verify concurrent querying, parsing, and confidence scoring of Google Books and OpenLibrary."""
    # 1. Mock Google Books
    google_mock_url = "https://www.googleapis.com/books/v1/volumes?q=intitle:Dune+inauthor:Frank%20Herbert&maxResults=8"
    google_response = {
        "items": [
            {
                "volumeInfo": {
                    "title": "Dune",
                    "authors": ["Frank Herbert"],
                    "publisher": "Chilton Books",
                    "publishedDate": "1965",
                    "description": "Epic science fiction novel.",
                    "categories": ["Fiction", "Science Fiction"],
                    "averageRating": 4.5,
                    "industryIdentifiers": [
                        {"type": "ISBN_13", "identifier": "9780441172719"}
                    ],
                    "imageLinks": {
                        "thumbnail": "http://books.google.com/books/cover_dune.jpg"
                    },
                }
            }
        ]
    }
    respx.get(google_mock_url).mock(return_value=httpx.Response(200, json=google_response))

    # 2. Mock OpenLibrary
    ol_mock_url = "https://openlibrary.org/search.json?title=Dune&author=Frank+Herbert"
    ol_response = {
        "docs": [
            {
                "title": "Dune",
                "author_name": ["Frank Herbert"],
                "publisher": ["Ace Books"],
                "first_publish_year": 1965,
                "isbn": ["9780441172719"],
                "cover_i": 123456,
                "subject": ["Science Fiction", "Arrakis"],
            }
        ]
    }
    respx.get(ol_mock_url).mock(return_value=httpx.Response(200, json=ol_response))

    service = OnlineMetadataService()
    candidates = await service.search_metadata(title="Dune", author="Frank Herbert")

    assert len(candidates) >= 2
    sources = {c.source for c in candidates}
    assert "google_books" in sources
    assert "openlibrary" in sources

    # Top candidate should have high confidence (> 0.8)
    top_cand = candidates[0]
    assert top_cand.title == "Dune"
    assert "Frank Herbert" in top_cand.authors
    assert top_cand.confidence_score >= 0.8
    assert top_cand.isbn == "9780441172719"
    # HTTP image links should be converted to HTTPS
    if top_cand.source == "google_books":
        assert top_cand.cover_url.startswith("https://")
