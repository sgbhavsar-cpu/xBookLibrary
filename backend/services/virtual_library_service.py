import json
import logging
import re
from typing import Any, Dict, List, Optional
import aiosqlite

from backend.domain.custom_columns import VirtualLibrary
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class VirtualLibraryService:
    """Manages Calibre preferences-backed Virtual Libraries and query filtering."""

    def __init__(self, library_manager: Optional[LibraryManager] = None):
        self.library_manager = library_manager or LibraryManager()

    async def get_virtual_libraries(self, library_id: str) -> List[VirtualLibrary]:
        """Fetch all saved virtual libraries from Calibre's preferences table."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            # Ensure preferences table exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    val TEXT NOT NULL
                )
            """)
            await conn.commit()

            cursor = await conn.execute(
                "SELECT val FROM preferences WHERE key = 'virtual_libraries'"
            )
            row = await cursor.fetchone()
            if not row or not row["val"]:
                return []

            try:
                data = json.loads(row["val"])
                if isinstance(data, dict):
                    return [
                        VirtualLibrary(name=k, query=v)
                        for k, v in data.items()
                        if isinstance(v, str)
                    ]
            except Exception as e:
                logger.error(f"Failed to parse virtual_libraries JSON: {e}")

        return []

    async def save_virtual_library(
        self, library_id: str, name: str, query: str
    ) -> VirtualLibrary:
        """Create or update a virtual library definition in preferences."""
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Virtual library name cannot be empty.")

        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT val FROM preferences WHERE key = 'virtual_libraries'"
            )
            row = await cursor.fetchone()
            current_dict: Dict[str, str] = {}
            if row and row["val"]:
                try:
                    current_dict = json.loads(row["val"])
                except Exception:
                    current_dict = {}

            current_dict[clean_name] = query.strip()
            serialized = json.dumps(current_dict)

            await conn.execute(
                """
                INSERT INTO preferences (key, val) VALUES ('virtual_libraries', ?)
                ON CONFLICT(key) DO UPDATE SET val = excluded.val
                """,
                (serialized,),
            )
            await conn.commit()

        return VirtualLibrary(name=clean_name, query=query.strip())

    async def delete_virtual_library(self, library_id: str, name: str) -> bool:
        """Remove a virtual library from Calibre preferences."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                "SELECT val FROM preferences WHERE key = 'virtual_libraries'"
            )
            row = await cursor.fetchone()
            if not row or not row["val"]:
                return False

            try:
                current_dict = json.loads(row["val"])
                if name in current_dict:
                    del current_dict[name]
                    serialized = json.dumps(current_dict)
                    await conn.execute(
                        "UPDATE preferences SET val = ? WHERE key = 'virtual_libraries'",
                        (serialized,),
                    )
                    await conn.commit()
                    return True
            except Exception as e:
                logger.error(f"Error deleting virtual library: {e}")

        return False

    @staticmethod
    def matches_query(
        query: str,
        book_data: Dict[str, Any],
        custom_values: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Evaluates whether a book record matches a Calibre-style search query."""
        if not query or not query.strip():
            return True

        raw_tokens = re.findall(r'(?:[^\s"]|"(?:\\.|[^"])*")+', query.strip())
        custom_vals = custom_values or {}

        pending_not = False
        for raw_token in raw_tokens:
            token = raw_token.strip()
            if not token:
                continue

            if token.lower() == "and":
                continue
            if token.lower() in ("not", "!"):
                pending_not = True
                continue

            negated = pending_not
            pending_not = False

            if token.lower().startswith("not ") or token.startswith("!"):
                negated = not negated
                token = re.sub(r'^(not\s+|!)', '', token, flags=re.IGNORECASE).strip()

            matched = True
            if ":" in token:
                field, val = token.split(":", 1)
                field = field.strip().lower()
                val = val.strip().strip('"').strip("'").lower()

                if field in ("tag", "tags"):
                    tags = [t.lower() for t in book_data.get("tags", [])]
                    matched = any(val in t for t in tags)
                elif field in ("author", "authors"):
                    authors = [a.lower() for a in book_data.get("authors", [])]
                    matched = any(val in a for a in authors)
                elif field in ("series",):
                    series_name = (book_data.get("series") or "").lower()
                    matched = val in series_name
                elif field.startswith("#"):
                    col_label = field.lstrip("#")
                    col_val = str(custom_vals.get(col_label, "")).lower()
                    matched = val in col_val
                elif field == "title":
                    title = str(book_data.get("title", "")).lower()
                    matched = val in title
                else:
                    # Generic text search on field
                    matched = val in str(book_data.get(field, "")).lower()
            else:
                # Plain free-text match across title, authors, and summary
                clean_term = token.strip('"').strip("'").lower()
                title = str(book_data.get("title", "")).lower()
                authors_str = " ".join(book_data.get("authors", [])).lower()
                summary = str(book_data.get("summary", "")).lower()
                matched = (clean_term in title) or (clean_term in authors_str) or (clean_term in summary)

            if negated:
                matched = not matched

            if not matched:
                return False

        return True
