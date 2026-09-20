import asyncio
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.config import ConfigManager
from backend.domain.conversion import ConversionJob, ConversionRequest
from backend.services.conversion_service import ConversionService

router = APIRouter(prefix="/api/convert", tags=["Format Conversion Engine"])

_conversion_services: dict = {}


def _get_conversion_service() -> ConversionService:
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    lib_path = Path(active_lib.path)
    lib_key = str(lib_path.resolve())
    if lib_key not in _conversion_services:
        _conversion_services[lib_key] = ConversionService(lib_path)
    return _conversion_services[lib_key]


@router.post("", response_model=ConversionJob, status_code=status.HTTP_202_ACCEPTED)
async def start_conversion_job(request: ConversionRequest):
    """Submits a format conversion job and begins background processing."""
    service = _get_conversion_service()
    try:
        job = await service.create_conversion_job(
            book_id=request.book_id,
            target_format=request.target_format,
            source_format=request.source_format,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Fire background task
    asyncio.create_task(service.execute_conversion_async(job.id))
    return job


@router.get("/jobs/{job_id}", response_model=ConversionJob)
async def get_conversion_job(job_id: str):
    """Retrieves conversion job status, progress percentage, and logs."""
    service = _get_conversion_service()
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Conversion job {job_id} not found")
    return job


@router.get("/jobs", response_model=List[ConversionJob])
async def list_conversion_jobs(book_id: Optional[int] = Query(None)):
    """Lists recent conversion jobs, optionally filtered by book."""
    service = _get_conversion_service()
    return service.list_jobs(book_id=book_id)
