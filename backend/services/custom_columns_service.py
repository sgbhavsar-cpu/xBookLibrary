import json
import logging
from typing import Any, Dict, List, Optional
import aiosqlite

from backend.domain.custom_columns import (
    BookCustomValues,
    CustomColumnCreateRequest,
    CustomColumnDatatype,
    CustomColumnDefinition,
    STANDARD_CUSTOM_COLUMN_PRESETS,
)
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class CustomColumnsService:
    """Manages Calibre 7.x custom_columns schema DDL, metadata definitions, and per-book values."""

    def __init__(self, library_manager: Optional[LibraryManager] = None):
        self.library_manager = library_manager or LibraryManager()

    async def get_custom_columns(self, library_id: str) -> List[CustomColumnDefinition]:
        """Fetch all active custom column definitions for a library."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            # Ensure custom_columns table exists
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS custom_columns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    datatype TEXT NOT NULL,
                    mark_for_delete INTEGER DEFAULT 0,
                    editable INTEGER DEFAULT 1,
                    display TEXT DEFAULT '{}',
                    is_multiple INTEGER DEFAULT 0,
                    normalized INTEGER DEFAULT 0
                )
            """)
            await conn.commit()

            cursor = await conn.execute("""
                SELECT id, label, name, datatype, mark_for_delete, editable, display, is_multiple, normalized
                FROM custom_columns
                WHERE mark_for_delete = 0
                ORDER BY id ASC
            """)
            rows = await cursor.fetchall()
            columns: List[CustomColumnDefinition] = []
            for row in rows:
                try:
                    display_data = json.loads(row["display"]) if row["display"] else {}
                except Exception:
                    display_data = {}

                columns.append(
                    CustomColumnDefinition(
                        id=row["id"],
                        label=row["label"],
                        name=row["name"],
                        datatype=CustomColumnDatatype(row["datatype"]),
                        is_multiple=bool(row["is_multiple"]),
                        normalized=bool(row["normalized"]),
                        display=display_data,
                        editable=bool(row["editable"]),
                    )
                )
            return columns

    async def create_custom_column(
        self, library_id: str, req: CustomColumnCreateRequest
    ) -> CustomColumnDefinition:
        """Define a new custom column and execute the required Calibre SQLite DDL."""
        clean_label = req.label.lstrip("#").strip().lower()
        if not clean_label:
            raise ValueError("Invalid column label.")

        # Determine normalized vs denormalized representation
        is_normalized = (
            req.datatype in (CustomColumnDatatype.ENUMERATION, CustomColumnDatatype.SERIES)
            or req.is_multiple
        )

        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            # Check if column already exists
            cursor = await conn.execute(
                "SELECT id FROM custom_columns WHERE label = ?", (clean_label,)
            )
            existing = await cursor.fetchone()
            if existing:
                col_id = existing["id"]
                # Reactivate if marked for delete
                await conn.execute(
                    "UPDATE custom_columns SET mark_for_delete = 0, name = ?, display = ? WHERE id = ?",
                    (req.name, json.dumps(req.display), col_id),
                )
                await conn.commit()
                return CustomColumnDefinition(
                    id=col_id,
                    label=clean_label,
                    name=req.name,
                    datatype=req.datatype,
                    is_multiple=req.is_multiple,
                    normalized=is_normalized,
                    display=req.display,
                )

            # Insert column definition
            cursor = await conn.execute(
                """
                INSERT INTO custom_columns (label, name, datatype, display, is_multiple, normalized)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_label,
                    req.name,
                    req.datatype.value,
                    json.dumps(req.display),
                    1 if req.is_multiple else 0,
                    1 if is_normalized else 0,
                ),
            )
            col_id = cursor.lastrowid
            if not col_id:
                raise RuntimeError("Failed to generate custom column ID.")

            # Generate dynamic table DDL
            if not is_normalized:
                sql_type = "INTEGER"
                if req.datatype == CustomColumnDatatype.FLOAT:
                    sql_type = "REAL"
                elif req.datatype in (
                    CustomColumnDatatype.TEXT,
                    CustomColumnDatatype.COMMENTS,
                ):
                    sql_type = "TEXT"

                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS custom_column_{col_id} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book INTEGER NOT NULL UNIQUE,
                        value {sql_type},
                        FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE
                    )
                """)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS cc_{col_id}_idx ON custom_column_{col_id} (book)
                """)
            else:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS custom_column_{col_id} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        value TEXT NOT NULL UNIQUE
                    )
                """)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS cc_{col_id}_val_idx ON custom_column_{col_id} (value)
                """)
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS books_custom_column_{col_id}_link (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        book INTEGER NOT NULL,
                        value INTEGER NOT NULL,
                        extra REAL,
                        FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
                        FOREIGN KEY(value) REFERENCES custom_column_{col_id}(id) ON DELETE CASCADE,
                        UNIQUE(book, value)
                    )
                """)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS bccl_{col_id}_idx ON books_custom_column_{col_id}_link (book, value)
                """)

            await conn.commit()

            return CustomColumnDefinition(
                id=col_id,
                label=clean_label,
                name=req.name,
                datatype=req.datatype,
                is_multiple=req.is_multiple,
                normalized=is_normalized,
                display=req.display,
            )

    async def install_default_presets(self, library_id: str) -> List[CustomColumnDefinition]:
        """Installs standard presets (#read_status, #difficulty, #rating, #pages, #notes)."""
        existing = await self.get_custom_columns(library_id)
        existing_labels = {col.label for col in existing}

        for preset in STANDARD_CUSTOM_COLUMN_PRESETS:
            if preset.label not in existing_labels:
                await self.create_custom_column(library_id, preset)

        return await self.get_custom_columns(library_id)

    async def get_book_custom_values(self, library_id: str, book_id: int) -> BookCustomValues:
        """Fetch all custom column values assigned to a book."""
        columns = await self.get_custom_columns(library_id)
        values: Dict[str, Any] = {}

        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            for col in columns:
                try:
                    if not col.normalized:
                        cursor = await conn.execute(
                            f"SELECT value FROM custom_column_{col.id} WHERE book = ?",
                            (book_id,),
                        )
                        row = await cursor.fetchone()
                        if row and row[0] is not None:
                            values[col.label] = row[0]
                    else:
                        cursor = await conn.execute(
                            f"""
                            SELECT c.value FROM custom_column_{col.id} c
                            JOIN books_custom_column_{col.id}_link l ON l.value = c.id
                            WHERE l.book = ?
                            ORDER BY c.id ASC
                            """,
                            (book_id,),
                        )
                        rows = await cursor.fetchall()
                        if col.is_multiple:
                            values[col.label] = [r[0] for r in rows] if rows else []
                        else:
                            values[col.label] = rows[0][0] if rows else None
                except Exception as e:
                    logger.debug(f"Could not read custom column {col.label}: {e}")

        return BookCustomValues(book_id=book_id, values=values)

    async def set_book_custom_values(
        self, library_id: str, book_id: int, values: Dict[str, Any]
    ) -> BookCustomValues:
        """Upsert custom values for a book in a Calibre-compatible manner."""
        columns = await self.get_custom_columns(library_id)
        col_map = {col.label: col for col in columns}

        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            for raw_label, val in values.items():
                label = raw_label.lstrip("#")
                if label not in col_map:
                    continue

                col = col_map[label]
                if not col.normalized:
                    if val is None or val == "":
                        await conn.execute(
                            f"DELETE FROM custom_column_{col.id} WHERE book = ?",
                            (book_id,),
                        )
                    else:
                        await conn.execute(
                            f"""
                            INSERT INTO custom_column_{col.id} (book, value)
                            VALUES (?, ?)
                            ON CONFLICT(book) DO UPDATE SET value = excluded.value
                            """,
                            (book_id, val),
                        )
                else:
                    await conn.execute(
                        f"DELETE FROM books_custom_column_{col.id}_link WHERE book = ?",
                        (book_id,),
                    )
                    if val is not None and val != "":
                        val_list = val if isinstance(val, list) else [val]
                        for item in val_list:
                            item_str = str(item).strip()
                            if not item_str:
                                continue
                            await conn.execute(
                                f"INSERT OR IGNORE INTO custom_column_{col.id} (value) VALUES (?)",
                                (item_str,),
                            )
                            cursor = await conn.execute(
                                f"SELECT id FROM custom_column_{col.id} WHERE value = ?",
                                (item_str,),
                            )
                            val_row = await cursor.fetchone()
                            if val_row:
                                await conn.execute(
                                    f"""
                                    INSERT OR REPLACE INTO books_custom_column_{col.id}_link (book, value)
                                    VALUES (?, ?)
                                    """,
                                    (book_id, val_row[0]),
                                )

            await conn.commit()

        return await self.get_book_custom_values(library_id, book_id)
