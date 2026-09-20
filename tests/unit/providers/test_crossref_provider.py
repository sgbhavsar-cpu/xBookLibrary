"""Unit tests for CrossRefProvider with respx HTTP mocking."""

from pathlib import Path

import pytest
import respx

from backend.providers.crossref import CrossRefProvider
from backend.services.http_cache import HttpCache


@pytest.mark.asyncio
@respx.mock
async def test_crossref_doi_lookup(tmp_path: Path):
    cache = HttpCache(tmp_path / "cache")
    provider = CrossRefProvider(cache=cache)

    doi = "10.1145/3318464.3389700"
    mock_payload = {
        "message": {
            "title": ["Attention Is All You Need"],
            "author": [{"given": "Ashish", "family": "Vaswani"}],
            "publisher": "Association for Computing Machinery",
            "published-print": {"date-parts": [[2017]]},
            "DOI": "10.1145/3318464.3389700",
            "abstract": (
                "<jats:p>The dominant sequence transduction models are based on "
                "complex recurrent or convolutional neural networks.</jats:p>"
            ),
            "subject": ["Machine Learning", "Artificial Intelligence"],
        }
    }

    respx.get(f"https://api.crossref.org/works/{doi}").respond(200, json=mock_payload)

    result = await provider.fetch_by_doi(doi)
    assert result is not None
    assert result.title == "Attention Is All You Need"
    assert result.authors == ["Ashish Vaswani"]
    assert result.publication_year == 2017
    assert result.identifiers["doi"] == doi
    assert "<jats:p>" not in (result.description or "")
    assert "The dominant sequence transduction" in (result.description or "")


@pytest.mark.asyncio
@respx.mock
async def test_crossref_search_query():
    provider = CrossRefProvider()

    mock_search = {
        "message": {
            "items": [
                {
                    "title": ["Deep Learning"],
                    "author": [
                        {"given": "Ian", "family": "Goodfellow"},
                        {"given": "Yoshua", "family": "Bengio"},
                    ],
                    "publisher": "MIT Press",
                    "published-print": {"date-parts": [[2016]]},
                    "ISBN": ["9780262035613"],
                }
            ]
        }
    }

    respx.get("https://api.crossref.org/works").respond(200, json=mock_search)

    results = await provider.fetch_by_query("Deep Learning", author="Goodfellow")
    assert len(results) == 1
    assert results[0].title == "Deep Learning"
    assert results[0].authors == ["Ian Goodfellow", "Yoshua Bengio"]
    assert results[0].publisher == "MIT Press"
    assert results[0].publication_year == 2016
    assert results[0].isbn == "9780262035613"
