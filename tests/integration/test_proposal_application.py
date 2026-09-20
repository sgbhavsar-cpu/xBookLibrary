"""Integration test for applying staged proposals to Calibre storage."""

from pathlib import Path

import pytest

from backend.domain.enrichment import MetadataProposal, ProposedField
from backend.services.enrichment_orchestrator import EnrichmentOrchestrator
from backend.services.ingestion_service import IngestionService
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_apply_proposal_updates_calibre_and_cleans_staging(tmp_path: Path):
    """Verifies atomic update of Calibre SQLite, OPF rewriting, and staging cleanup."""
    lib_dir = tmp_path / "IntegrationLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Integration Lib", set_active=False)

    # 1. Ingest initial book
    epub_path = tmp_path / "hyperion.epub"
    create_sample_epub(epub_path, title="Hyperion Raw", author="Dan S.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_path)
    book_id = book.id or 1

    orchestrator = EnrichmentOrchestrator(lib_dir)

    # 2. Stage a candidate proposal
    proposal_id = "prop-hyperion-123"
    proposal = MetadataProposal(
        id=proposal_id,
        book_id=book_id,
        is_exact_isbn=False,
        composite_confidence=0.88,
        fields={
            "title": ProposedField(
                field_name="title",
                current_value="Hyperion Raw",
                proposed_value="Hyperion",
                source="google_books",
            ),
            "authors": ProposedField(
                field_name="authors",
                current_value="Dan S.",
                proposed_value="Dan Simmons",
                source="google_books",
            ),
            "publisher": ProposedField(
                field_name="publisher",
                current_value=None,
                proposed_value="Doubleday",
                source="openlibrary",
            ),
            "publication_year": ProposedField(
                field_name="publication_year",
                current_value=None,
                proposed_value=1989,
                source="openlibrary",
            ),
            "description": ProposedField(
                field_name="description",
                current_value=None,
                proposed_value="On the world called Hyperion, beyond the reach of galactic law.",
                source="google_books",
            ),
            "isbn": ProposedField(
                field_name="isbn",
                current_value=None,
                proposed_value="9780385249492",
                source="google_books",
            ),
        },
    )

    orchestrator.proposal_mgr.save_proposal(proposal)
    assert (lib_dir / ".vectors" / "staging" / f"{proposal_id}.json").exists()

    # 3. Apply proposal with a user override
    updated_book = await orchestrator.apply_proposal(
        proposal_id=proposal_id,
        field_overrides={"title": "Hyperion: The Fall and Rise"},
    )

    # 4. Verify book returned
    assert updated_book.title == "Hyperion: The Fall and Rise"
    assert updated_book.authors == ["Dan Simmons"]
    assert updated_book.publisher == "Doubleday"
    assert updated_book.publication_year == 1989
    assert updated_book.isbn == "9780385249492"

    # 5. Verify Calibre SQLite
    reloaded_book = await orchestrator._get_book_record(book_id)
    assert reloaded_book is not None
    assert reloaded_book.title == "Hyperion: The Fall and Rise"
    assert reloaded_book.authors == ["Dan Simmons"]
    assert reloaded_book.publisher == "Doubleday"
    assert (
        reloaded_book.description
        == "On the world called Hyperion, beyond the reach of galactic law."
    )

    # 6. Verify metadata.opf is rewritten on disk
    book_dir = lib_dir / reloaded_book.path
    opf_file = book_dir / "metadata.opf"
    assert opf_file.exists()
    opf_content = opf_file.read_text(encoding="utf-8")
    assert "Hyperion: The Fall and Rise" in opf_content
    assert "Dan Simmons" in opf_content
    assert "Doubleday" in opf_content
    assert "9780385249492" in opf_content

    # 7. Verify staging file was discarded
    assert not (lib_dir / ".vectors" / "staging" / f"{proposal_id}.json").exists()
    assert orchestrator.proposal_mgr.get_proposal(proposal_id) is None
