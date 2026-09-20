import logging
from typing import List, Optional
import aiosqlite

from backend.domain.custom_columns import SeriesInfo
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class SeriesService:
    """Manages Calibre standard series, books_series_link, and books.series_index."""

    def __init__(self, library_manager: Optional[LibraryManager] = None):
        self.library_manager = library_manager or LibraryManager()

    async def get_series_list(self, library_id: str) -> List[SeriesInfo]:
        """Fetch all series in the library with their associated book count."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT s.id, s.name, COUNT(l.book) as book_count
                FROM series s
                LEFT JOIN books_series_link l ON l.series = s.id
                GROUP BY s.id, s.name
                ORDER BY s.name COLLATE NOCASE ASC
            """)
            rows = await cursor.fetchall()
            return [
                SeriesInfo(
                    id=row["id"],
                    name=row["name"],
                    series_index=1.0,
                    book_count=row["book_count"],
                )
                for row in rows
            ]

    async def get_book_series(self, library_id: str, book_id: int) -> Optional[SeriesInfo]:
        """Fetch series info and index for a specific book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute(
                """
                SELECT s.id, s.name, b.series_index
                FROM books b
                LEFT JOIN books_series_link l ON l.book = b.id
                LEFT JOIN series s ON s.id = l.series
                WHERE b.id = ?
                """,
                (book_id,),
            )
            row = await cursor.fetchone()
            if not row or not row["name"]:
                return None
            return SeriesInfo(
                id=row["id"],
                name=row["name"],
                series_index=float(row["series_index"]) if row["series_index"] is not None else 1.0,
            )

    async def set_book_series(
        self,
        library_id: str,
        book_id: int,
        series_name: Optional[str],
        series_index: float = 1.0,
    ) -> Optional[SeriesInfo]:
        """Assign or remove a series association for a book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            if not series_name or not series_name.strip():
                # Remove series link
                await conn.execute("DELETE FROM books_series_link WHERE book = ?", (book_id,))
                await conn.execute(
                    "UPDATE books SET series_index = 1.0 WHERE id = ?", (book_id,)
                )
                await conn.commit()
                return None

            clean_name = series_name.strip()
            # Upsert series
            await conn.execute("INSERT OR IGNORE INTO series (name) VALUES (?)", (clean_name,))
            cursor = await conn.execute("SELECT id FROM series WHERE name = ?", (clean_name,))
            s_row = await cursor.fetchone()
            if not s_row:
                raise RuntimeError(f"Failed to retrieve series ID for '{clean_name}'.")

            series_id = s_row[0]

            # Upsert link
            await conn.execute("DELETE FROM books_series_link WHERE book = ?", (book_id,))
            await conn.execute(
                "INSERT INTO books_series_link (book, series) VALUES (?, ?)",
                (book_id, series_id),
            )

            # Update book series_index
            await conn.execute(
                "UPDATE books SET series_index = ? WHERE id = ?",
                (series_index, book_id),
            )
            await conn.commit()

            return SeriesInfo(id=series_id, name=clean_name, series_index=series_index)
