"""KOReader Kosync protocol compatibility service for progress synchronization."""

from pathlib import Path
from typing import Optional, Tuple
import aiosqlite

from backend.domain.devices import KosyncProgress
from backend.domain.reading import ReadingProgressCreateRequest
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService


class KosyncService:
    """Handles KOReader wireless progress synchronization."""

    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        reading_service: Optional[ReadingService] = None,
    ):
        self.library_manager = library_manager or LibraryManager()
        self.reading_service = reading_service or ReadingService(self.library_manager)

    async def _ensure_table(self, db: aiosqlite.Connection) -> None:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS x_kosync_progress (
                document_hash TEXT PRIMARY KEY,
                progress TEXT NOT NULL,
                percentage REAL NOT NULL,
                device TEXT,
                device_id TEXT,
                updated_at INTEGER NOT NULL
            )
        """)
        await db.commit()

    async def _get_active_library_dir(self) -> Optional[Tuple[str, Path]]:
        lib = self.library_manager.get_active_library()
        if not lib:
            libs = self.library_manager.list_libraries()
            if not libs:
                return None
            lib = libs[0]
        p = Path(lib.path)
        if not p.exists():
            return None
        return lib.id, p

    async def save_progress(self, progress: KosyncProgress, lib_dir: Optional[Path] = None, lib_id: Optional[str] = None) -> None:
        if not lib_dir:
            res = await self._get_active_library_dir()
            if not res:
                return
            lib_id, lib_dir = res

        db_path = lib_dir / "metadata.db"
        async with aiosqlite.connect(db_path) as db:
            await self._ensure_table(db)
            await db.execute("""
                INSERT INTO x_kosync_progress (document_hash, progress, percentage, device, device_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_hash) DO UPDATE SET
                    progress = excluded.progress,
                    percentage = excluded.percentage,
                    device = excluded.device,
                    device_id = excluded.device_id,
                    updated_at = excluded.updated_at
            """, (progress.document, progress.progress, progress.percentage, progress.device, progress.device_id, progress.timestamp))
            await db.commit()

            # Cross-reference with x_file_hashes to update x_reading_progress if known book
            try:
                cur = await db.execute("SELECT book_id, format FROM x_file_hashes WHERE sha256 = ? OR sha256 LIKE ?", (progress.document, f"{progress.document}%"))
                row = await cur.fetchone()
                if row and lib_id:
                    matched_book_id = row[0]
                    matched_fmt = row[1]
                    req = ReadingProgressCreateRequest(
                        format=matched_fmt,
                        location=progress.progress,
                        progress_percent=progress.percentage * 100.0,
                    )
                    await self.reading_service.save_progress(lib_id, matched_book_id, req)
            except Exception:
                pass

    async def get_progress(self, document_hash: str, lib_dir: Optional[Path] = None) -> Optional[KosyncProgress]:
        if not lib_dir:
            res = await self._get_active_library_dir()
            if not res:
                return None
            _, lib_dir = res

        db_path = lib_dir / "metadata.db"
        if not db_path.exists():
            return None

        async with aiosqlite.connect(db_path) as db:
            await self._ensure_table(db)
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT document_hash, progress, percentage, device, device_id, updated_at "
                "FROM x_kosync_progress WHERE document_hash = ?",
                (document_hash,),
            )
            row = await cur.fetchone()
            if not row:
                return None

            return KosyncProgress(
                document=row["document_hash"],
                progress=row["progress"],
                percentage=row["percentage"],
                device=row["device"],
                device_id=row["device_id"],
                timestamp=row["updated_at"],
            )
