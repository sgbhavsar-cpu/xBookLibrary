"""FastAPI router for multi-resolution book summaries, exports, and Calibre sync."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.summary import BookSummary
from backend.services.summarization_service import SummarizationService
from backend.services.summary_exporter import SummaryExporter

router = APIRouter(prefix="/api/books", tags=["Summaries"])


class GenerateSummaryRequest(BaseModel):
    custom_instructions: Optional[str] = None
    force_regenerate: bool = False


def _get_active_library_path() -> Path:
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active library configured",
        )
    return Path(active_lib.path)


@router.get("/{book_id}/summary", response_model=BookSummary)
async def get_book_summary(book_id: int):
    """Retrieves cached multi-resolution summary for a book."""
    lib_path = _get_active_library_path()
    service = SummarizationService(lib_path)
    summary = await service.get_summary(book_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for book {book_id} not found",
        )
    return summary


@router.post("/{book_id}/summary", response_model=BookSummary)
@router.post("/{book_id}/summary/generate", response_model=BookSummary)
async def generate_book_summary(
    book_id: int,
    request: Optional[GenerateSummaryRequest] = None,
):
    """Generates or regenerates a multi-resolution summary for a book."""
    lib_path = _get_active_library_path()
    service = SummarizationService(lib_path)

    instructions = request.custom_instructions if request else None
    force = request.force_regenerate if request else False

    try:
        summary = await service.summarize_book(
            book_id=book_id,
            custom_instructions=instructions,
            force_regenerate=force,
        )
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {e}",
        )


@router.get("/{book_id}/summary/export")
async def export_book_summary(
    book_id: int,
    format: str = Query("markdown", pattern="^(markdown|html|json)$"),
):
    """Exports summary in Markdown, styled HTML, or JSON format."""
    lib_path = _get_active_library_path()
    service = SummarizationService(lib_path)
    summary = await service.get_summary(book_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for book {book_id} not found",
        )

    book_info = await service._get_book_record(book_id)
    title = book_info["title"] if book_info else f"Book {book_id}"
    authors = book_info["authors"] if book_info else []

    exporter = SummaryExporter(lib_path)

    if format == "html":
        content = exporter.export_html(summary, book_title=title, authors=authors)
        return Response(content=content, media_type="text/html; charset=utf-8")
    elif format == "json":
        return Response(
            content=summary.model_dump_json(indent=2),
            media_type="application/json; charset=utf-8",
        )
    else:
        content = exporter.export_markdown(summary, book_title=title, authors=authors)
        return Response(content=content, media_type="text/markdown; charset=utf-8")


@router.post("/{book_id}/summary/sync-calibre")
async def sync_summary_to_calibre(book_id: int):
    """Synchronizes executive summary into Calibre comments table and metadata.opf."""
    lib_path = _get_active_library_path()
    service = SummarizationService(lib_path)
    summary = await service.get_summary(book_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Summary for book {book_id} not found",
        )

    exporter = SummaryExporter(lib_path)
    synced = await exporter.sync_to_calibre_metadata(book_id=book_id, summary=summary)
    return {"status": "ok", "synced": synced}
