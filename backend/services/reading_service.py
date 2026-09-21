import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import aiosqlite

from backend.domain.reading import (
    Annotation,
    AnnotationCreateRequest,
    Bookmark,
    BookmarkCreateRequest,
    ReadingProgress,
    ReadingProgressCreateRequest,
)
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)


class ReadingService:
    """Manages reading progress tracking, cross-device synchronization, highlights, and bookmarks."""

    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        custom_columns_service: Optional[CustomColumnsService] = None,
    ):
        self.library_manager = library_manager or LibraryManager()
        self.custom_columns_service = custom_columns_service or CustomColumnsService(self.library_manager)

    async def _ensure_tables(self, conn: aiosqlite.Connection):
        """Ensure reading progress and annotation tables exist."""
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS x_reading_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                format TEXT NOT NULL,
                location TEXT NOT NULL,
                progress_percent REAL NOT NULL DEFAULT 0.0,
                total_seconds INTEGER NOT NULL DEFAULT 0,
                last_read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
                UNIQUE(book_id, format)
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_reading_progress_book ON x_reading_progress (book_id)
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS x_annotations (
                id TEXT PRIMARY KEY,
                book_id INTEGER NOT NULL,
                format TEXT NOT NULL,
                location TEXT NOT NULL,
                selected_text TEXT NOT NULL,
                color TEXT NOT NULL DEFAULT 'yellow',
                note_text TEXT,
                chapter_title TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_annotations_book ON x_annotations (book_id)
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS x_bookmarks (
                id TEXT PRIMARY KEY,
                book_id INTEGER NOT NULL,
                format TEXT NOT NULL,
                location TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_bookmarks_book ON x_bookmarks (book_id)
        """)
        await conn.commit()

    async def get_progress(
        self, library_id: str, book_id: int, format_name: Optional[str] = None
    ) -> Optional[ReadingProgress]:
        """Fetch current reading progress for a book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            if format_name:
                cursor = await conn.execute(
                    """
                    SELECT id, book_id, format, location, progress_percent, total_seconds, last_read_at
                    FROM x_reading_progress
                    WHERE book_id = ? AND UPPER(format) = UPPER(?)
                    """,
                    (book_id, format_name),
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT id, book_id, format, location, progress_percent, total_seconds, last_read_at
                    FROM x_reading_progress
                    WHERE book_id = ?
                    ORDER BY last_read_at DESC LIMIT 1
                    """,
                    (book_id,),
                )

            row = await cursor.fetchone()
            if not row:
                return None

            last_read = None
            if row["last_read_at"]:
                try:
                    last_read = datetime.fromisoformat(row["last_read_at"])
                except Exception:
                    last_read = None

            return ReadingProgress(
                id=row["id"],
                book_id=row["book_id"],
                format=row["format"],
                location=row["location"],
                progress_percent=float(row["progress_percent"]),
                total_seconds=int(row["total_seconds"]),
                last_read_at=last_read,
            )

    async def save_progress(
        self, library_id: str, book_id: int, req: ReadingProgressCreateRequest
    ) -> ReadingProgress:
        """Upsert reading progress and sync Calibre #read_status custom column if present."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            fmt = req.format.upper()
            cursor = await conn.execute(
                "SELECT id, total_seconds FROM x_reading_progress WHERE book_id = ? AND UPPER(format) = ?",
                (book_id, fmt),
            )
            existing = await cursor.fetchone()

            now = datetime.now(timezone.utc).isoformat()
            if existing:
                new_total_seconds = existing["total_seconds"] + req.seconds_increment
                await conn.execute(
                    """
                    UPDATE x_reading_progress
                    SET location = ?, progress_percent = ?, total_seconds = ?, last_read_at = ?
                    WHERE id = ?
                    """,
                    (req.location, req.progress_percent, new_total_seconds, now, existing["id"]),
                )
                progress_id = existing["id"]
            else:
                new_total_seconds = req.seconds_increment
                cursor = await conn.execute(
                    """
                    INSERT INTO x_reading_progress (book_id, format, location, progress_percent, total_seconds, last_read_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (book_id, fmt, req.location, req.progress_percent, new_total_seconds, now),
                )
                progress_id = cursor.lastrowid

            await conn.commit()

        # Calibre custom columns sync: update #read_status if defined
        try:
            custom_cols = await self.custom_columns_service.get_custom_columns(library_id)
            read_status_col = next((c for c in custom_cols if c.label == "read_status"), None)
            if read_status_col:
                if req.progress_percent >= 98.0:
                    status_val = "completed"
                elif req.progress_percent > 0.0:
                    status_val = "reading"
                else:
                    status_val = "unread"

                await self.custom_columns_service.set_book_custom_values(
                    library_id, book_id, {"read_status": status_val}
                )
        except Exception as e:
            logger.warning(f"Could not auto-sync #read_status: {e}")

        return ReadingProgress(
            id=progress_id,
            book_id=book_id,
            format=fmt,
            location=req.location,
            progress_percent=req.progress_percent,
            total_seconds=new_total_seconds,
            last_read_at=datetime.now(timezone.utc),
        )

    async def list_annotations(self, library_id: str, book_id: int) -> List[Annotation]:
        """Fetch all annotations and highlights for a book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            cursor = await conn.execute(
                """
                SELECT id, book_id, format, location, selected_text, color, note_text, chapter_title, created_at, updated_at
                FROM x_annotations
                WHERE book_id = ?
                ORDER BY created_at ASC
                """,
                (book_id,),
            )
            rows = await cursor.fetchall()
            annotations = []
            for r in rows:
                c_at = None
                u_at = None
                if r["created_at"]:
                    try:
                        c_at = datetime.fromisoformat(r["created_at"])
                    except Exception:
                        c_at = None
                if r["updated_at"]:
                    try:
                        u_at = datetime.fromisoformat(r["updated_at"])
                    except Exception:
                        u_at = None

                annotations.append(
                    Annotation(
                        id=r["id"],
                        book_id=r["book_id"],
                        format=r["format"],
                        location=r["location"],
                        selected_text=r["selected_text"],
                        color=r["color"],
                        note_text=r["note_text"],
                        chapter_title=r["chapter_title"],
                        created_at=c_at,
                        updated_at=u_at,
                    )
                )
            return annotations

    async def create_annotation(
        self, library_id: str, book_id: int, req: AnnotationCreateRequest
    ) -> Annotation:
        """Create a new highlight or note."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        annotation_id = f"ann-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            await conn.execute(
                """
                INSERT INTO x_annotations (id, book_id, format, location, selected_text, color, note_text, chapter_title, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    annotation_id,
                    book_id,
                    req.format.upper(),
                    req.location,
                    req.selected_text,
                    req.color,
                    req.note_text,
                    req.chapter_title,
                    now,
                    now,
                ),
            )
            await conn.commit()

        return Annotation(
            id=annotation_id,
            book_id=book_id,
            format=req.format.upper(),
            location=req.location,
            selected_text=req.selected_text,
            color=req.color,
            note_text=req.note_text,
            chapter_title=req.chapter_title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

    async def delete_annotation(self, library_id: str, annotation_id: str) -> bool:
        """Delete an annotation."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            await self._ensure_tables(conn)
            cursor = await conn.execute("DELETE FROM x_annotations WHERE id = ?", (annotation_id,))
            await conn.commit()
            return cursor.rowcount > 0

    async def list_bookmarks(self, library_id: str, book_id: int) -> List[Bookmark]:
        """Fetch all bookmarks for a book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            cursor = await conn.execute(
                "SELECT id, book_id, format, location, title, created_at FROM x_bookmarks WHERE book_id = ? ORDER BY created_at ASC",
                (book_id,),
            )
            rows = await cursor.fetchall()
            bookmarks = []
            for r in rows:
                c_at = None
                if r["created_at"]:
                    try:
                        c_at = datetime.fromisoformat(r["created_at"])
                    except Exception:
                        c_at = None
                bookmarks.append(
                    Bookmark(
                        id=r["id"],
                        book_id=r["book_id"],
                        format=r["format"],
                        location=r["location"],
                        title=r["title"],
                        created_at=c_at,
                    )
                )
            return bookmarks

    async def create_bookmark(
        self, library_id: str, book_id: int, req: BookmarkCreateRequest
    ) -> Bookmark:
        """Create a new bookmark."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        bm_id = f"bm-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()

        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            await self._ensure_tables(conn)

            await conn.execute(
                "INSERT INTO x_bookmarks (id, book_id, format, location, title, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (bm_id, book_id, req.format.upper(), req.location, req.title, now),
            )
            await conn.commit()

        return Bookmark(
            id=bm_id,
            book_id=book_id,
            format=req.format.upper(),
            location=req.location,
            title=req.title,
            created_at=datetime.now(timezone.utc),
        )

    async def delete_bookmark(self, library_id: str, bookmark_id: str) -> bool:
        """Delete a bookmark."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            await self._ensure_tables(conn)
            cursor = await conn.execute("DELETE FROM x_bookmarks WHERE id = ?", (bookmark_id,))
            await conn.commit()
            return cursor.rowcount > 0

    async def export_annotations_markdown(self, library_id: str, book_id: int) -> str:
        """Export all highlights, notes, and bookmarks to clean Markdown format."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("SELECT title, author_sort FROM books WHERE id = ?", (book_id,))
            book_row = await cursor.fetchone()
            title = book_row["title"] if book_row else f"Book {book_id}"
            author = book_row["author_sort"] if book_row else "Unknown Author"

        annotations = await self.list_annotations(library_id, book_id)
        bookmarks = await self.list_bookmarks(library_id, book_id)

        lines = [
            f"# Reading Notes & Highlights: {title}",
            f"**Author**: {author}  ",
            f"**Exported On**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}  ",
            "",
            "---",
            "",
            "## Highlights & Annotations",
            "",
        ]

        if not annotations:
            lines.append("_No highlights or notes recorded for this book._\n")
        else:
            for idx, ann in enumerate(annotations, start=1):
                chapter = f" ({ann.chapter_title})" if ann.chapter_title else ""
                lines.append(f"### {idx}. Highlight{chapter}")
                lines.append(f"> {ann.selected_text}")
                lines.append("")
                if ann.note_text:
                    lines.append(f"**Note**: {ann.note_text}  ")
                lines.append(f"*Color*: `{ann.color}` | *Location*: `{ann.location}`  ")
                lines.append("")

        lines.extend([
            "---",
            "",
            "## Bookmarks",
            "",
        ])

        if not bookmarks:
            lines.append("_No bookmarks saved._\n")
        else:
            for bm in bookmarks:
                lines.append(f"- **{bm.title}** (Location: `{bm.location}`)")

        return "\n".join(lines)
