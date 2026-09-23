"""FastAPI router for Multi-Book Document Synthesis Studio and Research Briefs."""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import aiosqlite
import litellm
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.synthesis import (
    SynthesisDocument,
    SynthesisJobStatus,
    SynthesisSource,
)
from backend.providers.embedding_provider import (
    BaseEmbeddingProvider,
    GeminiEmbeddingProvider,
    MockEmbeddingProvider,
)
from backend.providers.llm_adapter import LiteLLMClientAdapter
from backend.services.document_synthesis_service import DocumentSynthesisService
from backend.services.library_manager import LibraryManager
from backend.services.rag_search import RAGSearchService
from backend.services.synthesis_exporter import SynthesisExporter

router = APIRouter(prefix="/api/synthesis", tags=["Document Synthesis Studio"])

# In-memory background jobs registry
SYNTHESIS_JOBS: dict[str, SynthesisJobStatus] = {}


class GenerateSynthesisRequest(BaseModel):
    """Payload to trigger multi-book document synthesis."""

    title: str
    topic_prompt: str
    template_type: Literal[
        "topic_brief", "literature_review", "executive_summary", "custom_research"
    ] = "topic_brief"
    book_ids: list[int] | None = None
    library_id: str | None = None
    wait: bool = False


def _get_embedding_provider() -> BaseEmbeddingProvider:
    cfg = ConfigManager()
    gemini_key = cfg.get_gemini_api_key() or os.environ.get("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("fake"):
        return GeminiEmbeddingProvider(api_key=gemini_key)
    return MockEmbeddingProvider(dimension=768)


async def _default_llm_call(prompt: str, system_instruction: str) -> str:
    adapter = LiteLLMClientAdapter()
    try:
        return await adapter.generate_response(prompt=prompt, system_instruction=system_instruction)
    except Exception as e:
        return f"I could not generate a response from the model at this time ({e})."



async def _resolve_library(library_id: str | None = None) -> tuple[str, Path]:
    cfg_mgr = ConfigManager()
    lib_mgr = LibraryManager()
    libraries = lib_mgr.list_libraries()
    if not libraries:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No libraries found in workspace",
        )

    if library_id:
        matching = next((lib for lib in libraries if lib.id == library_id), None)
        if not matching:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Library {library_id} not found",
            )
        return matching.id, Path(matching.path)

    active_lib = cfg_mgr.get_active_library()
    if active_lib:
        return active_lib.id, Path(active_lib.path)

    first = libraries[0]
    return first.id, Path(first.path)


async def _run_async_synthesis(
    job_id: str,
    library_path: Path,
    library_id: str,
    request: GenerateSynthesisRequest,
) -> None:
    job = SYNTHESIS_JOBS[job_id]
    job.status = "running"
    job.stage = "outline_generation"
    job.percent_complete = 15

    async def progress_cb(stg: str, pct: int) -> None:
        job.stage = stg
        job.percent_complete = pct

    try:
        provider = _get_embedding_provider()
        search_svc = RAGSearchService(embedding_provider=provider)
        synthesis_svc = DocumentSynthesisService(
            search_service=search_svc,
            llm_caller=_default_llm_call,
        )

        db_path = library_path / "metadata.db"
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            doc = await synthesis_svc.generate_document(
                db=db,
                library_path=library_path,
                library_id=library_id,
                title=request.title,
                topic_prompt=request.topic_prompt,
                template_type=request.template_type,
                book_ids=request.book_ids,
                progress_callback=progress_cb,
            )

        job.status = "completed"
        job.stage = "completed"
        job.percent_complete = 100
        job.document_id = doc.id
    except Exception as exc:
        job.status = "failed"
        job.stage = "failed"
        job.error = str(exc)


@router.post(
    "/generate",
    response_model=SynthesisDocument | SynthesisJobStatus,
    summary="Trigger multi-book document synthesis",
)
async def generate_synthesis(
    request: GenerateSynthesisRequest,
    background_tasks: BackgroundTasks,
):
    """Generates a grounded research brief synchronously (wait=true) or enqueues a job."""
    lib_id, lib_path = await _resolve_library(request.library_id)

    if request.wait:
        provider = _get_embedding_provider()
        search_svc = RAGSearchService(embedding_provider=provider)
        synthesis_svc = DocumentSynthesisService(
            search_service=search_svc,
            llm_caller=_default_llm_call,
        )

        db_path = lib_path / "metadata.db"
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            doc = await synthesis_svc.generate_document(
                db=db,
                library_path=lib_path,
                library_id=lib_id,
                title=request.title,
                topic_prompt=request.topic_prompt,
                template_type=request.template_type,
                book_ids=request.book_ids,
            )
            return doc

    job_id = f"job-syn-{uuid.uuid4().hex[:8]}"
    job_status = SynthesisJobStatus(
        job_id=job_id,
        status="queued",
        stage="queued",
        percent_complete=0,
    )
    SYNTHESIS_JOBS[job_id] = job_status
    background_tasks.add_task(
        _run_async_synthesis,
        job_id=job_id,
        library_path=lib_path,
        library_id=lib_id,
        request=request,
    )
    return Response(
        content=job_status.model_dump_json(),
        status_code=status.HTTP_202_ACCEPTED,
        media_type="application/json",
    )


@router.get(
    "/jobs/{job_id}",
    response_model=SynthesisJobStatus,
    summary="Poll status and progress of a synthesis job",
)
async def get_synthesis_job(job_id: str):
    """Retrieves progress information for an asynchronous synthesis job."""
    job = SYNTHESIS_JOBS.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Synthesis job {job_id} not found",
        )
    return job


@router.get(
    "/documents",
    response_model=list[SynthesisDocument],
    summary="List all synthesized research documents in library",
)
async def list_synthesis_documents(
    library_id: str | None = Query(None, description="Optional library ID filter"),
):
    """Lists all synthesized documents in the active library."""
    lib_id, lib_path = await _resolve_library(library_id)
    db_path = lib_path / "metadata.db"

    docs: list[SynthesisDocument] = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, library_id, title, template_type, topic_prompt,
                   outline_json, content_markdown, sources_json, word_count, created_at, updated_at
            FROM x_synthesis_documents
            ORDER BY created_at DESC
            """
        ) as cur:
            rows = await cur.fetchall()
            for r in rows:
                outline = json.loads(r["outline_json"]) if r["outline_json"] else []
                sources_raw = json.loads(r["sources_json"]) if r["sources_json"] else []
                sources = [SynthesisSource(**s) for s in sources_raw]

                created_dt = (
                    datetime.fromisoformat(r["created_at"])
                    if isinstance(r["created_at"], str)
                    else datetime.now(timezone.utc)
                )
                updated_dt = (
                    datetime.fromisoformat(r["updated_at"])
                    if isinstance(r["updated_at"], str)
                    else datetime.now(timezone.utc)
                )

                docs.append(
                    SynthesisDocument(
                        id=r["id"],
                        library_id=r["library_id"],
                        title=r["title"],
                        template_type=r["template_type"],
                        topic_prompt=r["topic_prompt"],
                        outline=outline,
                        content_markdown=r["content_markdown"],
                        sources=sources,
                        word_count=r["word_count"],
                        created_at=created_dt,
                        updated_at=updated_dt,
                    )
                )

    return docs


@router.get(
    "/documents/{document_id}",
    response_model=SynthesisDocument,
    summary="Retrieve a full synthesized research document",
)
async def get_synthesis_document(
    document_id: str,
    library_id: str | None = Query(None),
):
    """Fetches details and full markdown content for a single synthesized brief."""
    _, lib_path = await _resolve_library(library_id)
    db_path = lib_path / "metadata.db"

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT id, library_id, title, template_type, topic_prompt,
                   outline_json, content_markdown, sources_json, word_count, created_at, updated_at
            FROM x_synthesis_documents
            WHERE id = ?
            """,
            (document_id,),
        ) as cur:
            r = await cur.fetchone()
            if not r:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Synthesis document {document_id} not found",
                )

            outline = json.loads(r["outline_json"]) if r["outline_json"] else []
            sources_raw = json.loads(r["sources_json"]) if r["sources_json"] else []
            sources = [SynthesisSource(**s) for s in sources_raw]

            created_dt = (
                datetime.fromisoformat(r["created_at"])
                if isinstance(r["created_at"], str)
                else datetime.now(timezone.utc)
            )
            updated_dt = (
                datetime.fromisoformat(r["updated_at"])
                if isinstance(r["updated_at"], str)
                else datetime.now(timezone.utc)
            )

            return SynthesisDocument(
                id=r["id"],
                library_id=r["library_id"],
                title=r["title"],
                template_type=r["template_type"],
                topic_prompt=r["topic_prompt"],
                outline=outline,
                content_markdown=r["content_markdown"],
                sources=sources,
                word_count=r["word_count"],
                created_at=created_dt,
                updated_at=updated_dt,
            )


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a synthesized document",
)
async def delete_synthesis_document(
    document_id: str,
    library_id: str | None = Query(None),
):
    """Deletes a document from the database and removes cached filesystem exports."""
    _, lib_path = await _resolve_library(library_id)
    db_path = lib_path / "metadata.db"

    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM x_synthesis_documents WHERE id = ?", (document_id,))
        await db.commit()

    # Remove files from .synthesis directory if present
    synthesis_dir = lib_path / ".synthesis"
    if synthesis_dir.exists():
        for ext in (".md", ".html", ".json"):
            file_path = synthesis_dir / f"{document_id}{ext}"
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/documents/{document_id}/export",
    summary="Export document as Markdown, styled HTML, or JSON",
)
async def export_synthesis_document(
    document_id: str,
    format: Literal["markdown", "html", "json"] = Query(
        "markdown", description="Target export format"
    ),
    library_id: str | None = Query(None),
):
    """Exports synthesized document with formatted layout, citations, and headers."""
    doc = await get_synthesis_document(document_id=document_id, library_id=library_id)
    exporter = SynthesisExporter()

    if format == "html":
        content = exporter.to_html(doc)
        return Response(
            content=content,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'inline; filename="{doc.id}.html"'},
        )
    elif format == "json":
        content = exporter.to_json(doc)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{doc.id}.json"'},
        )
    else:
        content = exporter.to_markdown(doc)
        return Response(
            content=content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{doc.id}.md"'},
        )
