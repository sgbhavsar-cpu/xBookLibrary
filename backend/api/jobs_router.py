"""FastAPI router for background ingestion job queries."""

from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.config import ConfigManager
from backend.domain.entities import IngestionJob
from backend.services.job_worker import JobManager

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("", response_model=List[IngestionJob])
async def list_jobs(limit: int = Query(50, ge=1, le=500)):
    """List recent ingestion jobs from the active library."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        return []

    mgr = JobManager(Path(active_lib.path) / "metadata.db")
    return await mgr.list_jobs(limit=limit)


@router.get("/{job_id}", response_model=IngestionJob)
async def get_job(job_id: str):
    """Retrieve details and status for a specific ingestion job."""
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")

    mgr = JobManager(Path(active_lib.path) / "metadata.db")
    job = await mgr.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job
