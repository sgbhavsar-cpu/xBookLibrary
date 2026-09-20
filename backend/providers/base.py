"""Abstract base class for bibliographic metadata providers."""

from abc import ABC, abstractmethod
from typing import List, Optional

from backend.domain.enrichment import CandidateMetadata


class MetadataProvider(ABC):
    """Abstract base strategy for bibliographic metadata providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""
        pass

    @abstractmethod
    async def fetch_by_isbn(self, isbn: str) -> Optional[CandidateMetadata]:
        """Lookup by ISBN."""
        pass

    @abstractmethod
    async def fetch_by_query(
        self, title: str, author: Optional[str] = None
    ) -> List[CandidateMetadata]:
        """Search by title and optional author."""
        pass
