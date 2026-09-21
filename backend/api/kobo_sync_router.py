"""FastAPI router for Kobo Store Sync API v1 compatibility."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.domain.devices import KoboStateUpdateRequest, KoboSyncResponse
from backend.services.kobo_sync_service import KoboSyncService
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService

router = APIRouter(tags=["Kobo Wireless Sync"])


def get_kobo_sync_service() -> KoboSyncService:
    lib_mgr = LibraryManager()
    reading_svc = ReadingService(lib_mgr)
    return KoboSyncService(library_manager=lib_mgr, reading_service=reading_svc)


@router.get(
    "/api/sync/kobo/{auth_token}/v1/user/profile",
    summary="Kobo sync user profile endpoint",
)
async def get_kobo_user_profile(
    auth_token: str,
    kobo_service: KoboSyncService = Depends(get_kobo_sync_service),
):
    try:
        return await kobo_service.get_user_profile(auth_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get(
    "/api/sync/kobo/{auth_token}/v1/library/sync",
    response_model=KoboSyncResponse,
    summary="Kobo library delta sync endpoint",
)
async def get_kobo_library_sync(
    auth_token: str,
    kobo_service: KoboSyncService = Depends(get_kobo_sync_service),
):
    try:
        return await kobo_service.sync_library(auth_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


class StateUpdateResponse(BaseModel):
    success: bool


@router.put(
    "/api/sync/kobo/{auth_token}/v1/library/{book_id}/state",
    response_model=StateUpdateResponse,
    summary="Kobo reading progress sync state update",
)
async def update_kobo_reading_state(
    auth_token: str,
    book_id: int,
    req: KoboStateUpdateRequest,
    kobo_service: KoboSyncService = Depends(get_kobo_sync_service),
):
    try:
        success = await kobo_service.update_reading_state(
            auth_token=auth_token,
            book_id=book_id,
            progress_percent=req.ProgressPercent,
            last_read=req.LastRead,
        )
        return StateUpdateResponse(success=success)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/api/sync/kobo/{auth_token}/v1/books/{book_id}/file",
    summary="Download book binary for Kobo e-reader",
)
async def download_kobo_book_file(
    auth_token: str,
    book_id: int,
    kobo_service: KoboSyncService = Depends(get_kobo_sync_service),
):
    try:
        file_path, media_type, fname = await kobo_service.get_book_file(auth_token, book_id)
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=fname,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
