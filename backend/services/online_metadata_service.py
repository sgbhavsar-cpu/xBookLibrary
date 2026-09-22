"""Online book metadata search service querying Google Books and OpenLibrary concurrently."""

import asyncio
import difflib
import logging
from typing import List, Optional

import httpx

from backend.domain.metadata_editor import OnlineMetadataCandidate

logger = logging.getLogger(__name__)


class OnlineMetadataService:
    """Queries external book metadata APIs and aggregates ranked candidates."""

    def __init__(self, timeout: float = 8.0):
        self.timeout = timeout

    async def search_metadata(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
        isbn: Optional[str] = None,
        limit: int = 10,
    ) -> List[OnlineMetadataCandidate]:
        """Queries Google Books and OpenLibrary concurrently and returns ranked candidates."""
        tasks = [
            self._query_google_books(title=title, author=author, isbn=isbn),
            self._query_openlibrary(title=title, author=author, isbn=isbn),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates: List[OnlineMetadataCandidate] = []

        for res in results:
            if isinstance(res, list):
                candidates.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"Metadata provider query failed: {res}")

        # Compute confidence score based on input match
        for cand in candidates:
            cand.confidence_score = self._compute_confidence(
                query_title=title,
                query_author=author,
                query_isbn=isbn,
                cand=cand,
            )

        # Sort descending by confidence score
        candidates.sort(key=lambda c: c.confidence_score, reverse=True)
        return candidates[:limit]

    async def _query_google_books(
        self, title: Optional[str], author: Optional[str], isbn: Optional[str]
    ) -> List[OnlineMetadataCandidate]:
        candidates: List[OnlineMetadataCandidate] = []
        query_parts = []
        if isbn:
            clean_isbn = isbn.replace("-", "").strip()
            query_parts.append(f"isbn:{clean_isbn}")
        else:
            if title:
                query_parts.append(f"intitle:{title.strip()}")
            if author:
                query_parts.append(f"inauthor:{author.strip()}")

        if not query_parts:
            return []

        q_str = "+".join(query_parts)
        url = f"https://www.googleapis.com/books/v1/volumes?q={q_str}&maxResults=8"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Google Books returned status {resp.status_code}")
                    return []
                data = resp.json()

            items = data.get("items", [])
            for item in items:
                vol = item.get("volumeInfo", {})
                cand_title = vol.get("title")
                if not cand_title:
                    continue

                authors = vol.get("authors", [])
                publisher = vol.get("publisher")
                published_date = vol.get("publishedDate")
                description = vol.get("description")
                categories = vol.get("categories", [])
                rating = vol.get("averageRating")

                # Identifiers
                industry_ids = vol.get("industryIdentifiers", [])
                cand_isbn = None
                identifiers = {}
                for id_obj in industry_ids:
                    id_type = id_obj.get("type", "").lower()
                    id_val = id_obj.get("identifier", "")
                    identifiers[id_type] = id_val
                    if "isbn" in id_type and not cand_isbn:
                        cand_isbn = id_val

                # Cover image
                image_links = vol.get("imageLinks", {})
                cover_url = (
                    image_links.get("extraLarge")
                    or image_links.get("large")
                    or image_links.get("medium")
                    or image_links.get("thumbnail")
                    or image_links.get("smallThumbnail")
                )
                if cover_url and cover_url.startswith("http://"):
                    cover_url = "https://" + cover_url[7:]

                candidates.append(
                    OnlineMetadataCandidate(
                        source="google_books",
                        title=cand_title,
                        authors=authors,
                        publisher=publisher,
                        published_date=published_date,
                        description=description,
                        isbn=cand_isbn,
                        identifiers=identifiers,
                        cover_url=cover_url,
                        rating=float(rating) if rating is not None else None,
                        tags=categories,
                    )
                )
        except Exception as e:
            logger.warning(f"Error querying Google Books: {e}")

        return candidates

    async def _query_openlibrary(
        self, title: Optional[str], author: Optional[str], isbn: Optional[str]
    ) -> List[OnlineMetadataCandidate]:
        candidates: List[OnlineMetadataCandidate] = []
        params = {}
        if isbn:
            params["isbn"] = isbn.replace("-", "").strip()
        else:
            if title:
                params["title"] = title.strip()
            if author:
                params["author"] = author.strip()

        if not params:
            return []

        url = "https://openlibrary.org/search.json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    logger.warning(f"OpenLibrary returned status {resp.status_code}")
                    return []
                data = resp.json()

            docs = data.get("docs", [])[:8]
            for doc in docs:
                cand_title = doc.get("title")
                if not cand_title:
                    continue

                authors = doc.get("author_name", [])
                publishers = doc.get("publisher", [])
                publisher = publishers[0] if publishers else None
                first_publish_year = doc.get("first_publish_year")
                published_date = str(first_publish_year) if first_publish_year else None

                # ISBNs
                isbns = doc.get("isbn", [])
                cand_isbn = isbns[0] if isbns else None
                identifiers = {}
                if cand_isbn:
                    identifiers["isbn"] = cand_isbn

                # Cover ID
                cover_id = doc.get("cover_i")
                cover_url = (
                    f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None
                )

                subjects = doc.get("subject", [])[:5]

                candidates.append(
                    OnlineMetadataCandidate(
                        source="openlibrary",
                        title=cand_title,
                        authors=authors,
                        publisher=publisher,
                        published_date=published_date,
                        description=None,
                        isbn=cand_isbn,
                        identifiers=identifiers,
                        cover_url=cover_url,
                        rating=None,
                        tags=subjects,
                    )
                )
        except Exception as e:
            logger.warning(f"Error querying OpenLibrary: {e}")

        return candidates

    def _compute_confidence(
        self,
        query_title: Optional[str],
        query_author: Optional[str],
        query_isbn: Optional[str],
        cand: OnlineMetadataCandidate,
    ) -> float:
        """Heuristic confidence metric from 0.0 to 1.0."""
        # Exact ISBN match is immediate 0.95+
        if query_isbn and cand.isbn:
            q_clean = query_isbn.replace("-", "").strip()
            c_clean = cand.isbn.replace("-", "").strip()
            if q_clean == c_clean:
                return 0.98

        score = 0.0

        # Title similarity (weight: 0.6)
        if query_title and cand.title:
            sim = difflib.SequenceMatcher(
                None, query_title.lower().strip(), cand.title.lower().strip()
            ).ratio()
            score += sim * 0.6
        else:
            score += 0.3

        # Author similarity (weight: 0.3)
        if query_author and cand.authors:
            author_str = " ".join(cand.authors).lower()
            a_sim = difflib.SequenceMatcher(None, query_author.lower().strip(), author_str).ratio()
            score += a_sim * 0.3
        elif cand.authors:
            score += 0.15

        # Has cover art bonus (weight: 0.05)
        if cand.cover_url:
            score += 0.05

        # Has description bonus (weight: 0.05)
        if cand.description:
            score += 0.05

        return round(min(1.0, max(0.0, score)), 2)
