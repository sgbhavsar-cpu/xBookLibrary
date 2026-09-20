"""Contract tests for multi-resolution book summarization REST API endpoints."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_sample_epub


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolates configuration directory to temporary path."""
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.mark.asyncio
async def test_summaries_api_contract_lifecycle(tmp_path: Path, isolated_env: Path):
    """Verifies generation, retrieval, export, and Calibre sync via REST API."""
    # 1. Setup library and ingest a book
    lib_dir = tmp_path / "SummaryAPILib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Summary API Lib", set_active=True)

    epub_file = tmp_path / "deep_learning.epub"
    create_sample_epub(epub_file, title="Deep Learning Systems", author="Ian G.")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Ingest book
        with open(epub_file, "rb") as f:
            upload_res = await client.post(
                "/api/books/upload",
                files={"files": ("deep_learning.epub", f, "application/epub+zip")},
            )
            assert upload_res.status_code == 202
            book = upload_res.json()[0]
            book_id = book["id"]

        # 2. GET summary before generation -> 404
        not_found_res = await client.get(f"/api/books/{book_id}/summary")
        assert not_found_res.status_code == 404

        # 3. POST summary generation
        mock_summary = {
            "executive_snapshot": {
                "hook": "A masterclass in modern deep representation learning.",
                "core_thesis": "Deep models learn representations directly from data.",
                "target_audience": "AI researchers and practitioners.",
                "key_arguments": [
                    "Backpropagation scales to billions of parameters.",
                    "Convolution and attention capture inductive spatial/temporal biases.",
                ],
                "estimated_reading_time_minutes": 320,
            },
            "chapters": [
                {
                    "chapter_index": 1,
                    "chapter_title": "Applied Math and Machine Learning Basics",
                    "summary": "Reviews linear algebra, probability, and numerical computation.",
                    "key_takeaways": [
                        "SVD and eigendecomposition decompose matrix transformations."
                    ],
                    "important_quotes": ["Probability theory is the logic of science."],
                }
            ],
            "conceptual_index": {
                "frameworks": ["Empirical Risk Minimization", "Deep Feedforward Networks"],
                "key_takeaways": [
                    "Stochastic gradient descent navigates non-convex loss surfaces."
                ],
                "quotable_moments": [
                    {"quote": "Probability theory is the logic of science.", "source": "Chapter 1"}
                ],
                "action_items": ["Implement mini-batch SGD with Adam optimizer."],
            },
        }

        with (
            patch(
                "backend.services.summarization_service.SummarizationService._call_chapter_summarizer",
                new_callable=AsyncMock,
                return_value={
                    "summary": "Reviews linear algebra, probability, and computation.",
                    "key_takeaways": ["SVD and eigendecomposition decompose matrices."],
                    "important_quotes": ["Probability theory is the logic of science."],
                },
            ),
            patch(
                "backend.services.summarization_service.SummarizationService._call_reduce_synthesizer",
                new_callable=AsyncMock,
                return_value={
                    "executive_snapshot": mock_summary["executive_snapshot"],
                    "conceptual_index": mock_summary["conceptual_index"],
                },
            ),
        ):
            gen_res = await client.post(
                f"/api/books/{book_id}/summary",
                json={"custom_instructions": "Focus on neural architectures"},
            )
            assert gen_res.status_code in (200, 202)
            summary_data = gen_res.json()
            assert summary_data["book_id"] == book_id
            assert summary_data["executive_snapshot"]["hook"].startswith("A masterclass")
            assert len(summary_data["chapters"]) >= 1

        # 4. GET summary after generation -> 200 from cache
        get_res = await client.get(f"/api/books/{book_id}/summary")
        assert get_res.status_code == 200
        cached = get_res.json()
        assert cached["executive_snapshot"]["hook"].startswith("A masterclass")

        # 5. GET export markdown
        export_md_res = await client.get(f"/api/books/{book_id}/summary/export?format=markdown")
        assert export_md_res.status_code == 200
        md_text = export_md_res.text
        assert "## Executive Snapshot" in md_text
        assert "A masterclass in modern deep representation learning." in md_text

        # 6. GET export HTML
        export_html_res = await client.get(f"/api/books/{book_id}/summary/export?format=html")
        assert export_html_res.status_code == 200
        assert "<!DOCTYPE html>" in export_html_res.text
        assert "A masterclass in modern deep representation learning." in export_html_res.text

        # 7. POST sync-calibre
        sync_res = await client.post(f"/api/books/{book_id}/summary/sync-calibre")
        assert sync_res.status_code == 200
        assert sync_res.json()["synced"] is True
