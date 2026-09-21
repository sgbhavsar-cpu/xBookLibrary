"""FastAPI router for KOReader Kosync wireless progress synchronization."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.domain.devices import KosyncProgress
from backend.services.kosync_service import KosyncService
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService

router = APIRouter(prefix="/api/sync/koreader", tags=["KOReader Kosync"])


def get_kosync_service() -> KosyncService:
    lib_mgr = LibraryManager()
    reading_svc = ReadingService(lib_mgr)
    return KosyncService(library_manager=lib_mgr, reading_service=reading_svc)


class UserCredentials(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    auth: bool
    user: str


class CreateUserResponse(BaseModel):
    created: bool
    username: str


@router.post("/users/create", response_model=CreateUserResponse, status_code=status.HTTP_201_CREATED)
async def kosync_create_user(creds: UserCredentials):
    return CreateUserResponse(created=True, username=creds.username)


@router.post("/users/auth", response_model=AuthResponse)
async def kosync_auth(creds: UserCredentials):
    return AuthResponse(auth=True, user=creds.username)


class ProgressSyncAck(BaseModel):
    document: str
    timestamp: int


@router.put("/syncs/progress", response_model=ProgressSyncAck)
async def kosync_push_progress(
    prog: KosyncProgress,
    kosync_service: KosyncService = Depends(get_kosync_service),
):
    await kosync_service.save_progress(prog)
    return ProgressSyncAck(document=prog.document, timestamp=prog.timestamp)


@router.get("/syncs/progress/{document_hash}", response_model=KosyncProgress)
async def kosync_get_progress(
    document_hash: str,
    kosync_service: KosyncService = Depends(get_kosync_service),
):
    prog = await kosync_service.get_progress(document_hash)
    if not prog:
        raise HTTPException(status_code=404, detail="No progress found for document hash.")
    return prog
