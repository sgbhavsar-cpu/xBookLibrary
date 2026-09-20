"""Unit tests for classification safeguards, tag cleaning, and proposal staging."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.services.classification_service import ClassificationService, clean_semantic_tags
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


def test_tag_cleaner():
    """Verifies that generic noise tags are stripped and valid tags normalized."""
    raw_tags = [
        "ebook",
        "General",
        "kindle edition",
        "Artificial Intelligence",
        "paperback",
        "Machine Learning",
        "MISC",
    ]
    cleaned = clean_semantic_tags(raw_tags)
    assert "ebook" not in cleaned
    assert "General" not in cleaned
    assert "paperback" not in cleaned
    assert "MISC" not in cleaned
    assert "Artificial Intelligence" in cleaned
    assert "Machine Learning" in cleaned


@pytest.mark.asyncio
async def test_low_confidence_classification_staged(tmp_path: Path):
    """Verifies that confidence < 0.85 stages an ephemeral proposal and avoids committing."""
    lib_dir = tmp_path / "SafeguardLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Safeguard Lib", set_active=False)

    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    epub = tmp_path / "obscure.epub"
    create_sample_epub(epub, title="Obscure Notes", author="Unknown A.")
    book = await ingestion.ingest_file(epub)
    book_id = book.id or 1

    service = ClassificationService(lib_dir)

    # Mock low-confidence classification
    mock_low_conf = {
        "bisac_code": "GEN000000",
        "bisac_heading": "GENERAL / General",
        "ddc_code": "000",
        "confidence": 0.65,
        "suggested_tags": ["General Notes"],
        "reasoning": "Ambiguous content",
    }

    with patch.object(service, "_call_llm_classifier", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_low_conf

        res = await service.classify_book(book_id, auto_apply=True)

        assert res.applied is False
        assert res.proposal_id is not None
        assert res.confidence == 0.65

        # Check staging file exists
        staging_file = lib_dir / ".vectors" / "staging" / f"{res.proposal_id}.json"
        assert staging_file.exists()

        # Verify x_classifications is untouched
        import aiosqlite

        async with aiosqlite.connect(lib_dir / "metadata.db") as db:
            async with db.execute(
                "SELECT COUNT(*) FROM x_classifications WHERE book_id = ?", (book_id,)
            ) as cur:
                count = (await cur.fetchone())[0]
                assert count == 0

        # Now approve and apply proposal
        applied_book = await service.apply_classification_proposal(res.proposal_id)
        assert applied_book is not None

        # Verify x_classifications is now populated
        async with aiosqlite.connect(lib_dir / "metadata.db") as db:
            async with db.execute(
                "SELECT bisac_code FROM x_classifications WHERE book_id = ?", (book_id,)
            ) as cur:
                row = await cur.fetchone()
                assert row is not None
                assert row[0] == "GEN000000"

        # Staging file is cleaned up
        assert not staging_file.exists()
