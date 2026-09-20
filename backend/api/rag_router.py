"""FastAPI router for Library-Wise RAG vector indexing, hybrid search, and conversational QA."""

import os
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import aiosqlite
import litellm
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from pydantic import BaseModel

from backend.config import ConfigManager
from backend.domain.rag import ChatMessage, ChatSession, IndexStatus, SearchResult
from backend.providers.embedding_provider import (
    BaseEmbeddingProvider,
    GeminiEmbeddingProvider,
    MockEmbeddingProvider,
)
from backend.services.rag_chat_agent import RAGChatAgent
from backend.services.rag_indexer import RAGIndexer
from backend.services.rag_search import RAGSearchService


async def _default_llm_call(prompt: str, system_instruction: str) -> str:
    cfg_mgr = ConfigManager()
    gemini_key = cfg_mgr.get_gemini_api_key() or os.environ.get("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("fake"):
        model = "gemini/gemini-2.0-flash"
        kwargs: dict = {
            "model": model,
            "api_key": gemini_key,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    else:
        model = "ollama/llama3.2"
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
    try:
        res = await litellm.acompletion(**kwargs)
        return res.choices[0].message.content or ""
    except Exception:
        return "I could not generate a response from the model at this time."


router = APIRouter(prefix="/api", tags=["RAG & Conversational QA"])


class SearchRequest(BaseModel):
    query: str
    book_id: Optional[int] = None
    top_k: int = 5
    mode: Literal["hybrid", "vector", "keyword"] = "hybrid"


class CreateSessionRequest(BaseModel):
    library_id: str
    book_id: Optional[int] = None
    title: str = "New Chat"


class SendMessageRequest(BaseModel):
    content: str


def _get_embedding_provider() -> BaseEmbeddingProvider:
    """Instantiates the active embedding provider based on environment and config."""
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key and not gemini_key.startswith("fake"):
        return GeminiEmbeddingProvider(api_key=gemini_key)
    return MockEmbeddingProvider(dimension=768)


def _resolve_library_path(library_id: Optional[str] = None) -> tuple[str, Path]:
    cfg_mgr = ConfigManager()
    config = cfg_mgr.load()
    if library_id:
        lib = next((lib for lib in config.libraries if lib.id == library_id), None)
        if lib:
            return lib.id, Path(lib.path)
    active = cfg_mgr.get_active_library()
    if not active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active library configured",
        )
    return active.id, Path(active.path)


@router.post("/books/{book_id}/index")
async def index_single_book(book_id: int):
    """Indexes or re-indexes a single book into the library's LanceDB vector store."""
    lib_id, lib_path = _resolve_library_path()
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    indexer = RAGIndexer(embedding_provider=embedder)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        result = await indexer.index_book(
            book_id=book_id,
            library_id=lib_id,
            library_path=lib_path,
            db=db,
            force=True,
        )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Indexing error"),
        )
    return result


@router.post("/libraries/{library_id}/index", status_code=status.HTTP_202_ACCEPTED)
async def trigger_library_indexing(
    library_id: str,
    background_tasks: BackgroundTasks,
    force_reindex: bool = False,
):
    """Dispatches asynchronous bulk indexing across all books in a library."""
    lib_id, lib_path = _resolve_library_path(library_id)
    db_file = lib_path / "metadata.db"

    async def _run_batch_indexing():
        embedder = _get_embedding_provider()
        indexer = RAGIndexer(embedding_provider=embedder)
        async with aiosqlite.connect(str(db_file)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT id FROM books ORDER BY id ASC") as cursor:
                book_rows = await cursor.fetchall()
            for b in book_rows:
                try:
                    await indexer.index_book(
                        book_id=b["id"],
                        library_id=lib_id,
                        library_path=lib_path,
                        db=db,
                        force=force_reindex,
                    )
                except Exception:
                    continue

    background_tasks.add_task(_run_batch_indexing)
    return {
        "job_id": f"idx_{library_id}",
        "status": "queued",
        "message": f"Bulk indexing started for library {library_id}",
    }


@router.get("/libraries/{library_id}/index/status", response_model=IndexStatus)
async def get_library_index_status(library_id: str):
    """Retrieves indexing progress, health, and chunk volume statistics."""
    _, lib_path = _resolve_library_path(library_id)
    db_file = lib_path / "metadata.db"

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        # Total books
        async with db.execute("SELECT COUNT(*) as c FROM books") as cur:
            tot_row = await cur.fetchone()
            total_books = tot_row["c"] if tot_row else 0

        # Indexed stats
        async with db.execute(
            """SELECT COUNT(*) as indexed_cnt,
                      COALESCE(SUM(chunk_count), 0) as total_chunks,
                      MAX(indexed_at) as last_indexed
               FROM x_index_status WHERE status = 'indexed'"""
        ) as cur:
            idx_row = await cur.fetchone()
            indexed_books = idx_row["indexed_cnt"] if idx_row else 0
            total_chunks = idx_row["total_chunks"] if idx_row else 0
            raw_last = idx_row["last_indexed"] if idx_row else None

    last_dt = None
    if raw_last:
        try:
            last_dt = datetime.fromisoformat(raw_last) if isinstance(raw_last, str) else raw_last
        except Exception:
            last_dt = None

    return IndexStatus(
        total_books=total_books,
        indexed_books=indexed_books,
        pending_books=max(0, total_books - indexed_books),
        total_chunks=total_chunks,
        last_indexed_at=last_dt,
    )


@router.post("/libraries/{library_id}/search", response_model=list[SearchResult])
async def search_library(library_id: str, request: SearchRequest):
    """Executes hybrid, vector, or keyword search across the library's LanceDB store."""
    _, lib_path = _resolve_library_path(library_id)
    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)

    results = await search_service.search(
        library_path=lib_path,
        query=request.query,
        book_id=request.book_id,
        top_k=request.top_k,
        mode=request.mode,
    )
    return results


@router.post("/chat/sessions", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
async def create_chat_session(request: CreateSessionRequest):
    """Creates a new conversational chat thread."""
    _, lib_path = _resolve_library_path(request.library_id)
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)
    agent = RAGChatAgent(search_service=search_service)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        session = await agent.create_session(
            db=db,
            library_id=request.library_id,
            book_id=request.book_id,
            title=request.title,
        )
    return session


@router.get("/chat/sessions", response_model=list[ChatSession])
async def list_chat_sessions(library_id: str = Query(..., description="Library ID")):
    """Lists all chat threads for a library."""
    _, lib_path = _resolve_library_path(library_id)
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)
    agent = RAGChatAgent(search_service=search_service)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        return await agent.list_sessions(db=db, library_id=library_id)


@router.get("/chat/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session_details(session_id: str):
    """Retrieves full dialogue history and citations for a session."""
    _, lib_path = _resolve_library_path()
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)
    agent = RAGChatAgent(search_service=search_service)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        session = await agent.get_session(db=db, session_id=session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found",
        )
    return session


@router.delete("/chat/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(session_id: str):
    """Deletes a chat session and associated messages."""
    _, lib_path = _resolve_library_path()
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)
    agent = RAGChatAgent(search_service=search_service)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        success = await agent.delete_session(db=db, session_id=session_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found",
        )


@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessage)
async def send_chat_message(session_id: str, request: SendMessageRequest):
    """Sends a user query and returns a citation-grounded assistant response."""
    _, lib_path = _resolve_library_path()
    db_file = lib_path / "metadata.db"

    embedder = _get_embedding_provider()
    search_service = RAGSearchService(embedding_provider=embedder)
    agent = RAGChatAgent(search_service=search_service, llm_adapter=_default_llm_call)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        try:
            return await agent.send_message(
                db=db,
                library_path=lib_path,
                session_id=session_id,
                user_prompt=request.content,
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
