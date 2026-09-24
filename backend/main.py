"""xBookLibrary Core FastAPI Application.

Serves REST endpoints for library management, multi-format book ingestion,
catalog queries, cover streaming, and health checks.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.audiobooks_router import router as audiobooks_router
from backend.api.books_router import router as books_router
from backend.api.conversion_router import router as conversion_router
from backend.api.custom_columns_router import router as custom_columns_router
from backend.api.devices_router import router as devices_router
from backend.api.jobs_router import router as jobs_router
from backend.api.kobo_sync_router import router as kobo_sync_router
from backend.api.kosync_router import router as kosync_router
from backend.api.libraries_router import router as libraries_router
from backend.api.opds_router import router as opds_router
from backend.api.preferences_router import router as preferences_router
from backend.api.proposals_router import router as proposals_router
from backend.api.rag_router import router as rag_router
from backend.api.reader_router import router as reader_router
from backend.api.summaries_router import router as summaries_router
from backend.api.synthesis_router import router as synthesis_router
from backend.api.taxonomies_router import router as taxonomies_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    import logging
    from backend.services.watcher_manager import drop_folder_watcher_manager
    try:
        await drop_folder_watcher_manager.sync_with_config()
    except Exception as e:
        logging.getLogger(__name__).error("Failed to start drop folder watcher on startup: %s", e)
    yield
    try:
        await drop_folder_watcher_manager.stop()
    except Exception as e:
        logging.getLogger(__name__).error("Error stopping drop folder watcher on shutdown: %s", e)


app = FastAPI(
    title="xBookLibrary Core API",
    version="0.1.0",
    description="Calibre-compatible AI book library core backend.",
    lifespan=lifespan,
)

# CORS configuration for modern web clients (Vite / React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(libraries_router)
app.include_router(books_router)
app.include_router(jobs_router)
app.include_router(proposals_router)
app.include_router(taxonomies_router)
app.include_router(summaries_router)
app.include_router(rag_router)
app.include_router(synthesis_router)
app.include_router(opds_router)
app.include_router(conversion_router)
app.include_router(custom_columns_router)
app.include_router(reader_router)
app.include_router(devices_router)
app.include_router(kobo_sync_router)
app.include_router(kosync_router)
app.include_router(audiobooks_router)
app.include_router(preferences_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for system readiness."""
    return {"status": "ok", "service": "xBookLibrary"}


# Mount production frontend build if available
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

