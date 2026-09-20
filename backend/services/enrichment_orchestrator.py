"""Enrichment orchestrator coordinating online providers,
LLM vision fallback, and Calibre updates.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite
import httpx

from backend.config import ConfigManager
from backend.domain.enrichment import (
    CandidateMetadata,
    CoverCandidate,
    MetadataProposal,
    ProposedField,
)
from backend.domain.entities import Book
from backend.providers.crossref import CrossRefProvider
from backend.providers.google_books import GoogleBooksProvider
from backend.providers.llm_adapter import LiteLLMClientAdapter
from backend.providers.openlibrary import OpenLibraryProvider
from backend.services.http_cache import HttpCache
from backend.services.proposal_manager import ProposalManager
from backend.services.storage_service import StorageService
from backend.services.vision_extractor import VisionExtractor


class EnrichmentResult:
    def __init__(
        self,
        status: str,  # "APPLIED" | "STAGED_FOR_REVIEW" | "NO_MATCH"
        book_id: int,
        proposal_id: Optional[str] = None,
        applied: Optional[bool] = None,
        applied_fields: Optional[Dict[str, Any]] = None,
    ):
        self.status = status
        self.book_id = book_id
        self.proposal_id = proposal_id
        self.applied = applied if applied is not None else (status == "APPLIED")
        self.applied_fields = applied_fields or {}


class EnrichmentOrchestrator:
    """Coordinates multi-source enrichment cascade, strict ISBN auto-apply, and staging review."""

    def __init__(
        self,
        library_root: Path,
        config_manager: Optional[ConfigManager] = None,
    ):
        self.library_root = library_root
        self.db_path = library_root / "metadata.db"
        self.config_manager = config_manager or ConfigManager()

        cache_dir = library_root / ".vectors" / "cache"
        self.cache = HttpCache(cache_dir)
        self.proposal_mgr = ProposalManager(library_root)
        self.storage = StorageService(library_root)

        # Providers
        self.openlibrary = OpenLibraryProvider(cache=self.cache)
        self.google_books = GoogleBooksProvider(cache=self.cache)
        self.crossref = CrossRefProvider(cache=self.cache)
        self.llm_adapter = LiteLLMClientAdapter(config_manager=self.config_manager)

    async def enrich_book(self, book_id: int) -> EnrichmentResult:
        """Executes full enrichment cascade on the specified book."""
        current_book = await self._get_book_record(book_id)
        if not current_book:
            return EnrichmentResult(status="NO_MATCH", book_id=book_id)

        # 1. Primary ISBN lookup (Parallel Fast-Lookup)
        if current_book.isbn:
            ol_res, gb_res = await asyncio.gather(
                self.openlibrary.fetch_by_isbn(current_book.isbn),
                self.google_books.fetch_by_isbn(current_book.isbn),
                return_exceptions=True,
            )
            candidate_ol = ol_res if isinstance(ol_res, CandidateMetadata) else None
            candidate_gb = gb_res if isinstance(gb_res, CandidateMetadata) else None

            if candidate_ol or candidate_gb:
                # Merge with provider-specialized precedence
                merged = self._merge_candidates(candidate_ol, candidate_gb)
                # Exact 100% ISBN match -> Auto-apply!
                await self._apply_candidate_to_db(book_id, merged, current_book)
                return EnrichmentResult(
                    status="APPLIED",
                    book_id=book_id,
                    applied_fields=merged.model_dump(exclude={"raw_payload"}),
                )

        # 2. Non-ISBN Search Cascade (OpenLibrary & Google Books by Title/Author)
        primary_author = current_book.authors[0] if current_book.authors else None
        ol_search, gb_search = await asyncio.gather(
            self.openlibrary.fetch_by_query(current_book.title, primary_author),
            self.google_books.fetch_by_query(current_book.title, primary_author),
            return_exceptions=True,
        )
        candidates_ol = ol_search if isinstance(ol_search, list) else []
        candidates_gb = gb_search if isinstance(gb_search, list) else []

        best_ol = candidates_ol[0] if candidates_ol else None
        best_gb = candidates_gb[0] if candidates_gb else None
        merged_candidate = self._merge_candidates(best_ol, best_gb)

        # 3. CrossRef fallback if no results
        if not merged_candidate:
            cr_results = await self.crossref.fetch_by_query(current_book.title, primary_author)
            if cr_results:
                merged_candidate = cr_results[0]

        # 4. Multimodal LLM Vision fallback if still unverified
        if not merged_candidate:
            book_file = self._find_first_book_file(current_book)
            if book_file and book_file.exists():
                images = VisionExtractor.extract_preview_images(book_file, max_pages=3)
                if images:
                    merged_candidate = await self.llm_adapter.extract_from_images(
                        images, fallback_title=current_book.title
                    )

        if not merged_candidate:
            return EnrichmentResult(status="NO_MATCH", book_id=book_id)

        # Because this was non-ISBN search or LLM vision -> Stage for human review!
        proposal = self._create_proposal(current_book, merged_candidate)
        cover_bytes = None
        if merged_candidate.cover and merged_candidate.cover.bytes_data:
            cover_bytes = merged_candidate.cover.bytes_data

        self.proposal_mgr.save_proposal(proposal, cover_bytes=cover_bytes)
        return EnrichmentResult(
            status="STAGED_FOR_REVIEW",
            book_id=book_id,
            proposal_id=proposal.id,
        )

    def _merge_candidates(
        self,
        ol: Optional[CandidateMetadata],
        gb: Optional[CandidateMetadata],
    ) -> Optional[CandidateMetadata]:
        """Merges OpenLibrary and Google Books with provider-specialized precedence:
        - Google Books: preferred for description and high-res cover
        - OpenLibrary: preferred for editions and ISBNs
        - Tags: union
        """
        if not ol and not gb:
            return None
        if ol and not gb:
            return ol
        if gb and not ol:
            return gb

        # Both present -> Merge
        assert ol is not None and gb is not None

        # Tags union
        all_tags = list(dict.fromkeys(gb.tags + ol.tags))

        # Description: Google Books preferred if non-empty, else OpenLibrary
        description = gb.description or ol.description

        # Cover: Google Books preferred for high-res
        cover = gb.cover or ol.cover

        # Publisher & Year: Google Books or OpenLibrary
        publisher = gb.publisher or ol.publisher
        year = gb.publication_year or ol.publication_year

        # Identifiers
        identifiers = {**ol.identifiers, **gb.identifiers}

        return CandidateMetadata(
            source="hybrid:google_books+openlibrary",
            isbn=ol.isbn or gb.isbn,
            title=gb.title or ol.title,
            authors=gb.authors if gb.authors else ol.authors,
            publisher=publisher,
            publication_year=year,
            description=description,
            tags=all_tags[:15],
            cover=cover,
            identifiers=identifiers,
        )

    def _create_proposal(self, current: Book, candidate: CandidateMetadata) -> MetadataProposal:
        """Generates a field-by-field diff proposal."""
        fields: Dict[str, ProposedField] = {}

        def add_diff(name: str, cur_val: Any, prop_val: Any):
            if prop_val is not None:
                is_diff = str(cur_val or "").strip().lower() != str(prop_val or "").strip().lower()
                fields[name] = ProposedField(
                    field_name=name,
                    current_value=cur_val,
                    proposed_value=prop_val,
                    source=candidate.source,
                    is_conflicting=is_diff and bool(cur_val),
                )

        add_diff("title", current.title, candidate.title)
        add_diff(
            "authors",
            ", ".join(current.authors) if current.authors else None,
            ", ".join(candidate.authors) if candidate.authors else None,
        )
        add_diff("publisher", current.publisher, candidate.publisher)
        add_diff("publication_year", current.publication_year, candidate.publication_year)
        add_diff("description", current.description, candidate.description)
        add_diff("isbn", current.isbn, candidate.isbn)

        candidate_covers: List[CoverCandidate] = []
        if candidate.cover:
            candidate_covers.append(candidate.cover)

        return MetadataProposal(
            id=f"prop-{uuid.uuid4().hex[:8]}",
            book_id=current.id or 0,
            is_exact_isbn=False,
            composite_confidence=0.75,
            fields=fields,
            candidate_covers=candidate_covers,
        )

    async def apply_proposal(
        self,
        proposal_id: str,
        field_overrides: Optional[Dict[str, Any]] = None,
        selected_cover_url: Optional[str] = None,
    ) -> Book:
        """Applies approved fields to Calibre SQLite tables and metadata.opf,
        then clears staging.
        """
        proposal = self.proposal_mgr.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found in staging")

        current_book = await self._get_book_record(proposal.book_id)
        if not current_book:
            raise ValueError(f"Book {proposal.book_id} not found")

        # Prepare updates
        title = current_book.title
        authors = current_book.authors
        publisher = current_book.publisher
        pub_year = current_book.publication_year
        desc = current_book.description
        isbn = current_book.isbn

        for field_name, pf in proposal.fields.items():
            val = pf.proposed_value
            if field_overrides and field_name in field_overrides:
                val = field_overrides[field_name]

            if val is not None:
                if field_name == "title":
                    title = str(val)
                elif field_name == "authors":
                    if isinstance(val, list):
                        authors = [str(a) for a in val]
                    else:
                        authors = [a.strip() for a in str(val).split(",") if a.strip()]
                elif field_name == "publisher":
                    publisher = str(val)
                elif field_name == "publication_year":
                    try:
                        pub_year = int(val)
                    except Exception:
                        pass
                elif field_name == "description":
                    desc = str(val)
                elif field_name == "isbn":
                    isbn = str(val)

        # Handle Cover
        book_dir = self.library_root / current_book.path
        if selected_cover_url:
            await self._download_and_save_cover(book_dir, selected_cover_url)
        else:
            # Check if staged cover exists
            staged_cover_path = self.proposal_mgr.get_proposal_cover_path(proposal_id)
            if staged_cover_path and staged_cover_path.exists():
                self.storage.save_cover_image(book_dir, staged_cover_path.read_bytes())

        # Write to Calibre SQLite
        await self._update_calibre_records(
            current_book.id or 0, title, authors, publisher, pub_year, desc, isbn
        )

        # Write metadata.opf
        updated_book = await self._get_book_record(current_book.id or 0)
        assert updated_book is not None
        self.storage.write_metadata_opf(book_dir, updated_book)

        # Cleanup ephemeral proposal
        self.proposal_mgr.discard_proposal(proposal_id)
        return updated_book

    async def _apply_candidate_to_db(
        self, book_id: int, candidate: CandidateMetadata, current: Book
    ) -> None:
        """Directly writes high-confidence candidate to SQLite and metadata.opf."""
        title = candidate.title or current.title
        authors = candidate.authors if candidate.authors else current.authors
        publisher = candidate.publisher or current.publisher
        pub_year = candidate.publication_year or current.publication_year
        desc = candidate.description or current.description
        isbn = candidate.isbn or current.isbn

        book_dir = self.library_root / current.path
        if candidate.cover:
            if candidate.cover.url:
                await self._download_and_save_cover(book_dir, candidate.cover.url)
            elif candidate.cover.bytes_data:
                self.storage.save_cover_image(book_dir, candidate.cover.bytes_data)

        await self._update_calibre_records(book_id, title, authors, publisher, pub_year, desc, isbn)
        updated_book = await self._get_book_record(book_id)
        if updated_book:
            self.storage.write_metadata_opf(book_dir, updated_book)

    async def _download_and_save_cover(self, book_dir: Path, url: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200 and len(res.content) > 1000:
                    self.storage.save_cover_image(book_dir, res.content)
        except Exception:
            pass

    async def _update_calibre_records(
        self,
        book_id: int,
        title: str,
        authors: List[str],
        publisher: Optional[str],
        pub_year: Optional[int],
        desc: Optional[str],
        isbn: Optional[str],
    ) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            # Update books table
            pub_date_str = f"{pub_year}-01-01" if pub_year else None
            await db.execute(
                "UPDATE books SET title = ?, sort = ?, pubdate = ?, isbn = ?, has_cover = 1 "
                "WHERE id = ?",
                (title, title, pub_date_str, isbn, book_id),
            )

            # Update authors
            if authors:
                # Remove existing links
                await db.execute("DELETE FROM books_authors_link WHERE book = ?", (book_id,))
                for auth_name in authors:
                    async with db.execute(
                        "SELECT id FROM authors WHERE name = ?", (auth_name,)
                    ) as cur:
                        row = await cur.fetchone()
                        if row:
                            auth_id = row[0]
                        else:
                            cur2 = await db.execute(
                                "INSERT INTO authors (name, sort) VALUES (?, ?)",
                                (auth_name, auth_name),
                            )
                            auth_id = cur2.lastrowid
                    await db.execute(
                        "INSERT INTO books_authors_link (book, author) VALUES (?, ?)",
                        (book_id, auth_id),
                    )

            # Update publisher
            if publisher:
                await db.execute("DELETE FROM books_publishers_link WHERE book = ?", (book_id,))
                async with db.execute(
                    "SELECT id FROM publishers WHERE name = ?", (publisher,)
                ) as cur:
                    row = await cur.fetchone()
                    if row:
                        pub_id = row[0]
                    else:
                        cur2 = await db.execute(
                            "INSERT INTO publishers (name, sort) VALUES (?, ?)",
                            (publisher, publisher),
                        )
                        pub_id = cur2.lastrowid
                await db.execute(
                    "INSERT INTO books_publishers_link (book, publisher) VALUES (?, ?)",
                    (book_id, pub_id),
                )

            # Update comments / description
            if desc:
                await db.execute(
                    "INSERT OR REPLACE INTO comments (book, text) VALUES (?, ?)", (book_id, desc)
                )

            # Update ISBN identifier
            if isbn:
                await db.execute(
                    "INSERT OR REPLACE INTO identifiers (book, type, val) VALUES (?, 'isbn', ?)",
                    (book_id, isbn),
                )

            await db.commit()

    async def _get_book_record(self, book_id: int) -> Optional[Book]:
        from backend.services.ingestion_service import IngestionService

        ingestion = IngestionService(self.library_root)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                return await ingestion._get_book_by_id(db, book_id)
            except Exception:
                return None

    def _find_first_book_file(self, book: Book) -> Optional[Path]:
        for fmt in book.formats:
            if fmt.file_path:
                full_path = self.library_root / fmt.file_path
                if full_path.exists():
                    return full_path
        return None
