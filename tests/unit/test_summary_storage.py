"""Unit tests for summary dual-storage (summary.json on disk + x_summaries in SQLite)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

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
from backend.services.summarization_service import SummarizationService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_summary_dual_storage_and_cache(tmp_path: Path):
    """Verifies that summaries write to both summary.json on disk and x_summaries in SQLite."""
    lib_dir = tmp_path / "DualStorageLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Dual Storage Lib", set_active=False)

    epub_file = tmp_path / "book.epub"
    create_sample_epub(epub_file, title="Cosmology Insights", author="Stephen H.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None

    service = SummarizationService(library_root=lib_dir)

    mock_summary = {
        "executive_snapshot": {
            "hook": "A brief look at the cosmic origins.",
            "core_thesis": "The universe expanded from a singular point.",
            "target_audience": "Curious minds.",
            "key_arguments": ["Spacetime has a geometric curvature."],
            "estimated_reading_time_minutes": 150,
        },
        "chapters": [
            {
                "chapter_index": 1,
                "chapter_title": "Our Picture of the Universe",
                "summary": "Reviews historical cosmological models from Aristotle to Hubble.",
                "key_takeaways": ["The universe is dynamic, not static."],
                "important_quotes": ["The universe was not always here."],
            }
        ],
        "conceptual_index": {
            "frameworks": ["Big Bang Theory"],
            "key_takeaways": ["Cosmic expansion implies a beginning."],
            "quotable_moments": [
                {"quote": "The universe was not always here.", "source": "Chapter 1"}
            ],
            "action_items": ["Observe redshift in astronomical data."],
        },
    }

    with patch.object(
        service,
        "_call_single_pass_summarizer",
        new_callable=AsyncMock,
        return_value=mock_summary,
    ):
        _ = await service.summarize_book(book_id=book.id, force_single_pass=True)

        # 1. Verify physical summary.json on disk
        book_dir = service.storage.resolve_book_path(book.path)
        summary_file = book_dir / "summary.json"
        assert summary_file.exists(), f"Expected {summary_file} to exist on disk"
        disk_data = json.loads(summary_file.read_text(encoding="utf-8"))
        assert disk_data["book_id"] == book.id
        assert disk_data["executive_snapshot"]["hook"] == "A brief look at the cosmic origins."

        # 2. Verify relational record in x_summaries table
        async with aiosqlite.connect(lib_dir / "metadata.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM x_summaries WHERE book_id = ?", (book.id,)) as cur:
                row = await cur.fetchone()
                assert row is not None
                assert row["book_id"] == book.id
                db_exec = json.loads(row["executive_snapshot"])
                assert db_exec["core_thesis"] == "The universe expanded from a singular point."

        # 3. Verify instant cached retrieval without re-summarizing
        with patch.object(service, "_call_single_pass_summarizer") as mock_never_called:
            cached: BookSummary = await service.get_summary(book_id=book.id)
            assert cached is not None
            assert cached.book_id == book.id
            assert cached.executive_snapshot.hook == "A brief look at the cosmic origins."
            mock_never_called.assert_not_called()


@pytest.mark.asyncio
async def test_adoption_of_existing_summary_json(tmp_path: Path):
    """Verifies that pre-existing summary.json on disk is adopted into SQLite during get_summary."""
    lib_dir = tmp_path / "AdoptLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Adopt Lib", set_active=False)

    epub_file = tmp_path / "relativity.epub"
    create_sample_epub(epub_file, title="Special Relativity", author="Albert E.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None

    service = SummarizationService(library_root=lib_dir)

    # Simulate an adopted library: manually write summary.json to disk without SQLite record
    book_dir = service.storage.resolve_book_path(book.path)
    summary_file = book_dir / "summary.json"
    existing_summary = BookSummary(
        book_id=book.id,
        executive_snapshot=ExecutiveSnapshot(
            hook="The speed of light is constant in all inertial frames.",
            core_thesis="Time and space are relative to the observer.",
            target_audience="Physicists",
            key_arguments=["Simultaneity is relative."],
            estimated_reading_time_minutes=90,
        ),
        chapters=[
            ChapterSummary(
                chapter_index=1,
                chapter_title="Inertial Frames",
                summary="Discusses Galilean relativity and Maxwell electrodynamics.",
                key_takeaways=["Electrodynamics requires constant c."],
                important_quotes=["Speed of light is invariant."],
            )
        ],
        conceptual_index=ConceptualIndex(
            frameworks=["Lorentz Transformation"],
            key_takeaways=["Time dilation occurs at relativistic speeds."],
            quotable_moments=[{"quote": "Speed of light is invariant.", "source": "Chapter 1"}],
            action_items=["Derive Lorentz factor gamma."],
        ),
        metadata=SummaryMetadata(model_name="manual-import"),
    )
    summary_file.write_text(existing_summary.model_dump_json(indent=2), encoding="utf-8")

    # Assert SQLite table does NOT have it yet
    async with aiosqlite.connect(lib_dir / "metadata.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM x_summaries WHERE book_id = ?", (book.id,)
        ) as cur:
            count = (await cur.fetchone())[0]
            assert count == 0

    # Retrieve via service -> should detect summary.json, adopt to SQLite, and return
    service = SummarizationService(library_root=lib_dir)
    retrieved = await service.get_summary(book.id)
    assert retrieved is not None
    assert (
        retrieved.executive_snapshot.core_thesis == "Time and space are relative to the observer."
    )

    # Now verify it was persisted to SQLite
    async with aiosqlite.connect(lib_dir / "metadata.db") as db:
        async with db.execute(
            "SELECT COUNT(*) FROM x_summaries WHERE book_id = ?", (book.id,)
        ) as cur:
            count = (await cur.fetchone())[0]
            assert count == 1
