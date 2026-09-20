"""FastAPI router for bibliographic metadata enrichment and proposal staging."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.enrichment import MetadataProposal
from backend.domain.entities import Book
from backend.services.enrichment_orchestrator import EnrichmentOrchestrator
from backend.services.proposal_manager import ProposalManager

router = APIRouter(tags=["Enrichment & Proposals"])


class EnrichResponse(BaseModel):
    applied: bool
    proposal_id: Optional[str] = None
    status: str


class ApplyProposalRequest(BaseModel):
    selected_cover_url: Optional[str] = None
    field_overrides: Optional[Dict[str, Any]] = None


def _get_active_library_path() -> Path:
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active library configured",
        )
    return Path(active_lib.path)


@router.post("/api/books/{book_id}/enrich", response_model=EnrichResponse)
async def enrich_book(book_id: int):
    """Triggers multi-source metadata enrichment for a specific book."""
    lib_path = _get_active_library_path()
    orchestrator = EnrichmentOrchestrator(lib_path)
    try:
        res = await orchestrator.enrich_book(book_id)
        return EnrichResponse(
            applied=res.applied,
            proposal_id=res.proposal_id,
            status=res.status,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {e}",
        )


@router.get("/api/proposals", response_model=List[MetadataProposal])
async def list_proposals():
    """Lists all pending metadata review proposals for the active library."""
    try:
        lib_path = _get_active_library_path()
    except HTTPException:
        return []

    prop_mgr = ProposalManager(lib_path)
    return prop_mgr.list_pending_proposals()


@router.get("/api/proposals/{proposal_id}", response_model=MetadataProposal)
async def get_proposal(proposal_id: str):
    """Retrieves field diffs and candidate covers for a specific proposal."""
    lib_path = _get_active_library_path()
    prop_mgr = ProposalManager(lib_path)
    proposal = prop_mgr.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found",
        )
    return proposal


@router.post("/api/proposals/{proposal_id}/apply", response_model=Book)
async def apply_proposal(proposal_id: str, request: Optional[ApplyProposalRequest] = None):
    """Applies approved proposal diffs and user overrides to Calibre SQLite and metadata.opf."""
    lib_path = _get_active_library_path()
    orchestrator = EnrichmentOrchestrator(lib_path)

    overrides = request.field_overrides if request else None
    cover_url = request.selected_cover_url if request else None

    try:
        updated_book = await orchestrator.apply_proposal(
            proposal_id=proposal_id,
            field_overrides=overrides,
            selected_cover_url=cover_url,
        )
        return updated_book
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply proposal: {e}",
        )


@router.post("/api/proposals/{proposal_id}/discard", status_code=status.HTTP_204_NO_CONTENT)
async def discard_proposal(proposal_id: str):
    """Discards an ephemeral proposal and deletes its staging files."""
    lib_path = _get_active_library_path()
    prop_mgr = ProposalManager(lib_path)
    proposal = prop_mgr.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal {proposal_id} not found",
        )
    prop_mgr.discard_proposal(proposal_id)
    return None
