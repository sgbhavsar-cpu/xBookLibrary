"""AI-powered dual-taxonomy classification service (BISAC & Dewey Decimal)."""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from backend.config import ConfigManager
from backend.data.bisac_ddc_reference import classify_heuristically as heuristic_match
from backend.domain.classification import ClassificationResult
from backend.domain.enrichment import MetadataProposal, ProposedField
from backend.domain.entities import Book
from backend.providers.llm_adapter import LiteLLMClientAdapter
from backend.services.proposal_manager import ProposalManager
from backend.services.storage_service import StorageService

NOISE_TAGS = {
    "ebook",
    "general",
    "kindle",
    "kindle edition",
    "paperback",
    "hardcover",
    "misc",
    "unclassified",
    "unknown",
    "books",
    "print",
}


def clean_semantic_tags(tags: List[str]) -> List[str]:
    """Filters generic noise words and normalizes semantic tags."""
    cleaned = []
    seen = set()
    for tag in tags:
        t = tag.strip()
        if not t or t.lower() in NOISE_TAGS:
            continue
        normalized = t.title() if len(t) > 3 and not t.isupper() else t
        if normalized.lower() not in seen:
            seen.add(normalized.lower())
            cleaned.append(normalized)
    return cleaned


class ClassificationService:
    """Classifies books using LLMs (Gemini / Ollama) with offline heuristic fallback."""

    def __init__(
        self,
        library_root: Path,
        config_manager: Optional[ConfigManager] = None,
        llm_adapter: Optional[LiteLLMClientAdapter] = None,
    ):
        self.library_root = library_root
        self.db_path = library_root / "metadata.db"
        self.config_manager = config_manager or ConfigManager()
        self.llm_adapter = llm_adapter or LiteLLMClientAdapter(config_manager=self.config_manager)
        self.storage = StorageService(library_root)
        self.proposal_mgr = ProposalManager(library_root)

    async def classify_heuristically(self, book: Book) -> ClassificationResult:
        """Applies offline heuristic keyword matching against curated BISAC/DDC tables."""
        author = book.authors[0] if book.authors else None
        code, heading, ddc, conf = heuristic_match(
            title=book.title,
            author=author,
            tags=book.tags,
            description=book.description,
        )
        return ClassificationResult(
            book_id=book.id or 0,
            bisac_code=code,
            bisac_heading=heading,
            ddc_code=ddc,
            confidence=conf,
            suggested_tags=[heading.split(" / ")[0]],
            reasoning="Matched via offline bibliographic reference taxonomy.",
        )

    def _build_classification_prompt_context(self, book: Book) -> str:
        """Formats bibliographic data and Table of Contents for prompt context."""
        parts = [
            f"Title: {book.title}",
            f"Authors: {', '.join(book.authors) if book.authors else 'Unknown'}",
        ]
        if book.tags:
            parts.append(f"Current Tags: {', '.join(book.tags)}")
        if book.description:
            parts.append(f"Description: {book.description}")

        if book.toc:
            toc_lines = [f"- {node.title}" for node in book.toc[:15]]
            parts.append("Table of Contents:\n" + "\n".join(toc_lines))

        return "\n\n".join(parts)

    async def _call_llm_classifier(self, context_text: str) -> Optional[Dict[str, Any]]:
        """Invokes LiteLLM to categorize book into standard BISAC and DDC schema."""
        try:
            import litellm

            system_prompt = (
                "You are an expert librarian and bibliographic cataloger. "
                "Analyze the provided book information and classify it using standard "
                "BISAC Subject Headings and Dewey Decimal Classification (DDC).\n"
                "Return pure JSON with the exact fields:\n"
                "- bisac_code: (9-character BISAC code, e.g. 'COM051010')\n"
                "- bisac_heading: (Full BISAC heading, e.g. 'COMPUTERS / Programming / General')\n"
                "- ddc_code: (Dewey Decimal notation, e.g. '005.1' or '813.54')\n"
                "- confidence: (float between 0.0 and 1.0)\n"
                "- suggested_tags: (list of 3 to 6 high-specificity topical tags)\n"
                "- reasoning: (concise 1-sentence cataloging rationale)\n"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context_text},
            ]

            response = await litellm.acompletion(
                model=self.llm_adapter.model_name,
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            return json.loads(content)
        except Exception:
            return None

    async def classify_book(self, book_id: int, auto_apply: bool = True) -> ClassificationResult:
        """Classifies a book by ID using LLM with offline fallback."""
        book = await self._get_book_by_id(book_id)
        if not book:
            raise ValueError(f"Book with id {book_id} not found")

        context = self._build_classification_prompt_context(book)
        llm_data = await self._call_llm_classifier(context)

        if llm_data and "bisac_code" in llm_data and "ddc_code" in llm_data:
            result = ClassificationResult(
                book_id=book_id,
                bisac_code=str(llm_data.get("bisac_code")),
                bisac_heading=str(llm_data.get("bisac_heading", "")),
                ddc_code=str(llm_data.get("ddc_code")),
                confidence=float(llm_data.get("confidence", 0.90)),
                suggested_tags=list(llm_data.get("suggested_tags", [])),
                reasoning=str(llm_data.get("reasoning", "Classified via LLM")),
            )
        else:
            # Fallback to offline heuristic matcher
            result = await self.classify_heuristically(book)

        # Confidence safeguard (Principle III)
        if result.confidence >= 0.85 and auto_apply:
            await self._apply_classification_to_db(book, result)
            result.applied = True
        else:
            # Stage proposal for review
            proposal_id = self._stage_classification_proposal(book, result)
            result.applied = False
            result.proposal_id = proposal_id

        return result

    async def _apply_classification_to_db(
        self, book: Book, classification: ClassificationResult
    ) -> None:
        """Persists classification to x_classifications, updates Calibre tags, and rewrites OPF."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Insert or replace in x_classifications
            await db.execute(
                """
                INSERT OR REPLACE INTO x_classifications
                (book_id, bisac_code, bisac_heading, ddc_code, confidence, reasoning)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    book.id,
                    classification.bisac_code,
                    classification.bisac_heading,
                    classification.ddc_code,
                    classification.confidence,
                    classification.reasoning,
                ),
            )

            # 2. Insert cleaned tags into tags and books_tags_link
            combined_tags = (
                book.tags + classification.suggested_tags + [f"DDC {classification.ddc_code}"]
            )
            new_tags = clean_semantic_tags(combined_tags)

            for tag_name in new_tags:
                clean_tag = tag_name.strip()
                if not clean_tag:
                    continue
                async with db.execute("SELECT id FROM tags WHERE name = ?", (clean_tag,)) as cur:
                    row = await cur.fetchone()
                    if row:
                        tag_id = row[0]
                    else:
                        cur2 = await db.execute("INSERT INTO tags (name) VALUES (?)", (clean_tag,))
                        tag_id = cur2.lastrowid

                await db.execute(
                    "INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (?, ?)",
                    (book.id, tag_id),
                )

            await db.commit()

        # 3. Update metadata.opf
        updated_book = await self._get_book_by_id(book.id or 0)
        if updated_book:
            book_dir = self.library_root / updated_book.path
            self.storage.write_metadata_opf(book_dir, updated_book)

    def _stage_classification_proposal(
        self, book: Book, classification: ClassificationResult
    ) -> str:
        """Stages an ephemeral classification proposal for user confirmation."""
        proposal_id = f"prop-cls-{uuid.uuid4().hex[:8]}"
        fields: Dict[str, ProposedField] = {
            "bisac": ProposedField(
                field_name="bisac",
                current_value=None,
                proposed_value=f"{classification.bisac_code} - {classification.bisac_heading}",
                source="ai_classifier",
                confidence=classification.confidence,
            ),
            "ddc": ProposedField(
                field_name="ddc",
                current_value=None,
                proposed_value=classification.ddc_code,
                source="ai_classifier",
                confidence=classification.confidence,
            ),
            "suggested_tags": ProposedField(
                field_name="suggested_tags",
                current_value=", ".join(book.tags),
                proposed_value=", ".join(classification.suggested_tags),
                source="ai_classifier",
                confidence=classification.confidence,
            ),
        }

        proposal = MetadataProposal(
            id=proposal_id,
            book_id=book.id or 0,
            is_exact_isbn=False,
            composite_confidence=classification.confidence,
            fields=fields,
        )
        self.proposal_mgr.save_proposal(proposal)
        return proposal_id

    async def apply_classification_proposal(
        self, proposal_id: str, field_overrides: Optional[Dict[str, Any]] = None
    ) -> Book:
        """Applies an approved classification proposal to Calibre records and cleans staging."""
        proposal = self.proposal_mgr.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found in staging")

        book = await self._get_book_by_id(proposal.book_id)
        if not book:
            raise ValueError(f"Book {proposal.book_id} not found")

        bisac_raw = proposal.fields.get("bisac")
        bisac_str = str(bisac_raw.proposed_value if bisac_raw else "GEN000000 - GENERAL / General")
        bisac_code, _, bisac_heading = bisac_str.partition(" - ")
        if not bisac_heading:
            bisac_heading = bisac_code

        ddc_raw = proposal.fields.get("ddc")
        ddc_code = str(ddc_raw.proposed_value if ddc_raw else "000")

        tags_raw = proposal.fields.get("suggested_tags")
        suggested_tags = [
            t.strip() for t in str(tags_raw.proposed_value or "").split(",") if t.strip()
        ]

        if field_overrides:
            if "bisac" in field_overrides:
                bisac_code, _, bisac_heading = field_overrides["bisac"].partition(" - ")
            if "ddc" in field_overrides:
                ddc_code = field_overrides["ddc"]
            if "suggested_tags" in field_overrides:
                val = field_overrides["suggested_tags"]
                if isinstance(val, list):
                    suggested_tags = val
                else:
                    suggested_tags = [t.strip() for t in str(val).split(",") if t.strip()]

        result = ClassificationResult(
            book_id=proposal.book_id,
            bisac_code=bisac_code.strip(),
            bisac_heading=bisac_heading.strip(),
            ddc_code=ddc_code.strip(),
            confidence=proposal.composite_confidence,
            suggested_tags=clean_semantic_tags(suggested_tags),
            reasoning="Approved from classification proposal.",
        )

        await self._apply_classification_to_db(book, result)
        self.proposal_mgr.discard_proposal(proposal_id)

        updated_book = await self._get_book_by_id(proposal.book_id)
        assert updated_book is not None
        return updated_book

    async def _get_book_by_id(self, book_id: int) -> Optional[Book]:
        from backend.services.ingestion_service import IngestionService

        ingestion = IngestionService(self.library_root)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                return await ingestion._get_book_by_id(db, book_id)
            except Exception:
                return None
