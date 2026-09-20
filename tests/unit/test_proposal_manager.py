"""Unit tests for ProposalManager ephemeral staging operations."""

from pathlib import Path

from backend.domain.enrichment import MetadataProposal, ProposalStatus, ProposedField
from backend.services.proposal_manager import ProposalManager


def test_proposal_lifecycle(tmp_path: Path):
    """Verifies saving, retrieving, listing, and discarding staging proposals."""
    lib_dir = tmp_path / "TestLibrary"
    mgr = ProposalManager(lib_dir)

    # 1. Create sample proposal
    proposal = MetadataProposal(
        id="prop-abc12345",
        book_id=42,
        is_exact_isbn=False,
        composite_confidence=0.78,
        fields={
            "title": ProposedField(
                field_name="title",
                current_value="Dune",
                proposed_value="Dune: Deluxe Edition",
                source="google_books",
                confidence=0.82,
            ),
            "publication_year": ProposedField(
                field_name="publication_year",
                current_value=1965,
                proposed_value=1969,
                source="openlibrary",
                confidence=0.74,
                is_conflicting=True,
            ),
        },
    )

    fake_cover_bytes = b"\xff\xd8\xff\xe0fakejpegcoverdata"

    # 2. Save proposal
    saved_path = mgr.save_proposal(proposal, cover_bytes=fake_cover_bytes)
    assert saved_path.exists()
    assert (lib_dir / ".vectors" / "staging" / "prop-abc12345.json").exists()
    assert (lib_dir / ".vectors" / "staging" / "prop-abc12345_cover.jpg").exists()

    # 3. Retrieve proposal
    retrieved = mgr.get_proposal("prop-abc12345")
    assert retrieved is not None
    assert retrieved.id == "prop-abc12345"
    assert retrieved.book_id == 42
    assert retrieved.status == ProposalStatus.PENDING
    assert retrieved.fields["title"].proposed_value == "Dune: Deluxe Edition"
    assert retrieved.fields["publication_year"].is_conflicting is True

    # 4. Cover path
    cover_path = mgr.get_proposal_cover_path("prop-abc12345")
    assert cover_path is not None
    assert cover_path.read_bytes() == fake_cover_bytes

    # 5. List proposals
    proposals = mgr.list_proposals()
    assert len(proposals) == 1
    assert proposals[0].id == "prop-abc12345"

    # 6. Discard proposal
    deleted = mgr.discard_proposal("prop-abc12345")
    assert deleted is True
    assert mgr.get_proposal("prop-abc12345") is None
    assert mgr.get_proposal_cover_path("prop-abc12345") is None
    assert len(mgr.list_proposals()) == 0
