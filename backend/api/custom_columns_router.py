from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.domain.custom_columns import (
    BookCustomValues,
    CustomColumnCreateRequest,
    CustomColumnDefinition,
    SeriesInfo,
    VirtualLibrary,
)
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager
from backend.services.series_service import SeriesService
from backend.services.virtual_library_service import VirtualLibraryService

router = APIRouter(tags=["Custom Columns & Series & Virtual Libraries"])


def get_library_manager() -> LibraryManager:
    return LibraryManager()


def get_custom_columns_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> CustomColumnsService:
    return CustomColumnsService(library_manager=lib_mgr)


def get_series_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> SeriesService:
    return SeriesService(library_manager=lib_mgr)


def get_virtual_library_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> VirtualLibraryService:
    return VirtualLibraryService(library_manager=lib_mgr)


# ---------------------------------------------------------
# Custom Columns
# ---------------------------------------------------------

@router.get(
    "/api/libraries/{library_id}/custom-columns",
    response_model=List[CustomColumnDefinition],
)
async def list_custom_columns(
    library_id: str,
    cc_service: CustomColumnsService = Depends(get_custom_columns_service),
):
    """Retrieve all defined custom columns for the library."""
    return await cc_service.get_custom_columns(library_id)


@router.post(
    "/api/libraries/{library_id}/custom-columns",
    response_model=CustomColumnDefinition,
    status_code=201,
)
async def create_custom_column(
    library_id: str,
    req: CustomColumnCreateRequest,
    cc_service: CustomColumnsService = Depends(get_custom_columns_service),
):
    """Create a new custom column and execute Calibre DDL."""
    try:
        return await cc_service.create_custom_column(library_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create custom column: {e}")


@router.post(
    "/api/libraries/{library_id}/custom-columns/presets",
    response_model=List[CustomColumnDefinition],
)
async def install_custom_column_presets(
    library_id: str,
    cc_service: CustomColumnsService = Depends(get_custom_columns_service),
):
    """Install standard Calibre custom columns (#read_status, #rating, #pages, #difficulty, #notes)."""
    return await cc_service.install_default_presets(library_id)


@router.get(
    "/api/books/{book_id}/custom-values",
    response_model=BookCustomValues,
)
async def get_book_custom_values(
    book_id: int,
    library_id: Optional[str] = Query(None),
    lib_mgr: LibraryManager = Depends(get_library_manager),
    cc_service: CustomColumnsService = Depends(get_custom_columns_service),
):
    """Fetch custom column values for a specific book."""
    active_lib = library_id or (lib_mgr.get_active_library().id if lib_mgr.get_active_library() else None)
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library found.")
    return await cc_service.get_book_custom_values(active_lib, book_id)


@router.put(
    "/api/books/{book_id}/custom-values",
    response_model=BookCustomValues,
)
async def update_book_custom_values(
    book_id: int,
    values: Dict[str, Any],
    library_id: Optional[str] = Query(None),
    lib_mgr: LibraryManager = Depends(get_library_manager),
    cc_service: CustomColumnsService = Depends(get_custom_columns_service),
):
    """Update custom column values for a book."""
    active_lib = library_id or (lib_mgr.get_active_library().id if lib_mgr.get_active_library() else None)
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library found.")
    return await cc_service.set_book_custom_values(active_lib, book_id, values)


# ---------------------------------------------------------
# Series & Universe Management
# ---------------------------------------------------------

class UpdateSeriesRequest(BaseModel):
    name: Optional[str] = None
    series_index: float = 1.0


@router.get(
    "/api/libraries/{library_id}/series",
    response_model=List[SeriesInfo],
)
async def list_series(
    library_id: str,
    series_svc: SeriesService = Depends(get_series_service),
):
    """List all series in the library with book counts."""
    return await series_svc.get_series_list(library_id)


@router.get(
    "/api/books/{book_id}/series",
    response_model=Optional[SeriesInfo],
)
async def get_book_series(
    book_id: int,
    library_id: Optional[str] = Query(None),
    lib_mgr: LibraryManager = Depends(get_library_manager),
    series_svc: SeriesService = Depends(get_series_service),
):
    """Get the series and volume index for a book."""
    active_lib = library_id or (lib_mgr.get_active_library().id if lib_mgr.get_active_library() else None)
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library found.")
    return await series_svc.get_book_series(active_lib, book_id)


@router.put(
    "/api/books/{book_id}/series",
    response_model=Optional[SeriesInfo],
)
async def update_book_series(
    book_id: int,
    req: UpdateSeriesRequest,
    library_id: Optional[str] = Query(None),
    lib_mgr: LibraryManager = Depends(get_library_manager),
    series_svc: SeriesService = Depends(get_series_service),
):
    """Set or remove series association and index for a book."""
    active_lib = library_id or (lib_mgr.get_active_library().id if lib_mgr.get_active_library() else None)
    if not active_lib:
        raise HTTPException(status_code=400, detail="No active library found.")
    return await series_svc.set_book_series(
        active_lib, book_id, series_name=req.name, series_index=req.series_index
    )


# ---------------------------------------------------------
# Virtual Libraries
# ---------------------------------------------------------

class CreateVirtualLibraryRequest(BaseModel):
    name: str
    query: str


@router.get(
    "/api/libraries/{library_id}/virtual-libraries",
    response_model=List[VirtualLibrary],
)
async def list_virtual_libraries(
    library_id: str,
    vl_svc: VirtualLibraryService = Depends(get_virtual_library_service),
):
    """List all virtual libraries saved in Calibre preferences."""
    return await vl_svc.get_virtual_libraries(library_id)


@router.post(
    "/api/libraries/{library_id}/virtual-libraries",
    response_model=VirtualLibrary,
)
async def create_virtual_library(
    library_id: str,
    req: CreateVirtualLibraryRequest,
    vl_svc: VirtualLibraryService = Depends(get_virtual_library_service),
):
    """Create or update a virtual library query in preferences."""
    try:
        return await vl_svc.save_virtual_library(library_id, req.name, req.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/api/libraries/{library_id}/virtual-libraries/{name}",
)
async def delete_virtual_library(
    library_id: str,
    name: str,
    vl_svc: VirtualLibraryService = Depends(get_virtual_library_service),
):
    """Delete a virtual library from Calibre preferences."""
    deleted = await vl_svc.delete_virtual_library(library_id, name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Virtual library '{name}' not found.")
    return {"message": f"Virtual library '{name}' deleted successfully."}
