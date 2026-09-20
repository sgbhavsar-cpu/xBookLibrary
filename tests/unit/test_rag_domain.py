from datetime import datetime, timezone

from backend.domain.rag import (
    ChatMessage,
    ChatSession,
    Citation,
    IndexStatus,
    SearchResult,
    VectorChunk,
)


def test_vector_chunk_domain_model():
    now = datetime.now(timezone.utc)
    chunk = VectorChunk(
        chunk_id="book_1_c0",
        book_id=1,
        library_id="default",
        book_title="Test Book",
        authors="Jane Doe",
        chapter_index=0,
        chapter_title="Chapter 1: Intro",
        content="This is a test content passage.",
        vector=[0.1] * 768,
        token_count=8,
        created_at=now,
    )
    assert chunk.chunk_id == "book_1_c0"
    assert chunk.book_id == 1
    assert chunk.token_count == 8
    assert len(chunk.vector) == 768


def test_citation_domain_model():
    cit = Citation(
        book_id=1,
        book_title="Test Book",
        authors="Jane Doe",
        chapter_index=0,
        chapter_title="Chapter 1: Intro",
        snippet="This is a test snippet...",
        score=0.92,
    )
    assert cit.score == 0.92
    assert cit.chapter_title == "Chapter 1: Intro"


def test_search_result_domain_model():
    res = SearchResult(
        chunk_id="book_1_c0",
        book_id=1,
        book_title="Test Book",
        authors="Jane Doe",
        chapter_index=0,
        chapter_title="Chapter 1: Intro",
        content="Full passage text here",
        score=0.88,
        match_type="hybrid",
    )
    assert res.match_type == "hybrid"
    assert res.score == 0.88


def test_chat_message_and_session_models():
    now = datetime.now(timezone.utc)
    msg_user = ChatMessage(
        id="msg_1",
        session_id="sess_1",
        role="user",
        content="What is the thesis of the book?",
        citations=[],
        created_at=now,
    )
    msg_asst = ChatMessage(
        id="msg_2",
        session_id="sess_1",
        role="assistant",
        content="The thesis is that...",
        citations=[
            Citation(
                book_id=1,
                book_title="Test Book",
                authors="Jane Doe",
                chapter_index=0,
                chapter_title="Chapter 1: Intro",
                snippet="Thesis statement snippet",
                score=0.95,
            )
        ],
        created_at=now,
    )

    session = ChatSession(
        id="sess_1",
        library_id="default",
        book_id=1,
        title="Researching Thesis",
        messages=[msg_user, msg_asst],
        created_at=now,
        updated_at=now,
    )

    assert len(session.messages) == 2
    assert session.messages[1].citations[0].chapter_title == "Chapter 1: Intro"


def test_index_status_model():
    now = datetime.now(timezone.utc)
    status = IndexStatus(
        total_books=20,
        indexed_books=15,
        pending_books=5,
        total_chunks=340,
        last_indexed_at=now,
    )
    assert status.total_books == 20
    assert status.pending_books == 5
    assert status.total_chunks == 340
