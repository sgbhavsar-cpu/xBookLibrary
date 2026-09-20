"""Google Books API metadata provider implementation."""

import re
from typing import List, Optional

import httpx

from backend.domain.enrichment import CandidateMetadata, CoverCandidate
from backend.providers.base import MetadataProvider
from backend.services.http_cache import HttpCache


class GoogleBooksProvider(MetadataProvider):
    """Fetches bibliographic metadata and high-definition covers from Google Books API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache: Optional[HttpCache] = None,
        timeout: float = 5.0,
    ):
        self.api_key = api_key
        self.cache = cache
        self.timeout = timeout
        self.base_url = "https://www.googleapis.com/books/v1/volumes"

    @property
    def name(self) -> str:
        return "google_books"

    async def fetch_by_isbn(self, isbn: str) -> Optional[CandidateMetadata]:
        clean_isbn = re.sub(r"[-\s]", "", isbn.strip())
        cache_key = f"google_books:isbn:{clean_isbn}"

        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return CandidateMetadata.model_validate(cached)

        params = {"q": f"isbn:{clean_isbn}", "maxResults": 1}
        if self.api_key:
            params["key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return None
                data = resp.json()
            except Exception:
                return None

        items = data.get("items", [])
        if not items:
            return None

        candidate = self._parse_volume(items[0], query_isbn=clean_isbn)
        if self.cache and candidate:
            self.cache.set(cache_key, candidate.model_dump())

        return candidate

    async def fetch_by_query(
        self, title: str, author: Optional[str] = None
    ) -> List[CandidateMetadata]:
        cache_key = f"google_books:search:{title.lower()}:{str(author).lower()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return [CandidateMetadata.model_validate(item) for item in cached]

        q = f'intitle:"{title}"'
        if author:
            q += f' inauthor:"{author}"'

        params = {"q": q, "maxResults": 5}
        if self.api_key:
            params["key"] = self.api_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.get(self.base_url, params=params)
                if resp.status_code != 200:
                    return []
                data = resp.json()
            except Exception:
                return []

        items = data.get("items", [])
        candidates: List[CandidateMetadata] = []
        for item in items:
            c = self._parse_volume(item)
            if c:
                candidates.append(c)

        if self.cache:
            self.cache.set(cache_key, [c.model_dump() for c in candidates])

        return candidates

    def _parse_volume(
        self, item: dict, query_isbn: Optional[str] = None
    ) -> Optional[CandidateMetadata]:
        vol = item.get("volumeInfo", {})
        title = vol.get("title")
        if not title:
            return None

        subtitle = vol.get("subtitle")
        full_title = f"{title}: {subtitle}" if subtitle else title

        authors = vol.get("authors", [])
        publisher = vol.get("publisher")

        pub_year = None
        if vol.get("publishedDate"):
            m = re.search(r"\b(1\d{3}|20\d{2})\b", str(vol["publishedDate"]))
            if m:
                pub_year = int(m.group(1))

        desc = vol.get("description")
        tags = vol.get("categories", [])
        language = vol.get("language")

        # Identifiers
        identifiers = {}
        isbn_found = query_isbn
        for ident in vol.get("industryIdentifiers", []):
            itype = ident.get("type", "").lower()
            ival = ident.get("identifier")
            if ival:
                identifiers[itype] = ival
                if "isbn_13" in itype:
                    isbn_found = ival
                elif "isbn_10" in itype and not isbn_found:
                    isbn_found = ival

        # Cover resolution: upgrade thumbnail to high-res
        cover = None
        images = vol.get("imageLinks", {})
        raw_cover_url = (
            images.get("extraLarge")
            or images.get("large")
            or images.get("medium")
            or images.get("thumbnail")
            or images.get("smallThumbnail")
        )

        if raw_cover_url:
            # Clean URL: upgrade to HTTPS and increase zoom for high definition
            high_res_url = raw_cover_url.replace("http://", "https://")
            high_res_url = re.sub(r"&edge=curl", "", high_res_url)
            high_res_url = re.sub(r"zoom=\d", "zoom=2", high_res_url)
            cover = CoverCandidate(url=high_res_url, source=self.name)

        return CandidateMetadata(
            source=self.name,
            isbn=isbn_found,
            title=full_title,
            authors=authors,
            publisher=publisher,
            publication_year=pub_year,
            description=desc,
            language=language,
            identifiers=identifiers,
            tags=tags[:15],
            cover=cover,
            raw_payload=item,
        )
