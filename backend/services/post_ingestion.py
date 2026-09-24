"""Automated post-ingestion workflow: metadata download, RAG indexing, and AI summary."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import aiosqlite

from backend.config import ConfigManager
from backend.services.enrichment_orchestrator import EnrichmentOrchestrator
from backend.services.rag_indexer import RAGIndexer
from backend.services.summarization_service import SummarizationService

logger = logging.getLogger(__name__)


async def trigger_post_ingestion_pipeline(
    book_id: int,
    library_path: Path,
    library_id: Optional[str] = None,
    auto_download_metadata: Optional[bool] = None,
    auto_index_rag: Optional[bool] = None,
    auto_generate_summary: Optional[bool] = None,
) -> None:
    """Executes configured automated post-ingestion tasks asynchronously in the background.

    Runs:
    1. Online metadata download & enrichment (Google Books, OpenLibrary, CrossRef)
    2. LanceDB chunk vector indexing for RAG chat
    3. Multi-resolution AI summary generation
    """
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    prefs = cfg.preferences

    download_meta = (
        auto_download_metadata if auto_download_metadata is not None else prefs.auto_download_metadata
    )
    index_rag = (
        auto_index_rag if auto_index_rag is not None else prefs.auto_index_rag
    )
    gen_summary = (
        auto_generate_summary if auto_generate_summary is not None else prefs.auto_generate_summary
    )

    if not (download_meta or index_rag or gen_summary):
        return

    logger.info(
        "[Post-Ingestion] Starting pipeline for book %d (meta=%s, rag=%s, summary=%s)",
        book_id,
        download_meta,
        index_rag,
        gen_summary,
    )

    # 1. Automatic Metadata Enrichment / Download
    if download_meta:
        try:
            logger.info("[Post-Ingestion] Downloading metadata for book %d...", book_id)
            orchestrator = EnrichmentOrchestrator(library_path)
            res = await orchestrator.enrich_book(book_id)
            logger.info("[Post-Ingestion] Metadata enrichment for book %d finished: %s", book_id, res.status)
        except Exception as e:
            logger.warning("[Post-Ingestion] Metadata download failed for book %d: %s", book_id, e)

    # 2. Automatic RAG Indexing
    if index_rag:
        try:
            logger.info("[Post-Ingestion] Indexing book %d for RAG chat...", book_id)
            # Import embedder provider from rag_router
            from backend.api.rag_router import _get_embedding_provider

            embedder = _get_embedding_provider()
            indexer = RAGIndexer(embedding_provider=embedder)
            db_file = library_path / "metadata.db"
            async with aiosqlite.connect(str(db_file)) as db:
                db.row_factory = aiosqlite.Row
                res = await indexer.index_book(
                    book_id=book_id,
                    library_id=library_id or "",
                    library_path=library_path,
                    db=db,
                    force=False,
                )
            logger.info("[Post-Ingestion] RAG indexing completed for book %d: %s", book_id, res.get("status"))
        except Exception as e:
            logger.warning("[Post-Ingestion] RAG indexing failed for book %d: %s", book_id, e)

    # 3. Automatic AI Multi-Resolution Summary
    if gen_summary:
        try:
            logger.info("[Post-Ingestion] Generating AI summary for book %d...", book_id)
            summarizer = SummarizationService(library_path)
            await summarizer.summarize_book(book_id=book_id)
            logger.info("[Post-Ingestion] AI summary generated successfully for book %d", book_id)
        except Exception as e:
            logger.warning("[Post-Ingestion] AI summary generation failed for book %d: %s", book_id, e)
