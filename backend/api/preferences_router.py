"""FastAPI router for global application preferences, AI/LLM configuration, and Drop Folder settings."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.config import ConfigManager, UserPreferences
from backend.services.watcher_service import WatcherService

router = APIRouter(prefix="/api/preferences", tags=["Preferences & Admin Console"])


class TestAIConnectionRequest(BaseModel):
    provider: str  # "gemini" | "openai" | "ollama"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_endpoint: Optional[str] = None
    ollama_model: Optional[str] = None


class TestAIConnectionResponse(BaseModel):
    success: bool
    provider: str
    message: str
    available_models: List[str] = []


class ScanDropFolderResponse(BaseModel):
    success: bool
    folder_scanned: str
    jobs_count: int
    files_processed: List[str] = []
    message: str


@router.get("", response_model=UserPreferences)
async def get_preferences():
    """Retrieve the current user preferences and configuration."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    return cfg.preferences


@router.put("", response_model=UserPreferences)
async def update_preferences(updated: UserPreferences):
    """Save and persist user preferences."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    cfg.preferences = updated
    cfg_mgr.save(cfg)
    return cfg.preferences


@router.post("/test-ai", response_model=TestAIConnectionResponse)
async def test_ai_connection(req: TestAIConnectionRequest):
    """Verifies connectivity to the selected AI provider (Gemini, OpenAI, or Ollama)."""
    provider = req.provider.lower()

    if provider == "ollama":
        endpoint = (req.ollama_endpoint or "http://127.0.0.1:11434").rstrip("/")
        if "localhost:11434" in endpoint:
            endpoint = endpoint.replace("localhost:11434", "127.0.0.1:11434")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{endpoint}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    return TestAIConnectionResponse(
                        success=True,
                        provider="ollama",
                        message=f"Connected to local Ollama server at {endpoint}.",
                        available_models=models,
                    )
                else:
                    return TestAIConnectionResponse(
                        success=False,
                        provider="ollama",
                        message=f"Ollama server returned HTTP {res.status_code}",
                    )
        except Exception as e:
            return TestAIConnectionResponse(
                success=False,
                provider="ollama",
                message=f"Could not connect to Ollama at {endpoint}: {e}",
            )

    elif provider == "gemini":
        key = req.gemini_api_key
        if not key or not key.strip():
            return TestAIConnectionResponse(
                success=False,
                provider="gemini",
                message="Gemini API Key is empty.",
            )
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key.strip()}"
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    models = [
                        m.get("name", "").replace("models/", "")
                        for m in data.get("models", [])
                        if "gemini" in m.get("name", "")
                    ][:10]
                    return TestAIConnectionResponse(
                        success=True,
                        provider="gemini",
                        message="Google Gemini API Key validated successfully!",
                        available_models=models,
                    )
                else:
                    return TestAIConnectionResponse(
                        success=False,
                        provider="gemini",
                        message=f"Gemini API returned HTTP {res.status_code}: {res.text[:200]}",
                    )
        except Exception as e:
            return TestAIConnectionResponse(
                success=False,
                provider="gemini",
                message=f"Gemini connection failed: {e}",
            )

    elif provider == "openai":
        key = req.openai_api_key
        if not key or not key.strip():
            return TestAIConnectionResponse(
                success=False,
                provider="openai",
                message="OpenAI API Key is empty.",
            )
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key.strip()}"},
                )
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("id", "") for m in data.get("data", []) if "gpt" in m.get("id", "")][:10]
                    return TestAIConnectionResponse(
                        success=True,
                        provider="openai",
                        message="OpenAI API Key validated successfully!",
                        available_models=models,
                    )
                else:
                    return TestAIConnectionResponse(
                        success=False,
                        provider="openai",
                        message=f"OpenAI API returned HTTP {res.status_code}: {res.text[:200]}",
                    )
        except Exception as e:
            return TestAIConnectionResponse(
                success=False,
                provider="openai",
                message=f"OpenAI connection failed: {e}",
            )

    return TestAIConnectionResponse(
        success=False,
        provider=provider,
        message=f"Unknown provider '{provider}'",
    )


@router.post("/scan-drop-folder", response_model=ScanDropFolderResponse)
async def scan_drop_folder():
    """Immediately scans the configured drop folder and processes any detected book files."""
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()

    drop_folder_str = cfg.preferences.auto_import_folder
    if not drop_folder_str or not drop_folder_str.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Auto-Import / Drop Folder configured in Preferences.",
        )

    drop_path = Path(drop_folder_str.strip())
    if not drop_path.exists():
        try:
            drop_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Drop folder path '{drop_folder_str}' does not exist and could not be created: {e}",
            )

    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active library selected to import books into.",
        )

    watcher = WatcherService(
        library_path=Path(active_lib.path),
        import_dir=drop_path,
        library_id=active_lib.id,
    )

    jobs = await watcher.scan_once()
    processed_files = [str(j.source_path) for j in jobs if j.source_path]

    return ScanDropFolderResponse(
        success=True,
        folder_scanned=str(drop_path),
        jobs_count=len(jobs),
        files_processed=processed_files,
        message=f"Scanned drop folder: processed {len(jobs)} book file(s).",
    )
