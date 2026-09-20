from unittest.mock import AsyncMock

import aiosqlite
import pytest

from backend.database.schema import CALIBRE_SCHEMA_DDL
from backend.domain.rag import SearchResult
from backend.services.rag_chat_agent import RAGChatAgent
from backend.services.rag_search import RAGSearchService


@pytest.fixture
async def chat_db(tmp_path):
    db_file = tmp_path / "chat_test.db"
    async with aiosqlite.connect(str(db_file)) as db:
        await db.executescript(CALIBRE_SCHEMA_DDL)
        await db.commit()
    return db_file


@pytest.mark.asyncio
async def test_session_lifecycle(chat_db):
    search_mock = AsyncMock(spec=RAGSearchService)
    llm_mock = AsyncMock()
    agent = RAGChatAgent(search_service=search_mock, llm_adapter=llm_mock)

    async with aiosqlite.connect(str(chat_db)) as db:
        db.row_factory = aiosqlite.Row

        # 1. Create session
        session = await agent.create_session(
            db=db, library_id="main_lib", book_id=42, title="Quantum Discussion"
        )
        assert session.id is not None
        assert session.library_id == "main_lib"
        assert session.book_id == 42
        assert session.title == "Quantum Discussion"

        # 2. Get session
        retrieved = await agent.get_session(db=db, session_id=session.id)
        assert retrieved is not None
        assert retrieved.id == session.id

        # 3. List sessions
        sessions = await agent.list_sessions(db=db, library_id="main_lib")
        assert len(sessions) == 1

        # 4. Delete session
        deleted = await agent.delete_session(db=db, session_id=session.id)
        assert deleted is True
        assert await agent.get_session(db=db, session_id=session.id) is None


@pytest.mark.asyncio
async def test_grounded_answer_with_citations(chat_db, tmp_path):
    search_mock = AsyncMock(spec=RAGSearchService)
    search_mock.search.return_value = [
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
        )
    ]

    llm_mock = AsyncMock()
    answer_text = (
        "Qubits can exist in superposition as described in "
        "[Quantum Information, Chapter 1: Quantum States]."
    )
    llm_mock.generate_response.return_value = answer_text

    agent = RAGChatAgent(search_service=search_mock, llm_adapter=llm_mock)

    async with aiosqlite.connect(str(chat_db)) as db:
        db.row_factory = aiosqlite.Row
        session = await agent.create_session(db=db, library_id="main_lib")

        # Send user message
        assistant_msg = await agent.send_message(
            db=db,
            library_path=tmp_path,
            session_id=session.id,
            user_prompt="What is a qubit state?",
        )

        assert assistant_msg.role == "assistant"
        assert "superposition" in assistant_msg.content
        assert len(assistant_msg.citations) > 0
        assert assistant_msg.citations[0].book_title == "Quantum Information"
        assert assistant_msg.citations[0].chapter_title == "Chapter 1: Quantum States"


@pytest.mark.asyncio
async def test_refusal_when_no_context_found(chat_db, tmp_path):
    search_mock = AsyncMock(spec=RAGSearchService)
    search_mock.search.return_value = []  # No books found

    llm_mock = AsyncMock()

    agent = RAGChatAgent(search_service=search_mock, llm_adapter=llm_mock)

    async with aiosqlite.connect(str(chat_db)) as db:
        db.row_factory = aiosqlite.Row
        session = await agent.create_session(db=db, library_id="main_lib")

        assistant_msg = await agent.send_message(
            db=db,
            library_path=tmp_path,
            session_id=session.id,
            user_prompt="How do I bake sourdough bread?",
        )

        assert assistant_msg.role == "assistant"
        assert "could not find information" in assistant_msg.content.lower()
        assert len(assistant_msg.citations) == 0
