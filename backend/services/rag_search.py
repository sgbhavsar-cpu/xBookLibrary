"""Hybrid semantic vector and keyword search service over LanceDB book chunks."""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import lancedb

from backend.domain.rag import SearchResult
from backend.providers.embedding_provider import BaseEmbeddingProvider


class RAGSearchService:
    """Provides hybrid, vector, and keyword search across an indexed library."""

    def __init__(self, embedding_provider: BaseEmbeddingProvider):
        self.embedding_provider = embedding_provider

    def _get_table(self, library_path: Path) -> Any | None:
        vector_dir = library_path / ".vectors"
        if not vector_dir.exists():
            return None

        db = lancedb.connect(str(vector_dir))
        table_name = "book_chunks"
        tables_res = db.list_tables()
        existing_tables = (
            tables_res.tables if hasattr(tables_res, "tables") else list(db.table_names())
        )
        if table_name not in existing_tables:
            return None

        tbl = db.open_table(table_name)
        if tbl.count_rows() == 0:
            return None
        return tbl

    async def search(
        self,
        library_path: Path,
        query: str,
        book_id: int | None = None,
        top_k: int = 5,
        mode: str = "hybrid",
    ) -> list[SearchResult]:
        """Executes hybrid, vector-only, or keyword search across indexed book chunks."""
        tbl = self._get_table(library_path)
        if tbl is None or not query.strip():
            return []

        where_clause = f"book_id = {book_id}" if book_id is not None else None

        # 1. Vector Search
        query_vec = await self.embedding_provider.embed_query(query)
        v_builder = tbl.search(query_vec).metric("cosine").limit(top_k * 3)
        if where_clause:
            v_builder = v_builder.where(where_clause)
        vector_candidates: list[dict[str, Any]] = v_builder.to_list()

        # 2. Keyword Search
        terms = [re.sub(r"[^a-zA-Z0-9]", "", t.lower()) for t in query.split() if len(t) >= 2]
        all_candidates_query = tbl.search().limit(top_k * 10)
        if where_clause:
            all_candidates_query = all_candidates_query.where(where_clause)
        all_pool: list[dict[str, Any]] = all_candidates_query.to_list()

        scored_keywords: list[tuple[float, dict[str, Any]]] = []
        for row in all_pool:
            text_lower = row["content"].lower()
            doc_len = len(text_lower.split()) + 1
            kw_score = 0.0
            for t in terms:
                count = text_lower.count(t)
                if count > 0:
                    kw_score += (count / doc_len) * 100.0
            if kw_score > 0:
                scored_keywords.append((kw_score, row))

        scored_keywords.sort(key=lambda x: x[0], reverse=True)
        keyword_candidates = [x[1] for x in scored_keywords[: top_k * 3]]

        # 3. Apply ranking based on mode
        if mode == "vector":
            results = []
            for item in vector_candidates[:top_k]:
                dist = item.get("_distance", 0.0)
                sim = max(0.0, 1.0 - dist)
                results.append(self._row_to_result(item, score=sim, match_type="vector"))
            return results

        if mode == "keyword":
            results = []
            max_kw = scored_keywords[0][0] if scored_keywords else 1.0
            for score, item in scored_keywords[:top_k]:
                norm_score = min(1.0, score / max_kw) if max_kw > 0 else 0.0
                results.append(self._row_to_result(item, score=norm_score, match_type="keyword"))
            return results

        # Hybrid Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = defaultdict(float)
        item_lookup: dict[str, dict[str, Any]] = {}

        k = 60.0
        for rank, item in enumerate(vector_candidates):
            cid = item["chunk_id"]
            rrf_scores[cid] += 1.0 / (k + rank + 1)
            item_lookup[cid] = item

        for rank, item in enumerate(keyword_candidates):
            cid = item["chunk_id"]
            rrf_scores[cid] += 1.0 / (k + rank + 1)
            item_lookup[cid] = item

        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        max_rrf = sorted_rrf[0][1] if sorted_rrf else 1.0

        hybrid_results: list[SearchResult] = []
        for cid, rrf_score in sorted_rrf[:top_k]:
            raw_item = item_lookup[cid]
            norm_score = round(rrf_score / max_rrf, 4) if max_rrf > 0 else 0.0
            hybrid_results.append(
                self._row_to_result(raw_item, score=norm_score, match_type="hybrid")
            )

        return hybrid_results

    def _row_to_result(self, row: dict[str, Any], score: float, match_type: str) -> SearchResult:
        return SearchResult(
            chunk_id=row["chunk_id"],
            book_id=int(row["book_id"]),
            book_title=row["book_title"],
            authors=row["authors"],
            chapter_index=int(row["chapter_index"]),
            chapter_title=row["chapter_title"],
            content=row["content"],
            score=round(score, 4),
            match_type=match_type,
        )
