"""Unit tests for the multi-resolution AI summarization service."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.domain.summary import BookSummary
from backend.services.ingestion_service import IngestionService
from backend.services.library_manager import LibraryManager
from backend.services.summarization_service import SummarizationService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_chapter_text_extraction(tmp_path: Path):
    """Verifies that the summarization service extracts chapters from book files."""
    lib_dir = tmp_path / "ExtractLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Extract Lib", set_active=False)

    epub_file = tmp_path / "chapters.epub"
    create_sample_epub(epub_file, title="Quantum Foundations", author="Alice Q.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None

    service = SummarizationService(library_root=lib_dir)
    chapters = await service.extract_chapters_from_book(book.id)

    assert len(chapters) >= 1
    assert "chapter_title" in chapters[0]
    assert "text" in chapters[0]
    assert len(chapters[0]["text"]) > 0


@pytest.mark.asyncio
async def test_map_reduce_summarization(tmp_path: Path):
    """Verifies map-reduce execution: chapter map step and executive reduce step."""
    lib_dir = tmp_path / "MapReduceLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Map Reduce Lib", set_active=False)

    epub_file = tmp_path / "complex_book.epub"
    create_sample_epub(epub_file, title="Theory of Computation", author="Alan T.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None

    service = SummarizationService(library_root=lib_dir)

    # Mock chapter-level LLM map response
    mock_chapter_summary = {
        "summary": "This chapter introduces Turing machines and deterministic automata.",
        "key_takeaways": [
            "Turing machines provide a formal model of computation.",
            "Halting problem is undecidable.",
        ],
        "important_quotes": ["Computing machines are capable of executing any algorithm."],
    }

    # Mock reduce synthesis response
    mock_reduce_summary = {
        "executive_snapshot": {
            "hook": "A seminal exploration of the mathematical limits of computation.",
            "core_thesis": "Computable functions correspond to Turing-computable functions.",
            "target_audience": "Computer scientists, mathematicians, and logicians.",
            "key_arguments": [
                "Universal computation is possible with simple rules.",
                "Incompleteness and undecidability bound mechanical computation.",
            ],
            "estimated_reading_time_minutes": 240,
        },
        "conceptual_index": {
            "frameworks": ["Universal Turing Machine", "Church-Turing Thesis"],
            "key_takeaways": [
                "Some well-defined mathematical problems have no algorithmic solution."
            ],
            "quotable_moments": [
                {
                    "quote": "A man computing a real number is comparable to a machine.",
                    "source": "Chapter 1",
                }
            ],
            "action_items": ["Model computation using state transition tables."],
        },
    }

    with (
        patch.object(
            service,
            "_call_chapter_summarizer",
            new_callable=AsyncMock,
            return_value=mock_chapter_summary,
        ),
        patch.object(
            service,
            "_call_reduce_synthesizer",
            new_callable=AsyncMock,
            return_value=mock_reduce_summary,
        ),
    ):
        summary: BookSummary = await service.summarize_book(book_id=book.id)

        assert summary.book_id == book.id
        assert summary.executive_snapshot.hook.startswith("A seminal exploration")
        assert len(summary.executive_snapshot.key_arguments) == 2
        assert len(summary.chapters) >= 1
        assert summary.chapters[0].summary.startswith("This chapter introduces")
        assert len(summary.conceptual_index.frameworks) == 2
        assert summary.metadata.model_name is not None


@pytest.mark.asyncio
async def test_single_pass_short_book_fallback(tmp_path: Path):
    """Verifies that short works (< 3000 words) execute an optimized single-pass summary."""
    lib_dir = tmp_path / "SinglePassLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Single Pass Lib", set_active=False)

    epub_file = tmp_path / "essay.epub"
    create_sample_epub(epub_file, title="Brief Essay on Logic", author="Bertrand R.")

    ingestion = IngestionService(lib_dir)
    book = await ingestion.ingest_file(epub_file)
    assert book.id is not None

    service = SummarizationService(library_root=lib_dir)

    mock_full_summary = {
        "executive_snapshot": {
            "hook": "A succinct breakdown of formal logical propositions.",
            "core_thesis": "Logic is the foundation of mathematical certainty.",
            "target_audience": "Philosophy and mathematics students.",
            "key_arguments": ["Propositions have truth values independently of minds."],
            "estimated_reading_time_minutes": 25,
        },
        "chapters": [
            {
                "chapter_index": 1,
                "chapter_title": "Full Text Synthesis",
                "summary": "Covers foundational propositional calculus and symbolic logic.",
                "key_takeaways": ["Symbolic notation eliminates linguistic ambiguity."],
                "important_quotes": ["Logic is the youth of mathematics."],
            }
        ],
        "conceptual_index": {
            "frameworks": ["Propositional Calculus"],
            "key_takeaways": ["Truth values are invariant under isomorphic transformation."],
            "quotable_moments": [
                {"quote": "Logic is the youth of mathematics.", "source": "Section 1"}
            ],
            "action_items": ["Translate natural language sentences into symbolic logic."],
        },
    }

    with patch.object(
        service,
        "_call_single_pass_summarizer",
        new_callable=AsyncMock,
        return_value=mock_full_summary,
    ):
        summary = await service.summarize_book(book_id=book.id, force_single_pass=True)

        assert summary.book_id == book.id
        assert summary.executive_snapshot.core_thesis.startswith("Logic is the foundation")
        assert len(summary.chapters) == 1
        assert summary.chapters[0].chapter_title == "Full Text Synthesis"
