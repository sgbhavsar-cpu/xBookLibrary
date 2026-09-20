"""OpenLibrary metadata provider implementation."""

import re
from typing import List, Optional

import httpx

from backend.domain.enrichment import CandidateMetadata, CoverCandidate
from backend.providers.base import MetadataProvider
from backend.services.http_cache import HttpCache


class OpenLibraryProvider(MetadataProvider):
    """Fetches bibliographic metadata and covers from OpenLibrary.org."""

    def __init__(self, cache: Optional[HttpCache] = None, timeout: float = 5.0):
        self.cache = cache
        self.timeout = timeout
        self.headers = {"User-Agent": "xBookLibrary/0.1.0 (https://github.com/sac/xBookLibrary)"}

    @property
    def name(self) -> str:
        return "openlibrary"

    async def fetch_by_isbn(self, isbn: str) -> Optional[CandidateMetadata]:
        clean_isbn = re.sub(r"[-\s]", "", isbn.strip())
        cache_key = f"openlibrary:isbn:{clean_isbn}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return CandidateMetadata.model_validate(cached)

        url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{clean_isbn}&format=json&jscmd=data"
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()
            except Exception:
                return None

        book_key = f"ISBN:{clean_isbn}"
        if book_key not in data:
            return None

        raw = data[book_key]
        candidate = self._parse_isbn_data(clean_isbn, raw)

        if self.cache and candidate:
            self.cache.set(cache_key, candidate.model_dump())

        return candidate

    async def fetch_by_query(
        self, title: str, author: Optional[str] = None
    ) -> List[CandidateMetadata]:
        cache_key = f"openlibrary:search:{title.lower()}:{str(author).lower()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return [CandidateMetadata.model_validate(item) for item in cached]

        params = {"title": title, "limit": 5}
        if author:
            params["author"] = author

        url = "https://openlibrary.org/search.json"
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
            except Exception:
                return []

        docs = data.get("docs", [])
        candidates: List[CandidateMetadata] = []
        for doc in docs:
            c = self._parse_search_doc(doc)
            if c:
                candidates.append(c)

        if self.cache:
            self.cache.set(cache_key, [c.model_dump() for c in candidates])

        return candidates

    def _parse_isbn_data(self, isbn: str, raw: dict) -> CandidateMetadata:
        title = raw.get("title")
        authors = [a.get("name") for a in raw.get("authors", []) if a.get("name")]

        publishers = [p.get("name") for p in raw.get("publishers", []) if p.get("name")]
        publisher = publishers[0] if publishers else None

        pub_year = None
        if raw.get("publish_date"):
            m = re.search(r"\b(1\d{3}|20\d{2})\b", str(raw["publish_date"]))
            if m:
                pub_year = int(m.group(1))

        desc = raw.get("notes") or ""
        if isinstance(raw.get("description"), dict):
            desc = raw["description"].get("value", "")
        elif isinstance(raw.get("description"), str):
            desc = raw["description"]

        tags = [s.get("name") for s in raw.get("subjects", []) if s.get("name")]

        # Covers
        cover = None
        cover_info = raw.get("cover", {})
        if cover_info.get("large"):
            cover = CoverCandidate(url=cover_info["large"], source=self.name)
        elif cover_info.get("medium"):
            cover = CoverCandidate(url=cover_info["medium"], source=self.name)

        identifiers = {}
        if "identifiers" in raw:
            for k, vals in raw["identifiers"].items():
                if vals and isinstance(vals, list):
                    identifiers[k] = str(vals[0])

        return CandidateMetadata(
            source=self.name,
            isbn=isbn,
            title=title,
            authors=authors,
            publisher=publisher,
            publication_year=pub_year,
            description=desc if desc else None,
            tags=tags[:15],
            cover=cover,
            identifiers=identifiers,
            raw_payload=raw,
        )

    def _parse_search_doc(self, doc: dict) -> Optional[CandidateMetadata]:
        title = doc.get("title")
        if not title:
            return None

        authors = doc.get("author_name", [])
        publishers = doc.get("publisher", [])
        publisher = publishers[0] if publishers else None
        pub_year = doc.get("first_publish_year")

        isbns = doc.get("isbn", [])
        primary_isbn = isbns[0] if isbns else None

        cover = None
        cover_i = doc.get("cover_i")
        if cover_i:
            cover = CoverCandidate(
                url=f"https://covers.openlibrary.org/b/id/{cover_i}-L.jpg",
                source=self.name,
            )

        return CandidateMetadata(
            source=self.name,
            isbn=primary_isbn,
            title=title,
            authors=authors,
            publisher=publisher,
            publication_year=pub_year,
            tags=doc.get("subject", [])[:15],
            cover=cover,
            raw_payload=doc,
        )
