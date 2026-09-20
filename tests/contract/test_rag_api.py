from pathlib import Path
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_rag_api_contract_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies end-to-end RAG indexing, status, search, and chat sessions via REST API."""
    lib_dir = tmp_path / "RAGApiLib"
    lib_mgr = LibraryManager()
    lib_entry = await lib_mgr.create_new_library(lib_dir, name="RAG API Lib", set_active=True)
    lib_id = lib_entry.id

    epub_file = tmp_path / "quantum_computing.epub"
    create_sample_epub(epub_file, title="Quantum Computing Essentials", author="Richard F.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Ingest book
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("quantum_computing.epub", f, "application/epub+zip")},
            )
            assert upload_res.status_code == 202
            book = upload_res.json()[0]
            book_id = book["id"]

        # 1. POST single book index
        index_res = await client.post(f"/api/books/{book_id}/index")
        assert index_res.status_code == 200
        index_data = index_res.json()
        assert index_data["book_id"] == book_id
        assert index_data["status"] == "indexed"
        assert index_data["chunks_indexed"] > 0

        # 2. GET index status
        status_res = await client.get(f"/api/libraries/{lib_id}/index/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["total_books"] == 1
        assert status_data["indexed_books"] == 1
        assert status_data["total_chunks"] > 0

        # 3. POST hybrid search
        search_res = await client.post(
            f"/api/libraries/{lib_id}/search",
            json={"query": "quantum computing", "top_k": 3},
        )
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert len(search_data) > 0
        assert search_data[0]["book_id"] == book_id

        # 4. POST create chat session
        create_sess_res = await client.post(
            "/api/chat/sessions",
            json={"library_id": lib_id, "title": "Quantum Chat"},
        )
        assert create_sess_res.status_code == 201
        sess_data = create_sess_res.json()
        session_id = sess_data["id"]
        assert sess_data["title"] == "Quantum Chat"

        # 5. GET list sessions
        list_sess_res = await client.get(f"/api/chat/sessions?library_id={lib_id}")
        assert list_sess_res.status_code == 200
        assert len(list_sess_res.json()) >= 1

        # 6. POST message to chat session
        mock_llm_answer = (
            "Quantum computers leverage qubits and entanglement as described in "
            "[Quantum Computing Essentials, Chapter 1]."
        )
        with patch("backend.services.rag_chat_agent.RAGChatAgent.send_message") as mock_send:
            from datetime import datetime, timezone

            from backend.domain.rag import ChatMessage, Citation

            mock_send.return_value = ChatMessage(
                id="msg_asst",
                session_id=session_id,
                role="assistant",
                content=mock_llm_answer,
                citations=[
                    Citation(
                        book_id=book_id,
                        book_title="Quantum Computing Essentials",
                        authors="Richard F.",
                        chapter_index=0,
                        chapter_title="Chapter 1",
                        snippet="Quantum computing snippet",
                        score=0.92,
                    )
                ],
                created_at=datetime.now(timezone.utc),
            )

            msg_res = await client.post(
                f"/api/chat/sessions/{session_id}/messages",
                json={"content": "What is quantum computing?"},
            )
            assert msg_res.status_code == 200
            msg_data = msg_res.json()
            assert msg_data["role"] == "assistant"
            assert len(msg_data["citations"]) == 1

        # 7. GET chat session detail
        get_sess_res = await client.get(f"/api/chat/sessions/{session_id}")
        assert get_sess_res.status_code == 200
        assert get_sess_res.json()["id"] == session_id

        # 8. DELETE chat session
        del_res = await client.delete(f"/api/chat/sessions/{session_id}")
        assert del_res.status_code == 204
