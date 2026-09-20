"""CrossRef API metadata provider for academic books, monographs, and papers."""

import re
from typing import List, Optional

import httpx

from backend.domain.enrichment import CandidateMetadata
from backend.providers.base import MetadataProvider
from backend.services.http_cache import HttpCache


class CrossRefProvider(MetadataProvider):
    """Fetches academic metadata, DOIs, and monographs from CrossRef API."""

    def __init__(
        self,
        mailto: str = "support@example.com",
        cache: Optional[HttpCache] = None,
        timeout: float = 5.0,
    ):
        self.mailto = mailto
        self.cache = cache
        self.timeout = timeout
        self.base_url = "https://api.crossref.org/works"
        self.headers = {"User-Agent": f"xBookLibrary/0.1.0 (mailto:{mailto})"}

    @property
    def name(self) -> str:
        return "crossref"

    async def fetch_by_isbn(self, isbn: str) -> Optional[CandidateMetadata]:
        clean_isbn = re.sub(r"[-\s]", "", isbn.strip())
        cache_key = f"crossref:isbn:{clean_isbn}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return CandidateMetadata.model_validate(cached)

        params = {"query.bibliographic": clean_isbn, "rows": 1}
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return None
                data = resp.json()
            except Exception:
                return None

        items = data.get("message", {}).get("items", [])
        if not items:
            return None

        candidate = self._parse_item(items[0], query_isbn=clean_isbn)
        if self.cache and candidate:
            self.cache.set(cache_key, candidate.model_dump())

        return candidate

    async def fetch_by_doi(self, doi: str) -> Optional[CandidateMetadata]:
        clean_doi = doi.strip()
        cache_key = f"crossref:doi:{clean_doi}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return CandidateMetadata.model_validate(cached)

        url = f"{self.base_url}/{clean_doi}"
        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return None
                data = resp.json()
            except Exception:
                return None

        item = data.get("message", {})
        if not item:
            return None

        candidate = self._parse_item(item)
        if self.cache and candidate:
            self.cache.set(cache_key, candidate.model_dump())

        return candidate

    async def fetch_by_query(
        self, title: str, author: Optional[str] = None
    ) -> List[CandidateMetadata]:
        cache_key = f"crossref:search:{title.lower()}:{str(author).lower()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return [CandidateMetadata.model_validate(item) for item in cached]

        params = {"query.bibliographic": title, "rows": 3}
        if author:
            params["query.author"] = author

        async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
            try:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
            except Exception:
                return []

        items = data.get("message", {}).get("items", [])
        candidates = []
        for item in items:
            c = self._parse_item(item)
            if c:
                candidates.append(c)

        if self.cache:
            self.cache.set(cache_key, [c.model_dump() for c in candidates])

        return candidates

    def _parse_item(
        self, item: dict, query_isbn: Optional[str] = None
    ) -> Optional[CandidateMetadata]:
        titles = item.get("title", [])
        if not titles:
            return None
        title = titles[0]

        authors = []
        for a in item.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            full = f"{given} {family}".strip()
            if full:
                authors.append(full)

        publisher = item.get("publisher")

        pub_year = None
        date_parts = (
            item.get("published-print", {}).get("date-parts", [])
            or item.get("published-online", {}).get("date-parts", [])
            or item.get("created", {}).get("date-parts", [])
        )
        if date_parts and date_parts[0] and date_parts[0][0]:
            try:
                pub_year = int(date_parts[0][0])
            except Exception:
                pass

        identifiers = {}
        if item.get("DOI"):
            identifiers["doi"] = str(item["DOI"])

        isbns = item.get("ISBN", [])
        isbn_found = query_isbn or (isbns[0] if isbns else None)

        abstract = item.get("abstract")
        clean_desc = None
        if abstract:
            clean_desc = re.sub(r"<[^>]+>", "", abstract).strip()

        tags = item.get("subject", [])

        return CandidateMetadata(
            source=self.name,
            isbn=isbn_found,
            title=title,
            authors=authors,
            publisher=publisher,
            publication_year=pub_year,
            description=clean_desc,
            identifiers=identifiers,
            tags=tags[:10],
            raw_payload=item,
        )
