"""Global configuration and library registry manager."""

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field

from backend.domain.devices import SMTPSettings
from backend.domain.entities import Library


class UserPreferences(BaseModel):
    theme: str = "dark"
    default_page_size: int = 50
    default_format: str = "EPUB"
    view_mode: str = "grid"

    # AI & LLM Services Configuration
    active_ai_provider: str = "ollama"  # "gemini" | "openai" | "ollama"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_endpoint: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    embedding_model: str = "all-MiniLM-L6-v2"

    # Drop Folder / Auto-Import Configuration
    auto_import_folder: Optional[str] = None
    auto_import_enabled: bool = False
    auto_import_action: str = "merge"  # "skip" | "create_new" | "merge"

    # Sharing & Network
    opds_enabled: bool = True
    opds_port: int = 8000
    smtp_settings: SMTPSettings = Field(default_factory=SMTPSettings)


class AppConfig(BaseModel):
    active_library_id: Optional[str] = None
    libraries: List[Library] = Field(default_factory=list)
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class ConfigManager:
    """Manages the persistence of ~/.xbooklibrary/config.json."""

    def __init__(self, config_dir: Optional[Path] = None):
        import os

        if config_dir is None:
            env_override = os.environ.get("XBOOKLIBRARY_CONFIG_DIR")
            if env_override:
                config_dir = Path(env_override)
            else:
                config_dir = Path.home() / ".xbooklibrary"
        self.config_dir = config_dir
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_file()

    def _ensure_config_file(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            default_config = AppConfig()
            self.save(default_config)

    def load(self) -> AppConfig:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig.model_validate(data)
        except Exception:
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        with open(self.config_file, "w", encoding="utf-8") as f:
            f.write(config.model_dump_json(indent=2))

    def get_active_library(self) -> Optional[Library]:
        config = self.load()
        if not config.active_library_id:
            return config.libraries[0] if config.libraries else None
        for lib in config.libraries:
            if lib.id == config.active_library_id:
                return lib
        return config.libraries[0] if config.libraries else None

    def register_library(self, library: Library, set_active: bool = True) -> Library:
        config = self.load()
        # Check if already registered
        existing = [
            lib for lib in config.libraries if lib.id == library.id or lib.path == library.path
        ]
        if not existing:
            config.libraries.append(library)
        else:
            # Update existing
            for idx, lib in enumerate(config.libraries):
                if lib.id == library.id or lib.path == library.path:
                    config.libraries[idx] = library
        if set_active:
            config.active_library_id = library.id
        self.save(config)
        return library

    def get_gemini_api_key(self) -> Optional[str]:
        import os

        return os.environ.get("GEMINI_API_KEY") or self.load().preferences.gemini_api_key

    def get_openai_api_key(self) -> Optional[str]:
        import os

        return os.environ.get("OPENAI_API_KEY") or self.load().preferences.openai_api_key

    def get_ollama_endpoint(self) -> str:
        import os

        ep = os.environ.get("OLLAMA_HOST") or self.load().preferences.ollama_endpoint or "http://127.0.0.1:11434"
        if "localhost:11434" in ep:
            ep = ep.replace("localhost:11434", "127.0.0.1:11434")
        return ep.rstrip("/")

    def get_ollama_model(self) -> str:
        return self.load().preferences.ollama_model or "qwen2.5-coder:7b"
