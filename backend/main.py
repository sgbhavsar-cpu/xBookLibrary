"""xBookLibrary Core FastAPI Application.

Serves REST endpoints for library management, multi-format book ingestion,
catalog queries, cover streaming, and health checks.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.books_router import router as books_router
from backend.api.jobs_router import router as jobs_router
from backend.api.libraries_router import router as libraries_router
from backend.api.proposals_router import router as proposals_router
from backend.api.summaries_router import router as summaries_router
from backend.api.taxonomies_router import router as taxonomies_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    yield


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


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for system readiness."""
    return {"status": "ok", "service": "xBookLibrary"}
