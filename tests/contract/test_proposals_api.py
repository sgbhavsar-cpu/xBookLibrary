"""Contract tests for agentic metadata proposals REST API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.enrichment import CoverCandidate, MetadataProposal, ProposedField
from backend.main import app
from backend.services.enrichment_orchestrator import EnrichmentResult
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolates config directory to temporary path."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_proposals_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies end-to-end lifecycle of metadata enrichment and proposal reviews via REST API."""
    # 1. Setup isolated library and ingest initial book
    lib_dir = tmp_path / "EnrichmentAPILib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Enrichment API Lib", set_active=True)

    epub_file = tmp_path / "neuromancer.epub"
    create_sample_epub(epub_file, title="Neuromancer Raw", author="William G.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("neuromancer.epub", f, "application/epub+zip")},
            )
            assert upload_res.status_code == 202
            book = upload_res.json()[0]
            book_id = book["id"]

        # 2. Trigger enrichment where fuzzy match results in a staged proposal
        staged_proposal = MetadataProposal(
            id="prop-test-neuro-001",
            book_id=book_id,
            is_exact_isbn=False,
            composite_confidence=0.82,
            fields={
                "title": ProposedField(
                    field_name="title",
                    current_value="Neuromancer Raw",
                    proposed_value="Neuromancer",
                    source="google_books",
                ),
                "authors": ProposedField(
                    field_name="authors",
                    current_value="William G.",
                    proposed_value="William Gibson",
                    source="google_books",
                ),
                "publisher": ProposedField(
                    field_name="publisher",
                    current_value=None,
                    proposed_value="Ace Books",
                    source="openlibrary",
                ),
            },
            candidate_covers=[
                CoverCandidate(url="https://books.google.com/cover.jpg", source="google_books")
            ],
        )

        with patch(
            "backend.services.enrichment_orchestrator.EnrichmentOrchestrator.enrich_book",
            new_callable=AsyncMock,
        ) as mock_enrich:
            mock_enrich.return_value = EnrichmentResult(
                status="STAGED_FOR_REVIEW",
                book_id=book_id,
                proposal_id="prop-test-neuro-001",
                applied=False,
            )

            # Manually save proposal to staging so GET endpoints can query it
            from backend.services.proposal_manager import ProposalManager

            prop_mgr = ProposalManager(lib_dir / ".vectors" / "staging")
            prop_mgr.save_proposal(staged_proposal)

            enrich_res = await client.post(f"/api/books/{book_id}/enrich")
            assert enrich_res.status_code == 200
            enrich_data = enrich_res.json()
            assert enrich_data["status"] == "STAGED_FOR_REVIEW"
            assert enrich_data["applied"] is False
            assert enrich_data["proposal_id"] == "prop-test-neuro-001"

        # 3. List proposals
        list_res = await client.get("/api/proposals")
        assert list_res.status_code == 200
        proposals_list = list_res.json()
        assert len(proposals_list) == 1
        assert proposals_list[0]["id"] == "prop-test-neuro-001"
        assert proposals_list[0]["book_id"] == book_id

        # 4. Get proposal details
        detail_res = await client.get("/api/proposals/prop-test-neuro-001")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["id"] == "prop-test-neuro-001"
        assert "title" in detail_data["fields"]
        assert detail_data["fields"]["title"]["proposed_value"] == "Neuromancer"

        # 5. Apply proposal with user override
        apply_res = await client.post(
            "/api/proposals/prop-test-neuro-001/apply",
            json={"field_overrides": {"title": "Neuromancer: Sprawl Trilogy"}},
        )
        assert apply_res.status_code == 200
        updated_book = apply_res.json()
        assert updated_book["title"] == "Neuromancer: Sprawl Trilogy"
        assert updated_book["authors"] == ["William Gibson"]
        assert updated_book["publisher"] == "Ace Books"

        # 6. Verify proposal is removed from staging
        get_again = await client.get("/api/proposals/prop-test-neuro-001")
        assert get_again.status_code == 404

        # 7. Discard flow: stage another proposal and discard it
        discard_proposal = MetadataProposal(
            id="prop-test-discard-002",
            book_id=book_id,
            is_exact_isbn=False,
            composite_confidence=0.60,
            fields={},
        )
        prop_mgr.save_proposal(discard_proposal)

        discard_res = await client.post("/api/proposals/prop-test-discard-002/discard")
        assert discard_res.status_code == 204

        get_discarded = await client.get("/api/proposals/prop-test-discard-002")
        assert get_discarded.status_code == 404
