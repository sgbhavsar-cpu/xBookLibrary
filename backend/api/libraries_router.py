"""FastAPI router for library registration, adoption, and switching."""

from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.config import ConfigManager
from backend.domain.entities import Library
from backend.services.library_manager import LibraryManager

router = APIRouter(prefix="/api/libraries", tags=["Libraries"])


class CreateLibraryPayload(BaseModel):
    name: str
    path: str
    adopt_existing_calibre: bool = True
    set_active: bool = True


@router.get("", response_model=List[Library])
async def list_libraries():
    """Lists all registered libraries."""
    lib_mgr = LibraryManager()
    return lib_mgr.list_libraries()


@router.post("", response_model=Library, status_code=status.HTTP_201_CREATED)
async def create_or_adopt_library(payload: CreateLibraryPayload):
    """Creates a new library or adopts an existing Calibre directory."""
    lib_mgr = LibraryManager()
    lib_path = Path(payload.path)

    try:
        if payload.adopt_existing_calibre:
            return await lib_mgr.adopt_calibre_library(
                library_path=lib_path,
                name=payload.name,
                set_active=payload.set_active,
            )
        else:
            return await lib_mgr.create_new_library(
                library_path=lib_path,
                name=payload.name,
                set_active=payload.set_active,
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{library_id}/switch", response_model=Library)
async def switch_library(library_id: str):
    """Sets the active library."""
    lib_mgr = LibraryManager()
    try:
        return lib_mgr.switch_active_library(library_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
