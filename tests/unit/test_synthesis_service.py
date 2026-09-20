from unittest.mock import AsyncMock

import aiosqlite
import pytest

from backend.database.schema import CALIBRE_SCHEMA_DDL
from backend.domain.rag import SearchResult
from backend.domain.synthesis import SynthesisDocument, SynthesisSection
from backend.services.document_synthesis_service import DocumentSynthesisService
from backend.services.rag_search import RAGSearchService


@pytest.fixture
async def synthesis_db(tmp_path):
    db_file = tmp_path / "synthesis_test.db"
    async with aiosqlite.connect(str(db_file)) as db:
        await db.executescript(CALIBRE_SCHEMA_DDL)
        await db.commit()
    return db_file


@pytest.fixture
def mock_search_service():
    service = AsyncMock(spec=RAGSearchService)
    service.search.return_value = [
        SearchResult(
            chunk_id="b1_c0",
            book_id=1,
            book_title="Quantum Information",
            authors="Nielsen & Chuang",
            chapter_index=0,
            chapter_title="Chapter 1: Quantum States",
            content="Qubits can exist in a superposition of |0> and |1>.",
            score=0.95,
            match_type="hybrid",
        ),
        SearchResult(
            chunk_id="b2_c1",
            book_id=2,
            book_title="Programming Quantum Computers",
            authors="Eric Johnston",
            chapter_index=1,
            chapter_title="Chapter 2: QPU Architecture",
            content="Physical QPUs apply unitary rotations to manipulate quantum phase.",
            score=0.91,
            match_type="hybrid",
        ),
    ]
    return service


@pytest.mark.asyncio
async def test_outline_generation_templates(mock_search_service):
    synth_service = DocumentSynthesisService(search_service=mock_search_service)

    outline = await synth_service.generate_outline(
        title="Modern Quantum Computing",
        topic_prompt="Compare theoretical and practical architectures.",
        template_type="literature_review",
    )

    assert len(outline) >= 3
    assert "title" in outline[0]
    assert "query" in outline[0]


@pytest.mark.asyncio
async def test_section_drafting_with_inline_citations(mock_search_service):
    async def fake_llm(prompt: str, sys: str) -> str:
        return (
            "Quantum computation fundamentally differs from classical systems. "
            "Superposition allows parallel states "
            "[Quantum Information, Chapter 1: Quantum States], "
            "while physical QPUs implement unitary transformations "
            "[Programming Quantum Computers, Chapter 2: QPU Architecture]."
        )

    synth_service = DocumentSynthesisService(
        search_service=mock_search_service,
        llm_caller=fake_llm,
    )

    section_spec = {
        "title": "Quantum Foundations & Hardware",
        "query": "superposition qpu architecture",
    }
    evidence = mock_search_service.search.return_value

    section = await synth_service.draft_section(
        section_spec=section_spec,
        evidence=evidence,
        topic_prompt="Explain quantum hardware foundations.",
    )

    assert isinstance(section, SynthesisSection)
    assert section.title == "Quantum Foundations & Hardware"
    assert "superposition" in section.content.lower()
    assert len(section.citations) >= 2


@pytest.mark.asyncio
async def test_end_to_end_document_generation(synthesis_db, mock_search_service, tmp_path):
    async def fake_llm(prompt: str, sys: str) -> str:
        return (
            "Analysis demonstrates significant architectural synergy. "
            "As established in [Quantum Information, Chapter 1: Quantum States], "
            "state coherence is critical."
        )

    synth_service = DocumentSynthesisService(
        search_service=mock_search_service,
        llm_caller=fake_llm,
    )

    async with aiosqlite.connect(str(synthesis_db)) as db:
        db.row_factory = aiosqlite.Row

        progress_calls = []

        def on_progress(stage: str, pct: int):
            progress_calls.append((stage, pct))

        doc = await synth_service.generate_document(
            db=db,
            library_path=tmp_path,
            library_id="test_lib",
            title="Comprehensive Quantum Synthesis",
            topic_prompt="Synthesize quantum information principles.",
            template_type="topic_brief",
            book_ids=[1, 2],
            progress_callback=on_progress,
        )

        assert isinstance(doc, SynthesisDocument)
        assert doc.title == "Comprehensive Quantum Synthesis"
        assert len(doc.sources) >= 1
        assert doc.word_count > 0
        assert "## Bibliography & Cited Sources" in doc.content_markdown
        assert len(progress_calls) >= 3

        # Verify persistence in SQLite x_synthesis_documents
        async with db.execute("SELECT * FROM x_synthesis_documents WHERE id = ?", (doc.id,)) as cur:
            row = await cur.fetchone()
            assert row is not None
            assert row["title"] == "Comprehensive Quantum Synthesis"
            assert row["template_type"] == "topic_brief"
