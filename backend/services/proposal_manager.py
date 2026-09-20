"""Manages ephemeral candidate proposals in .vectors/staging/."""

import json
from pathlib import Path
from typing import List, Optional

from backend.domain.enrichment import MetadataProposal


class ProposalManager:
    """Handles persistence, loading, and disposal of ephemeral proposals in .vectors/staging/."""

    def __init__(self, library_root: Path):
        if library_root.name == "staging" and library_root.parent.name == ".vectors":
            self.library_root = library_root.parent.parent
            self.staging_dir = library_root
        else:
            self.library_root = library_root
            self.staging_dir = library_root / ".vectors" / "staging"
        self._ensure_staging_dir()

    def _ensure_staging_dir(self) -> None:
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def save_proposal(
        self, proposal: MetadataProposal, cover_bytes: Optional[bytes] = None
    ) -> Path:
        """Saves a candidate proposal as an ephemeral JSON file and optional staged cover."""
        self._ensure_staging_dir()
        proposal_file = self.staging_dir / f"{proposal.id}.json"
        with open(proposal_file, "w", encoding="utf-8") as f:
            f.write(proposal.model_dump_json(indent=2))

        if cover_bytes:
            cover_file = self.staging_dir / f"{proposal.id}_cover.jpg"
            with open(cover_file, "wb") as f:
                f.write(cover_bytes)

        return proposal_file

    def get_proposal(self, proposal_id: str) -> Optional[MetadataProposal]:
        """Loads a specific candidate proposal by ID."""
        proposal_file = self.staging_dir / f"{proposal_id}.json"
        if not proposal_file.exists():
            return None

        try:
            with open(proposal_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return MetadataProposal.model_validate(data)
        except Exception:
            return None

    def list_proposals(self) -> List[MetadataProposal]:
        """Lists all pending proposals in the staging directory."""
        if not self.staging_dir.exists():
            return []

        proposals = []
        for file in self.staging_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    proposals.append(MetadataProposal.model_validate(data))
            except Exception:
                continue

        # Sort by creation date descending
        proposals.sort(key=lambda p: p.created_at, reverse=True)
        return proposals

    def list_pending_proposals(self) -> List[MetadataProposal]:
        """Alias for listing pending proposals."""
        return self.list_proposals()

    def get_proposal_cover_path(self, proposal_id: str) -> Optional[Path]:
        """Returns the path to the staged cover image if present."""
        cover_file = self.staging_dir / f"{proposal_id}_cover.jpg"
        return cover_file if cover_file.exists() else None

    def discard_proposal(self, proposal_id: str) -> bool:
        """Deletes a staged proposal JSON and any associated cover image."""
        proposal_file = self.staging_dir / f"{proposal_id}.json"
        cover_file = self.staging_dir / f"{proposal_id}_cover.jpg"

        deleted = False
        if proposal_file.exists():
            proposal_file.unlink()
            deleted = True
        if cover_file.exists():
            cover_file.unlink()

        return deleted

    def clear_all(self) -> int:
        """Removes all staged proposal files and returns count removed."""
        count = 0
        if self.staging_dir.exists():
            for item in self.staging_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    count += 1
        return count
