"""Unit tests for dual-taxonomy BISAC and Dewey Decimal classification service."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.domain.classification import ClassificationResult
from backend.domain.entities import Book, TocNode
from backend.services.classification_service import ClassificationService
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_offline_heuristic_classification():
    """Verifies that offline keyword heuristic accurately maps known tech and fiction books."""
    service = ClassificationService(library_root=Path("."))

    # Technical book
    tech_book = Book(
        id=1,
        title="Designing Data-Intensive Applications",
        authors=["Martin Kleppmann"],
        tags=["database", "distributed systems"],
        description="The big ideas behind reliable, scalable, and maintainable systems.",
    )
    tech_res = await service.classify_heuristically(tech_book)
    assert tech_res.bisac_code == "COM014000"
    assert "Database Management" in tech_res.bisac_heading
    assert tech_res.ddc_code == "005.74"
    assert tech_res.confidence >= 0.70

    # Fiction book
    sci_fi_book = Book(
        id=2,
        title="Dune Messiah",
        authors=["Frank Herbert"],
        tags=["Science Fiction", "space opera"],
        description="Paul Atreides rules the known universe as Emperor.",
    )
    fiction_res = await service.classify_heuristically(sci_fi_book)
    assert fiction_res.bisac_code == "FIC028000"
    assert "Science Fiction" in fiction_res.bisac_heading
    assert fiction_res.ddc_code == "813.54"


@pytest.mark.asyncio
async def test_llm_classification_and_sqlite_persistence(tmp_path: Path):
    """Verifies LLM-based classification with Calibre tag injection and x_classifications update."""
    lib_dir = tmp_path / "ClassificationLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Classification Lib", set_active=False)

    epub_file = tmp_path / "deep_learning.epub"
    create_sample_epub(epub_file, title="Deep Learning Fundamentals", author="Ian G.")

    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    book_id = book.id or 1

    service = ClassificationService(library_root=lib_dir)

    mock_llm_response = {
        "bisac_code": "COM051260",
        "bisac_heading": "COMPUTERS / Artificial Intelligence / Machine Learning",
        "ddc_code": "006.3",
        "confidence": 0.96,
        "suggested_tags": ["Artificial Intelligence", "Deep Learning", "Neural Networks"],
        "reasoning": "Comprehensive study of neural architectures and gradient descent.",
    }

    with patch.object(service, "_call_llm_classifier", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_llm_response

        res = await service.classify_book(book_id, auto_apply=True)

        assert isinstance(res, ClassificationResult)
        assert res.bisac_code == "COM051260"
        assert res.ddc_code == "006.3"
        assert res.confidence == 0.96
        assert res.applied is True

        # Check SQLite persistence in x_classifications
        import aiosqlite

        async with aiosqlite.connect(lib_dir / "metadata.db") as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT bisac_code, ddc_code, confidence FROM x_classifications WHERE book_id = ?",
                (book_id,),
            ) as cur:
                row = await cur.fetchone()
                assert row is not None
                assert row["bisac_code"] == "COM051260"
                assert row["ddc_code"] == "006.3"

            query = (
                "SELECT t.name FROM tags t JOIN books_tags_link btl ON t.id = btl.tag "
                "WHERE btl.book = ?"
            )
            async with db.execute(query, (book_id,)) as cur:
                tags = [r["name"] for r in await cur.fetchall()]
                assert "Artificial Intelligence" in tags
                assert "Deep Learning" in tags


@pytest.mark.asyncio
async def test_toc_sampling_for_sparse_metadata(tmp_path: Path):
    """Verifies that book with empty description uses Table of Contents outline for context."""
    lib_dir = tmp_path / "TOCLib"
    service = ClassificationService(library_root=lib_dir)

    sparse_book = Book(
        id=5,
        title="Modern Robotics",
        authors=["Kevin M."],
        description=None,
        tags=[],
        toc=[
            TocNode(id=1, book_id=5, title="Chapter 1: Kinematics", order_index=0),
            TocNode(id=2, book_id=5, title="Chapter 2: Dynamics and Control", order_index=1),
            TocNode(id=3, book_id=5, title="Chapter 3: Motion Planning", order_index=2),
        ],
    )

    context = service._build_classification_prompt_context(sparse_book)
    assert "Chapter 1: Kinematics" in context
    assert "Dynamics and Control" in context
    assert "Motion Planning" in context
