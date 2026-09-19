"""Library manager service for creating, adopting, and switching libraries."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Book, Library
from backend.services.calibre_sync import CalibreSyncService


class LibraryManager:
    """Coordinates library creation, adoption of existing Calibre repositories, and queries."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()

    async def adopt_calibre_library(
        self, library_path: Path, name: Optional[str] = None, set_active: bool = True
    ) -> Library:
        """Adopts an existing Calibre library directory in place without copying files."""
        sync_service = CalibreSyncService(library_path)
        # 1. Validate Calibre schema
        await sync_service.validate_calibre_directory(library_path)

        # 2. Augment with xBookLibrary extension tables and .vectors/
        await sync_service.augment_schema()

        # 3. Retrieve book count
        book_count = await sync_service.get_book_count()

        lib_name = name or library_path.name
        lib_id = f"lib-{uuid.uuid4().hex[:8]}"

        library = Library(
            id=lib_id,
            name=lib_name,
            path=str(library_path.resolve()),
            is_calibre_adopted=True,
            book_count=book_count,
            created_at=datetime.now(timezone.utc),
        )

        # 4. Register in global config
        self.config_manager.register_library(library, set_active=set_active)
        return library

    async def create_new_library(
        self, library_path: Path, name: str, set_active: bool = True
    ) -> Library:
        """Creates a brand new portable library with full Calibre schema and .vectors/ directory."""
        library_path.mkdir(parents=True, exist_ok=True)
        db_mgr = DatabaseManager(library_path)
        await db_mgr.initialize_database()

        lib_id = f"lib-{uuid.uuid4().hex[:8]}"
        library = Library(
            id=lib_id,
            name=name,
            path=str(library_path.resolve()),
            is_calibre_adopted=False,
            book_count=0,
            created_at=datetime.now(timezone.utc),
        )

        self.config_manager.register_library(library, set_active=set_active)
        return library

    def list_libraries(self) -> List[Library]:
        config = self.config_manager.load()
        return config.libraries

    def get_active_library(self) -> Optional[Library]:
        return self.config_manager.get_active_library()

    def switch_active_library(self, library_id: str) -> Library:
        config = self.config_manager.load()
        target = next((lib for lib in config.libraries if lib.id == library_id), None)
        if not target:
            raise ValueError(f"Library with id '{library_id}' not found.")
        config.active_library_id = library_id
        self.config_manager.save(config)
        return target

    async def get_books_for_library(
        self, library_id: str, page: int = 1, limit: int = 50, query: Optional[str] = None
    ) -> List[Book]:
        """Queries books from the specified library."""
        config = self.config_manager.load()
        library = next((lib for lib in config.libraries if lib.id == library_id), None)
        if not library:
            raise ValueError(f"Library '{library_id}' not found")

        sync_service = CalibreSyncService(Path(library.path))
        return await sync_service.get_books(page=page, limit=limit, query=query)
