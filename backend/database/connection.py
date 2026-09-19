"""Dynamic per-library SQLite database connection manager."""

from pathlib import Path
from typing import Optional

import aiosqlite

from backend.database.schema import CALIBRE_SCHEMA_DDL


class DatabaseManager:
    """Manages SQLite connections to active library metadata.db."""

    def __init__(self, library_path: Optional[Path] = None):
        self.library_path = library_path
        self.db_path = library_path / "metadata.db" if library_path else None

    def set_library(self, library_path: Path) -> None:
        self.library_path = library_path
        self.db_path = library_path / "metadata.db"

    async def initialize_database(self) -> None:
        """Initialize metadata.db with standard Calibre and x_ tables if not present."""
        if not self.db_path:
            raise ValueError("Library path is not configured.")

        self.library_path.mkdir(parents=True, exist_ok=True)
        # Create .vectors folder as mandated by Constitution Principle I
        vectors_dir = self.library_path / ".vectors"
        vectors_dir.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(CALIBRE_SCHEMA_DDL)
            await db.commit()

    async def get_connection(self) -> aiosqlite.Connection:
        if not self.db_path:
            raise ValueError("Library path is not configured.")
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA foreign_keys = ON")
        return conn
