"""Unit tests for EnrichmentOrchestrator decision safeguards and cascade logic."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.domain.enrichment import CandidateMetadata, CoverCandidate
from backend.services.enrichment_orchestrator import EnrichmentOrchestrator
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_exact_isbn_auto_applied(tmp_path: Path):
    """Verifies that an exact 100% ISBN match auto-applies directly without human review."""
    lib_dir = tmp_path / "TestLibrary"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Enrichment Lib", set_active=False)

    # Ingest a sample book with ISBN
    epub_path = tmp_path / "dune.epub"
    create_sample_epub(epub_path, title="Dune Initial", author="Frank H.")

    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_path)

    # Set ISBN on book
    import aiosqlite

    async with aiosqlite.connect(lib_dir / "metadata.db") as db:
        await db.execute("UPDATE books SET isbn = '9780441172719' WHERE id = ?", (book.id,))
        await db.commit()

    orchestrator = EnrichmentOrchestrator(lib_dir)

    # Mock OpenLibrary and GoogleBooks ISBN responses
    mock_ol = CandidateMetadata(
        source="openlibrary",
        isbn="9780441172719",
        title="Dune",
        authors=["Frank Herbert"],
        publisher="Ace Books",
        publication_year=1965,
    )
    mock_gb = CandidateMetadata(
        source="google_books",
        isbn="9780441172719",
        title="Dune",
        authors=["Frank Herbert"],
        description="The definitive science fiction masterpiece.",
        cover=CoverCandidate(url="https://books.google.com/dune_cover.jpg", source="google_books"),
    )

    with patch.object(
        orchestrator.openlibrary, "fetch_by_isbn", new_callable=AsyncMock
    ) as mock_ol_fetch:
        with patch.object(
            orchestrator.google_books, "fetch_by_isbn", new_callable=AsyncMock
        ) as mock_gb_fetch:
            mock_ol_fetch.return_value = mock_ol
            mock_gb_fetch.return_value = mock_gb

            result = await orchestrator.enrich_book(book.id or 1)

            assert result.status == "APPLIED"
            assert result.proposal_id is None

            # Verify Calibre SQLite was updated
            updated_book = await orchestrator._get_book_record(book.id or 1)
            assert updated_book is not None
            assert updated_book.title == "Dune"
            assert updated_book.authors == ["Frank Herbert"]
            assert updated_book.publisher == "Ace Books"
            assert updated_book.publication_year == 1965
            assert updated_book.description == "The definitive science fiction masterpiece."


@pytest.mark.asyncio
async def test_non_isbn_staged_for_review(tmp_path: Path):
    """Verifies that non-ISBN title search matches are staged in .vectors/staging/ for review."""
    lib_dir = tmp_path / "TestLibrary"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Review Lib", set_active=False)

    epub_path = tmp_path / "neuromancer.epub"
    create_sample_epub(epub_path, title="Neuromancer", author="William Gibson")

    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_path)

    # Clear ISBN so it triggers title search
    import aiosqlite

    async with aiosqlite.connect(lib_dir / "metadata.db") as db:
        await db.execute("UPDATE books SET isbn = NULL WHERE id = ?", (book.id,))
        await db.commit()

    orchestrator = EnrichmentOrchestrator(lib_dir)

    mock_search = CandidateMetadata(
        source="google_books",
        isbn="9780441569595",
        title="Neuromancer: Sprawl Trilogy",
        authors=["William Gibson"],
        publisher="Ace",
        publication_year=1984,
        description="The sky above the port was the color of television.",
    )

    with patch.object(
        orchestrator.openlibrary, "fetch_by_query", new_callable=AsyncMock
    ) as mock_ol_q:
        with patch.object(
            orchestrator.google_books, "fetch_by_query", new_callable=AsyncMock
        ) as mock_gb_q:
            mock_ol_q.return_value = []
            mock_gb_q.return_value = [mock_search]

            result = await orchestrator.enrich_book(book.id or 1)

            assert result.status == "STAGED_FOR_REVIEW"
            assert result.proposal_id is not None

            # Verify proposal is staged as JSON file
            staging_file = lib_dir / ".vectors" / "staging" / f"{result.proposal_id}.json"
            assert staging_file.exists()

            proposal = orchestrator.proposal_mgr.get_proposal(result.proposal_id)
            assert proposal is not None
            assert proposal.book_id == book.id
            assert proposal.fields["title"].proposed_value == "Neuromancer: Sprawl Trilogy"
