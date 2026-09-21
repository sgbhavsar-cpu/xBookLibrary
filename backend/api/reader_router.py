from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.domain.reading import (
    Annotation,
    AnnotationCreateRequest,
    Bookmark,
    BookmarkCreateRequest,
    ComicManifest,
    ReadingProgress,
    ReadingProgressCreateRequest,
)
from backend.services.comic_service import ComicService
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService

router = APIRouter(tags=["Reader & Progress Sync"])


def get_library_manager() -> LibraryManager:
    return LibraryManager()


def get_reading_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> ReadingService:
    return ReadingService(library_manager=lib_mgr)


def get_comic_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> ComicService:
    return ComicService(library_manager=lib_mgr)


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/progress",
    response_model=Optional[ReadingProgress],
    summary="Get reading progress for a book",
)
async def get_reading_progress(
    library_id: str,
    book_id: int,
    format: Optional[str] = Query(None, description="Book format filter e.g. EPUB, PDF, CBZ"),
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.get_progress(library_id, book_id, format_name=format)


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/progress",
    response_model=ReadingProgress,
    summary="Save reading progress and sync Calibre #read_status",
)
async def save_reading_progress(
    library_id: str,
    book_id: int,
    req: ReadingProgressCreateRequest,
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.save_progress(library_id, book_id, req)


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/annotations",
    response_model=List[Annotation],
    summary="List all highlights and notes for a book",
)
async def list_annotations(
    library_id: str,
    book_id: int,
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.list_annotations(library_id, book_id)


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/annotations",
    response_model=Annotation,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new highlight or note",
)
async def create_annotation(
    library_id: str,
    book_id: int,
    req: AnnotationCreateRequest,
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.create_annotation(library_id, book_id, req)


@router.delete(
    "/api/libraries/{library_id}/books/{book_id}/annotations/{annotation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an annotation",
)
async def delete_annotation(
    library_id: str,
    book_id: int,
    annotation_id: str,
    reading_service: ReadingService = Depends(get_reading_service),
):
    success = await reading_service.delete_annotation(library_id, annotation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Annotation not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/annotations/export",
    summary="Export annotations to Markdown",
)
async def export_annotations_markdown(
    library_id: str,
    book_id: int,
    reading_service: ReadingService = Depends(get_reading_service),
):
    md_content = await reading_service.export_annotations_markdown(library_id, book_id)
    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="notes_book_{book_id}.md"'
        },
    )


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/bookmarks",
    response_model=List[Bookmark],
    summary="List all bookmarks for a book",
)
async def list_bookmarks(
    library_id: str,
    book_id: int,
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.list_bookmarks(library_id, book_id)


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/bookmarks",
    response_model=Bookmark,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new bookmark",
)
async def create_bookmark(
    library_id: str,
    book_id: int,
    req: BookmarkCreateRequest,
    reading_service: ReadingService = Depends(get_reading_service),
):
    return await reading_service.create_bookmark(library_id, book_id, req)


@router.delete(
    "/api/libraries/{library_id}/books/{book_id}/bookmarks/{bookmark_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a bookmark",
)
async def delete_bookmark(
    library_id: str,
    book_id: int,
    bookmark_id: str,
    reading_service: ReadingService = Depends(get_reading_service),
):
    success = await reading_service.delete_bookmark(library_id, bookmark_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/comic/manifest",
    response_model=ComicManifest,
    summary="Get comic/manga page manifest and metadata",
)
async def get_comic_manifest(
    library_id: str,
    book_id: int,
    comic_service: ComicService = Depends(get_comic_service),
):
    manifest = comic_service.get_manifest(library_id, book_id)
    return manifest


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/comic/pages/{page_index}",
    summary="Stream an extracted page image from a comic archive",
)
async def get_comic_page_image(
    library_id: str,
    book_id: int,
    page_index: int,
    comic_service: ComicService = Depends(get_comic_service),
):
    result = comic_service.get_page_image(library_id, book_id, page_index)
    if not result:
        raise HTTPException(status_code=404, detail="Page not found or invalid index")
    img_bytes, mime_type = result
    return Response(
        content=img_bytes,
        media_type=mime_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
