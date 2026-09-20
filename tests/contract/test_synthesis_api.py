"""Contract tests for Multi-Book Document Synthesis Studio REST API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.rag import SearchResult
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
async def test_synthesis_api_contract_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies end-to-end synthesis generation, job tracking, document retrieval, and export."""
    lib_dir = tmp_path / "SynthesisApiLib"
    lib_mgr = LibraryManager()
    lib_entry = await lib_mgr.create_new_library(lib_dir, name="Synthesis Lib", set_active=True)
    lib_id = lib_entry.id

    # Ingest a sample book so library has content
    epub_file = tmp_path / "ai_agents.epub"
    create_sample_epub(epub_file, title="Autonomous AI Agents", author="Alan Turing")

    # Mock RAG search results so we don't need real LanceDB embeddings
    mock_results = [
        SearchResult(
            chunk_id="chk-1",
            book_id=1,
            book_title="Autonomous AI Agents",
            authors="Alan Turing",
            chapter_title="Chapter 1: Agentic Architectures",
            chapter_index=0,
            content="Agentic architectures rely on perception, planning, action loops.",
            score=0.92,
        ),
        SearchResult(
            chunk_id="chk-2",
            book_id=1,
            book_title="Autonomous AI Agents",
            authors="Alan Turing",
            chapter_title="Chapter 2: Multi-Agent Systems",
            chapter_index=1,
            content="Multi-agent collaboration coordinates specialized domain subagents.",
            score=0.88,
        ),
    ]

    async def fake_llm(prompt: str, sys: str) -> str:
        if "outline" in sys.lower() or "outline" in prompt.lower():
            return """# Proposed Outline:
## 1. Architectural Foundations
Query: agentic perception planning action loops

## 2. Multi-Agent Collaboration
Query: multi-agent coordination specialization
"""
        elif "executive summary" in prompt.lower():
            return "This brief analyzes autonomous AI systems and team structures."
        else:
            return (
                "Agentic architectures demonstrate significant capabilities in reasoning. "
                "Perception loops guide reactive behaviors [Autonomous AI Agents, "
                "Chapter 1: Agentic Architectures], while multi-agent coordination establishes "
                "distributed problem solving "
                "[Autonomous AI Agents, Chapter 2: Multi-Agent Systems]."
            )

    with (
        patch(
            "backend.services.rag_search.RAGSearchService.search", new_callable=AsyncMock
        ) as mock_search,
        patch("backend.api.synthesis_router._default_llm_call", side_effect=fake_llm),
    ):
        mock_search.return_value = mock_results

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 1. Ingest book
            with open(epub_file, "rb") as f:
                upload_res = await client.post(
                    "/api/books/upload",
                    files={"files": ("ai_agents.epub", f, "application/epub+zip")},
                )
                assert upload_res.status_code == 202

            # 2. Synchronous synthesis generation (wait=true)
            gen_res = await client.post(
                "/api/synthesis/generate",
                json={
                    "title": "State of Autonomous AI Agents",
                    "topic_prompt": "Analyze autonomous agent architectures and coordination",
                    "template_type": "topic_brief",
                    "wait": True,
                },
            )
            assert gen_res.status_code == 200
            doc = gen_res.json()
            doc_id = doc["id"]
            assert doc["title"] == "State of Autonomous AI Agents"
            assert doc["library_id"] == lib_id
            assert len(doc["outline"]) > 0
            assert "content_markdown" in doc
            assert len(doc["sources"]) > 0

            # 3. List documents in library
            list_res = await client.get("/api/synthesis/documents")
            assert list_res.status_code == 200
            docs = list_res.json()
            assert any(d["id"] == doc_id for d in docs)

            # 4. Get specific document
            get_res = await client.get(f"/api/synthesis/documents/{doc_id}")
            assert get_res.status_code == 200
            assert get_res.json()["id"] == doc_id

            # 5. Export document as Markdown
            exp_md = await client.get(f"/api/synthesis/documents/{doc_id}/export?format=markdown")
            assert exp_md.status_code == 200
            assert "text/markdown" in exp_md.headers["content-type"]
            assert "# State of Autonomous AI Agents" in exp_md.text

            # 6. Export document as HTML
            exp_html = await client.get(f"/api/synthesis/documents/{doc_id}/export?format=html")
            assert exp_html.status_code == 200
            assert "text/html" in exp_html.headers["content-type"]
            assert "<!DOCTYPE html>" in exp_html.text

            # 7. Export document as JSON
            exp_json = await client.get(f"/api/synthesis/documents/{doc_id}/export?format=json")
            assert exp_json.status_code == 200
            assert "application/json" in exp_json.headers["content-type"]
            assert exp_json.json()["id"] == doc_id

            # 8. Asynchronous synthesis generation (wait=false)
            async_res = await client.post(
                "/api/synthesis/generate",
                json={
                    "title": "Async Agent Study",
                    "topic_prompt": "Fast overview of agents",
                    "template_type": "executive_summary",
                    "wait": False,
                },
            )
            assert async_res.status_code == 202
            job = async_res.json()
            assert "job_id" in job
            assert job["status"] in ("queued", "running", "completed")

            # 9. Poll job status
            job_id = job["job_id"]
            job_res = await client.get(f"/api/synthesis/jobs/{job_id}")
            assert job_res.status_code == 200
            assert job_res.json()["job_id"] == job_id

            # 10. Delete document
            del_res = await client.delete(f"/api/synthesis/documents/{doc_id}")
            assert del_res.status_code == 204

            # Verify 404 after deletion
            get_del_res = await client.get(f"/api/synthesis/documents/{doc_id}")
            assert get_del_res.status_code == 404
