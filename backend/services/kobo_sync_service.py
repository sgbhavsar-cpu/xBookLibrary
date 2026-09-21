"""Kobo Store Sync API compatibility service for wireless Kobo e-reader synchronization."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import aiosqlite

from backend.domain.devices import KoboItem, KoboSyncResponse
from backend.domain.reading import ReadingProgressCreateRequest
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService


class KoboSyncService:
    """Implements Kobo Store Sync v1 protocol and reading progress synchronizer."""

    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        reading_service: Optional[ReadingService] = None,
    ):
        self.library_manager = library_manager or LibraryManager()
        self.reading_service = reading_service or ReadingService(self.library_manager)

    async def get_library_by_token(self, auth_token: str) -> Optional[Tuple[str, Path]]:
        """Scans registered libraries to find the one associated with this Kobo auth_token."""
        for lib in self.library_manager.list_libraries():
            lib_dir = Path(lib.path)
            db_path = lib_dir / "metadata.db"
            if not db_path.exists():
                continue
            try:
                async with aiosqlite.connect(db_path) as db:
                    db.row_factory = aiosqlite.Row
                    cur = await db.execute("SELECT id FROM x_devices WHERE auth_token = ?", (auth_token,))
                    row = await cur.fetchone()
                    if row:
                        return lib.id, lib_dir
            except Exception:
                continue
        return None

    async def get_user_profile(self, auth_token: str) -> Dict[str, str]:
        res = await self.get_library_by_token(auth_token)
        if not res:
            raise ValueError("Invalid Kobo authentication token.")
        lib_id, _ = res
        return {
            "user_key": f"kobo-{auth_token[:8]}",
            "user_id": f"user-{auth_token[:8]}",
            "library_id": lib_id,
        }

    async def sync_library(self, auth_token: str) -> KoboSyncResponse:
        res = await self.get_library_by_token(auth_token)
        if not res:
            raise ValueError("Invalid Kobo authentication token.")
        lib_id, lib_dir = res
        db_path = lib_dir / "metadata.db"

        items: List[KoboItem] = []
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cur_tables = await db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in await cur_tables.fetchall()}

            pub_clause = "(SELECT GROUP_CONCAT(pub.name, ', ') FROM publishers pub JOIN books_publishers_link bpl ON pub.id = bpl.publisher WHERE bpl.book = b.id) as publisher_names" if "publishers" in existing_tables else "NULL as publisher_names"
            desc_clause = "(SELECT c.text FROM comments c WHERE c.book = b.id) as description" if "comments" in existing_tables else "NULL as description"

            cursor = await db.execute(f"""
                SELECT b.id, b.title, b.path,
                       (SELECT GROUP_CONCAT(a.name, ', ')
                        FROM authors a JOIN books_authors_link bal ON a.id = bal.author
                        WHERE bal.book = b.id) as author_names,
                       {pub_clause},
                       {desc_clause}
                FROM books b
                ORDER BY b.id ASC
            """)
            rows = await cursor.fetchall()
            for r in rows:
                book_id = r["id"]
                # Check for EPUB format
                cur_fmt = await db.execute(
                    "SELECT format FROM data WHERE book = ? AND format IN ('EPUB', 'KEPUB', 'PDF')",
                    (book_id,),
                )
                fmt_row = await cur_fmt.fetchone()
                fmt = fmt_row["format"].upper() if fmt_row else "EPUB"

                items.append(
                    KoboItem(
                        Id=f"book-{book_id}",
                        Title=r["title"],
                        Author=r["author_names"] or "Unknown Author",
                        Publisher=r["publisher_names"],
                        Description=r["description"],
                        DownloadUrl=f"/api/sync/kobo/{auth_token}/v1/books/{book_id}/file",
                        Format=fmt,
                    )
                )

        return KoboSyncResponse(
            NewEntitlementCount=len(items),
            Items=items,
        )

    async def update_reading_state(
        self,
        auth_token: str,
        book_id: int,
        progress_percent: float,
        last_read: Optional[str] = None,
    ) -> bool:
        res = await self.get_library_by_token(auth_token)
        if not res:
            raise ValueError("Invalid Kobo authentication token.")
        lib_id, _ = res

        req = ReadingProgressCreateRequest(
            format="EPUB",
            location=f"kobo-percent-{progress_percent:.1f}",
            progress_percent=progress_percent,
        )
        await self.reading_service.save_progress(lib_id, book_id, req)
        return True

    async def get_book_file(self, auth_token: str, book_id: int) -> Tuple[Path, str, str]:
        res = await self.get_library_by_token(auth_token)
        if not res:
            raise ValueError("Invalid Kobo authentication token.")
        lib_id, lib_dir = res
        db_path = lib_dir / "metadata.db"

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT title, path FROM books WHERE id = ?", (book_id,))
            book_row = await cur.fetchone()
            if not book_row:
                raise FileNotFoundError(f"Book with id {book_id} not found.")

            cur = await db.execute(
                "SELECT format, name FROM data WHERE book = ? AND format IN ('EPUB', 'KEPUB', 'PDF') ORDER BY (format = 'EPUB') DESC",
                (book_id,),
            )
            fmt_row = await cur.fetchone()
            if not fmt_row:
                raise FileNotFoundError(f"No readable format available for book {book_id}.")

            fmt = fmt_row["format"].lower()
            fname = fmt_row["name"]

        book_path = lib_dir / book_row["path"] / f"{fname}.{fmt}"
        if not book_path.exists():
            matches = list((lib_dir / book_row["path"]).glob(f"*.{fmt}"))
            if matches:
                book_path = matches[0]
            else:
                raise FileNotFoundError(f"File {fname}.{fmt} not found on disk.")

        media_type = "application/epub+zip" if fmt in ("epub", "kepub") else "application/pdf"
        return book_path, media_type, f"{book_row['title']}.{fmt}"
