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
from backend.domain.metadata_editor import (
    BookDeleteResponse,
    BookMetadataUpdateRequest,
    BulkDeleteRequest,
    BulkDeleteResult,
    BulkMetadataUpdateRequest,
    BulkMetadataUpdateResult,
    FormatAddResponse,
    FormatDeleteResponse,
    OnlineMetadataCandidate,
    OnlineMetadataSearchRequest,
)
from backend.services.calibre_sync import CalibreSyncService
from backend.services.ingestion_service import IngestionService
from backend.services.metadata_editor_service import MetadataEditorService
from backend.services.online_metadata_service import OnlineMetadataService

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
    """Streams the cover.jpg file for the requested book,
    with optional dynamic thumbnail resizing.
    """
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

                from fastapi.responses import Response
                from PIL import Image

                w = width or 150
                h = height or 220
                with Image.open(cover_path) as img:
                    img = img.convert("RGB")
                    img.thumbnail((w, h), Image.Resampling.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    return Response(content=buf.getvalue(), media_type="image/jpeg")

            return FileResponse(cover_path, media_type="image/jpeg")


MIME_TYPES = {
    "PDF": "application/pdf",
    "EPUB": "application/epub+zip",
    "CBZ": "application/vnd.comicbook+zip",
    "CBR": "application/vnd.comicbook-rar",
    "M4B": "audio/mp4",
    "MP3": "audio/mpeg",
    "MOBI": "application/x-mobipocket-ebook",
    "AZW3": "application/vnd.amazon.ebook",
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "TXT": "text/plain",
}


@router.get("/{book_id}/download/{format_name}")
async def download_book_format(book_id: int, format_name: str):
    """Streams or downloads a specific book file format for reading or exporting."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    lib_path = Path(active_lib.path)
    db_path = lib_path / "metadata.db"
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Library database not found")

    fmt = format_name.split(".")[-1].upper()
    import aiosqlite

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT path, title FROM books WHERE id = ?", (book_id,)) as cur:
            book_row = await cur.fetchone()
            if not book_row:
                raise HTTPException(status_code=404, detail=f"Book with id {book_id} not found")

        async with db.execute(
            "SELECT name, format FROM data WHERE book = ? AND UPPER(format) = ?",
            (book_id, fmt),
        ) as cur:
            data_row = await cur.fetchone()
            if not data_row:
                raise HTTPException(
                    status_code=404,
                    detail=f"Format {fmt} not found for book {book_id}",
                )

        file_name = f"{data_row['name']}.{data_row['format'].lower()}"
        file_path = lib_path / book_row["path"] / file_name
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Book file '{file_name}' missing on disk",
            )

        media_type = MIME_TYPES.get(fmt, "application/octet-stream")
        safe_title = (
            "".join(c for c in book_row["title"] if c.isalnum() or c in " .-_").strip() or "book"
        )
        download_filename = f"{safe_title}.{data_row['format'].lower()}"

        return FileResponse(
            file_path,
            media_type=media_type,
            filename=download_filename,
            headers={
                "Content-Disposition": f'inline; filename="{download_filename}"',
                "Accept-Ranges": "bytes",
            },
        )


@router.post("/check-duplicate")
async def check_book_duplicate(file: UploadFile = File(...)):
    """Checks whether an uploaded file matches an existing book without importing it."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library configured")

    ingestion_service = IngestionService(Path(active_lib.path))
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / (file.filename or "upload.bin")
        with open(temp_file, "wb") as f:
            shutil.copyfileobj(file.file, f)
        await file.close()

        match = await ingestion_service.find_duplicate(temp_file)
        return {"duplicate": match is not None, "match": match}


@router.post("/upload", response_model=List[Book], status_code=status.HTTP_202_ACCEPTED)
async def upload_books(
    files: List[UploadFile] = File(...),
    conflict_action: str = Query("merge", pattern="^(merge|create_new|skip)$"),
):
    """Uploads one or more book files, parses them, and ingests them into the active library."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(
            status_code=400, detail="No active library configured to upload books into"
        )

    ingestion_service = IngestionService(Path(active_lib.path))
    ingested_books: List[Book] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        for upload in files:
            temp_file = temp_dir_path / (upload.filename or "upload.bin")
            with open(temp_file, "wb") as f:
                shutil.copyfileobj(upload.file, f)
            await upload.close()

            book = await ingestion_service.ingest_file(temp_file, conflict_action=conflict_action)
            ingested_books.append(book)

            # Trigger automated post-ingestion workflows (metadata, RAG, summary)
            import asyncio
            from backend.services.post_ingestion import trigger_post_ingestion_pipeline
            asyncio.create_task(
                trigger_post_ingestion_pipeline(
                    book_id=book.id,
                    library_path=Path(active_lib.path),
                    library_id=active_lib.id,
                )
            )

    return ingested_books


@router.put("/{book_id}/metadata", response_model=Book)
async def update_book_metadata(book_id: int, req: BookMetadataUpdateRequest):
    """Updates book metadata in Calibre SQLite and metadata.opf."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    try:
        return await service.update_book_metadata(book_id, req)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update metadata: {str(e)}")


@router.post("/{book_id}/cover", response_model=Book)
async def upload_book_cover(book_id: int, cover: UploadFile = File(...)):
    """Uploads and normalizes cover art to RGB JPEG, updating Calibre metadata."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    try:
        cover_bytes = await cover.read()
        await service.save_book_cover(book_id, cover_bytes)
        return await service.get_book_metadata(book_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save cover: {str(e)}")


@router.post("/{book_id}/online-metadata/query", response_model=List[OnlineMetadataCandidate])
async def query_online_metadata(book_id: int, req: Optional[OnlineMetadataSearchRequest] = None):
    """Searches external providers (Google Books, OpenLibrary) for candidate metadata."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    editor_service = MetadataEditorService(Path(active_lib.path))
    try:
        current_book = await editor_service.get_book_metadata(book_id)
    except Exception:
        current_book = None

    # Determine search parameters
    query_title = req.title if req and req.title else (current_book.title if current_book else None)
    query_author = (
        req.author
        if req and req.author
        else (current_book.authors[0] if current_book and current_book.authors else None)
    )
    query_isbn = req.isbn if req and req.isbn else (current_book.isbn if current_book else None)

    online_service = OnlineMetadataService()
    return await online_service.search_metadata(
        title=query_title,
        author=query_author,
        isbn=query_isbn,
        limit=10,
    )


@router.post(
    "/{book_id}/formats", response_model=FormatAddResponse, status_code=status.HTTP_201_CREATED
)
async def attach_book_format(book_id: int, file: UploadFile = File(...)):
    """Attaches an additional format file to an existing book record."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    filename = file.filename or "file.bin"
    file_bytes = await file.read()
    suffix = Path(filename).suffix.lstrip(".")
    if not suffix:
        raise HTTPException(status_code=400, detail="Uploaded file missing extension")

    format_name = suffix.upper()
    stem = Path(filename).stem

    service = MetadataEditorService(Path(active_lib.path))
    try:
        return await service.attach_format(
            book_id=book_id,
            format_name=format_name,
            filename_base=stem,
            file_bytes=file_bytes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to attach format: {str(e)}")


@router.delete("/{book_id}/formats/{format_name}", response_model=FormatDeleteResponse)
async def delete_book_format(book_id: int, format_name: str):
    """Deletes a specific format file from disk and the data table."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    try:
        return await service.delete_format(book_id, format_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete format: {str(e)}")


@router.post("/bulk-update", response_model=BulkMetadataUpdateResult)
async def bulk_update_books(req: BulkMetadataUpdateRequest):
    """Batch-updates tags, author, publisher, rating, or series across multiple books."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    return await service.bulk_update_books(req)


@router.delete("/{book_id}", response_model=BookDeleteResponse)
async def delete_book(book_id: int):
    """Completely deletes a book record, its files on disk, and vector embeddings."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    try:
        return await service.delete_book(book_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")


@router.post("/bulk-delete", response_model=BulkDeleteResult)
async def bulk_delete_books(req: BulkDeleteRequest):
    """Batch-deletes multiple books from library, filesystem, and vector index."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    service = MetadataEditorService(Path(active_lib.path))
    return await service.bulk_delete_books(req)

