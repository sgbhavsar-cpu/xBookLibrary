"""Unit tests for summary export formatters (Markdown, HTML) and Calibre OPF sync."""

import xml.etree.ElementTree as ET
from pathlib import Path

import aiosqlite
import pytest

from backend.domain.summary import (
    BookSummary,
    ChapterSummary,
    ConceptualIndex,
    ExecutiveSnapshot,
    SummaryMetadata,
)
from backend.services.ingestion_service import IngestionService
from backend.services.library_manager import LibraryManager
from backend.services.summary_exporter import SummaryExporter
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def sample_summary() -> BookSummary:
    """Fixture providing a rich BookSummary object."""
    return BookSummary(
        book_id=1,
        executive_snapshot=ExecutiveSnapshot(
            hook="A comprehensive treatise on modern artificial intelligence.",
            core_thesis="Deep learning and foundation models enable generalized reasoning.",
            target_audience="Engineers, researchers, and technical leaders.",
            key_arguments=[
                "Transformers scale predictably with compute and data.",
                "Reinforcement learning from human feedback aligns model outputs.",
                "Inference efficiency is key for deployment.",
            ],
            estimated_reading_time_minutes=360,
        ),
        chapters=[
            ChapterSummary(
                chapter_index=1,
                chapter_title="Foundations of Machine Learning",
                summary="Covers supervised learning, loss functions, and gradient descent.",
                key_takeaways=["Backpropagation calculates exact parameter gradients."],
                important_quotes=["Gradient descent is optimization in high dimensions."],
            ),
            ChapterSummary(
                chapter_index=2,
                chapter_title="Attention and Transformers",
                summary="Explains self-attention, multi-head projections, and positional encoding.",
                key_takeaways=["Attention replaces recurrence with parallel computation."],
                important_quotes=["Attention is all you need."],
            ),
        ],
        conceptual_index=ConceptualIndex(
            frameworks=["Self-Attention Mechanism", "Scaling Laws"],
            key_takeaways=["Scaling parameters and compute leads to emergent abilities."],
            quotable_moments=[{"quote": "Attention is all you need.", "source": "Chapter 2"}],
            action_items=["Profile GPU memory when configuring attention key-value caches."],
        ),
        metadata=SummaryMetadata(model_name="gemini-2.5-flash", duration_seconds=12.4),
    )


def test_export_markdown(sample_summary: BookSummary):
    """Verifies that export_markdown produces structured GitHub-Flavored Markdown."""
    exporter = SummaryExporter()
    md = exporter.export_markdown(
        sample_summary, book_title="AI Architecture", authors=["Jane Doe"]
    )

    assert "# AI Architecture" in md
    assert "**Authors**: Jane Doe" in md
    assert "## Executive Snapshot" in md
    assert "A comprehensive treatise on modern artificial intelligence." in md
    assert "### Chapter 1: Foundations of Machine Learning" in md
    assert "### Chapter 2: Attention and Transformers" in md
    assert "## Conceptual Index & Action Items" in md
    assert "Self-Attention Mechanism" in md
    assert "Attention is all you need." in md


def test_export_html(sample_summary: BookSummary):
    """Verifies that export_html produces valid, styled HTML document."""
    exporter = SummaryExporter()
    html = exporter.export_html(sample_summary, book_title="AI Architecture", authors=["Jane Doe"])

    assert "<!DOCTYPE html>" in html
    assert "<title>Summary: AI Architecture</title>" in html
    assert "<h1>AI Architecture</h1>" in html
    assert "Foundations of Machine Learning" in html
    assert "Scaling Laws" in html
    assert "style>" in html


@pytest.mark.asyncio
async def test_sync_to_calibre_metadata(tmp_path: Path, sample_summary: BookSummary):
    """Verifies that sync_to_calibre_metadata writes to comments table and metadata.opf."""
    lib_dir = tmp_path / "SyncLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Sync Lib", set_active=False)

    epub_file = tmp_path / "ai.epub"
    create_sample_epub(epub_file, title="AI Architecture", author="Jane Doe")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None
    sample_summary.book_id = book.id

    exporter = SummaryExporter(library_root=lib_dir)
    synced = await exporter.sync_to_calibre_metadata(book_id=book.id, summary=sample_summary)
    assert synced is True

    # 1. Check Calibre SQLite comments table
    async with aiosqlite.connect(lib_dir / "metadata.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT text FROM comments WHERE book = ?", (book.id,)) as cur:
            row = await cur.fetchone()
            assert row is not None
            assert "A comprehensive treatise on modern artificial intelligence." in row["text"]

    # 2. Check metadata.opf dc:description
    book_dir = exporter.storage.resolve_book_path(book.path)
    opf_file = book_dir / "metadata.opf"
    assert opf_file.exists()
    root = ET.fromstring(opf_file.read_text(encoding="utf-8"))
    ns = {"dc": "http://purl.org/dc/elements/1.1/"}
    desc_el = root.find(".//dc:description", ns)
    assert desc_el is not None
    assert "A comprehensive treatise on modern artificial intelligence." in desc_el.text
