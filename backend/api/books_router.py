"""FastAPI router for book queries, details, cover streaming, and file uploads."""

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.config import ConfigManager
from backend.domain.entities import Book
from backend.services.calibre_sync import CalibreSyncService
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/api/books", tags=["Books"])


class PaginatedBooksResponse(BaseModel):
    items: List[Book]
    page: int
    limit: int
    total: int


@router.get("", response_model=PaginatedBooksResponse)
async def list_books(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    query: Optional[str] = Query(None),
):
    """Query books from the currently active library."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        return PaginatedBooksResponse(items=[], page=page, limit=limit, total=0)

    sync_service = CalibreSyncService(Path(active_lib.path))
    books = await sync_service.get_books(page=page, limit=limit, query=query)
    total = await sync_service.get_book_count()
    return PaginatedBooksResponse(items=books, page=page, limit=limit, total=total)


@router.get("/{book_id}", response_model=Book)
async def get_book_detail(book_id: int):
    """Retrieve detailed book record with formats, authors, and TOC."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    ingestion_service = IngestionService(Path(active_lib.path))
    import aiosqlite

    async with aiosqlite.connect(ingestion_service.db_path) as db:
        db.row_factory = aiosqlite.Row
        try:
            return await ingestion_service._get_book_by_id(db, book_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")


@router.get("/{book_id}/cover")
async def get_book_cover(
    book_id: int,
    width: Optional[int] = Query(None, ge=16, le=2000),
    height: Optional[int] = Query(None, ge=16, le=2000),
):
    """Streams the cover.jpg file for the requested book, with optional dynamic thumbnail resizing."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    ingestion_service = IngestionService(Path(active_lib.path))
    import aiosqlite

    async with aiosqlite.connect(ingestion_service.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT path, has_cover FROM books WHERE id = ?", (book_id,)) as cur:
            row = await cur.fetchone()
            if not row or not row["has_cover"]:
                raise HTTPException(status_code=404, detail="Cover not found for book")
            cover_path = Path(active_lib.path) / row["path"] / "cover.jpg"
            if not cover_path.exists():
                raise HTTPException(status_code=404, detail="Cover file missing on disk")

            if width or height:
                import io
                from PIL import Image
                from fastapi.responses import Response

                w = width or 150
                h = height or 220
                with Image.open(cover_path) as img:
                    img = img.convert("RGB")
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    return Response(content=buf.getvalue(), media_type="image/jpeg")

            return FileResponse(cover_path, media_type="image/jpeg")


@router.post("/upload", response_model=List[Book], status_code=status.HTTP_202_ACCEPTED)
async def upload_books(files: List[UploadFile] = File(...)):
    """Uploads one or more book files, parses them, and ingests them into the active library."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library configured to upload books into")

    ingestion_service = IngestionService(Path(active_lib.path))
    ingested_books: List[Book] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        for upload in files:
            temp_file = temp_dir_path / (upload.filename or "upload.bin")
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            await upload.close()

            book = await ingestion_service.ingest_file(temp_file)
            ingested_books.append(book)

    return ingested_books
