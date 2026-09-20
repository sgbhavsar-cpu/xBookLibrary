"""FastAPI router for AI classification, hierarchical taxonomies, and virtual bookshelves."""

from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.classification import Bookshelf, ClassificationResult, TaxonomyNode
from backend.domain.entities import Book
from backend.services.classification_service import ClassificationService
from backend.services.taxonomy_service import TaxonomyService

router = APIRouter(tags=["Classification & Taxonomies"])


class CreateTaxonomyRequest(BaseModel):
    name: str
    parent_id: Optional[int] = None
    description: Optional[str] = None


class CreateBookshelfRequest(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_smart: bool = False
    rule_expression: Optional[str] = None


class AddBooksToShelfRequest(BaseModel):
    book_ids: List[int]


def _get_active_library_path() -> Path:
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active library configured",
        )
    return Path(active_lib.path)


# --- Classification ---


@router.post("/api/books/{book_id}/classify", response_model=ClassificationResult)
async def classify_book(book_id: int):
    """Triggers dual-taxonomy (BISAC & DDC) AI classification for a book."""
    lib_path = _get_active_library_path()
    service = ClassificationService(lib_path)
    try:
        result = await service.classify_book(book_id=book_id)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification failed: {e}",
        )


# --- Custom Taxonomies ---


@router.get("/api/taxonomies", response_model=List[TaxonomyNode])
async def list_taxonomies():
    """Retrieves the custom category tree as a nested hierarchy."""
    try:
        lib_path = _get_active_library_path()
    except HTTPException:
        return []
    service = TaxonomyService(lib_path)
    return await service.get_taxonomy_tree()


@router.post(
    "/api/taxonomies",
    response_model=TaxonomyNode,
    status_code=status.HTTP_201_CREATED,
)
async def create_taxonomy(request: CreateTaxonomyRequest):
    """Creates a new category node in the custom taxonomy tree."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    try:
        node = await service.create_category(
            name=request.name,
            parent_id=request.parent_id,
            description=request.description,
        )
        return node
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create category: {e}",
        )


@router.delete(
    "/api/taxonomies/{taxonomy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_taxonomy(taxonomy_id: int):
    """Deletes a custom category and all its descendant subcategories."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    success = await service.delete_category(taxonomy_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Taxonomy node {taxonomy_id} not found",
        )
    return None


# --- Virtual Bookshelves ---


@router.get("/api/bookshelves", response_model=List[Bookshelf])
async def list_bookshelves():
    """Lists all virtual bookshelves in the active library."""
    try:
        lib_path = _get_active_library_path()
    except HTTPException:
        return []
    service = TaxonomyService(lib_path)
    return await service.list_bookshelves()


@router.post(
    "/api/bookshelves",
    response_model=Bookshelf,
    status_code=status.HTTP_201_CREATED,
)
async def create_bookshelf(request: CreateBookshelfRequest):
    """Creates a new virtual bookshelf."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    try:
        shelf = await service.create_bookshelf(
            name=request.name,
            description=request.description,
            icon=request.icon,
            is_smart=request.is_smart,
            rule_expression=request.rule_expression,
        )
        return shelf
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create bookshelf: {e}",
        )


@router.get("/api/bookshelves/{bookshelf_id}/books", response_model=List[Book])
async def get_bookshelf_books(bookshelf_id: int):
    """Retrieves all book records assigned to a bookshelf."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    return await service.get_books_on_shelf(bookshelf_id)


@router.post("/api/bookshelves/{bookshelf_id}/books")
async def add_books_to_shelf(bookshelf_id: int, request: AddBooksToShelfRequest):
    """Adds a list of book IDs to a virtual bookshelf."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    await service.add_books_to_shelf(bookshelf_id, request.book_ids)
    return {"status": "ok", "books_added": len(request.book_ids)}


@router.delete(
    "/api/bookshelves/{bookshelf_id}/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_book_from_shelf(bookshelf_id: int, book_id: int):
    """Removes a book from a virtual bookshelf."""
    lib_path = _get_active_library_path()
    service = TaxonomyService(lib_path)
    await service.remove_book_from_shelf(shelf_id=bookshelf_id, book_id=book_id)
    return None
