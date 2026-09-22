"""Device management and dispatch service for Kindle, Kobo, and USB export."""

from datetime import datetime, timezone
from pathlib import Path
import shutil
import uuid
from typing import List, Optional

import aiosqlite

from backend.domain.devices import (
    Device,
    DeviceCreateRequest,
    DeviceSyncLog,
    DeviceSyncStatus,
    DeviceType,
    ExportToDirectoryRequest,
    SendToDeviceRequest,
    SMTPSettings,
)
from backend.services.conversion_service import ConversionService
from backend.services.email_service import EmailService
from backend.services.library_manager import LibraryManager
from backend.services.storage_service import sanitize_filename


class DeviceService:
    """Manages registered e-reader devices and dispatches books via SMTP or directory export."""

    def __init__(
        self,
        library_manager: Optional[LibraryManager] = None,
        email_service: Optional[EmailService] = None,
    ):
        self.library_manager = library_manager or LibraryManager()
        self.email_service = email_service or EmailService()

    async def _get_library_dir(self, library_id: str) -> Path:
        lib = self.library_manager.get_library(library_id)
        if not lib:
            raise ValueError(f"Library '{library_id}' not found.")
        lib_dir = Path(lib.path)
        if not lib_dir.exists():
            raise FileNotFoundError(f"Library directory '{lib.path}' does not exist.")
        return lib_dir

    async def _ensure_tables(self, db: aiosqlite.Connection) -> None:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS x_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                target_address TEXT,
                auth_token TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_sync_at DATETIME
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS x_device_sync_logs (
                id TEXT PRIMARY KEY,
                book_id INTEGER NOT NULL,
                book_title TEXT NOT NULL,
                device_id TEXT,
                device_type TEXT NOT NULL,
                format_sent TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(device_id) REFERENCES x_devices(id) ON DELETE SET NULL
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_x_device_sync_logs_book ON x_device_sync_logs (book_id)
        """)
        await db.commit()

    async def list_devices(self, library_id: str) -> List[Device]:
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        devices: List[Device] = []
        async with aiosqlite.connect(db_path) as db:
            await self._ensure_tables(db)
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, name, device_type, target_address, auth_token, created_at, last_sync_at "
                "FROM x_devices ORDER BY created_at DESC"
            )
            rows = await cursor.fetchall()
            for r in rows:
                devices.append(
                    Device(
                        id=r["id"],
                        name=r["name"],
                        device_type=DeviceType(r["device_type"]),
                        target_address=r["target_address"],
                        auth_token=r["auth_token"],
                        created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc),
                        last_sync_at=datetime.fromisoformat(r["last_sync_at"]) if r["last_sync_at"] else None,
                    )
                )
        return devices

    async def get_device(self, library_id: str, device_id: str) -> Optional[Device]:
        devices = await self.list_devices(library_id)
        for d in devices:
            if d.id == device_id:
                return d
        return None

    async def create_device(self, library_id: str, req: DeviceCreateRequest) -> Device:
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        device_id = f"dev-{uuid.uuid4().hex[:8]}"
        auth_token = uuid.uuid4().hex if req.device_type in (DeviceType.KOBO, DeviceType.KOREADER) else None
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        async with aiosqlite.connect(db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                "INSERT INTO x_devices (id, name, device_type, target_address, auth_token, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (device_id, req.name, req.device_type.value, req.target_address, auth_token, now_iso),
            )
            await db.commit()

        return Device(
            id=device_id,
            name=req.name,
            device_type=req.device_type,
            target_address=req.target_address,
            auth_token=auth_token,
            created_at=now_dt,
        )

    async def delete_device(self, library_id: str, device_id: str) -> bool:
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("DELETE FROM x_devices WHERE id = ?", (device_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def _update_device_last_sync(self, lib_dir: Path, device_id: str) -> None:
        db_path = lib_dir / "metadata.db"
        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(db_path) as db:
            await db.execute("UPDATE x_devices SET last_sync_at = ? WHERE id = ?", (now_iso, device_id))
            await db.commit()

    async def record_sync_log(
        self,
        lib_dir: Path,
        book_id: int,
        book_title: str,
        device_type: DeviceType,
        format_sent: str,
        status: DeviceSyncStatus,
        device_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> DeviceSyncLog:
        db_path = lib_dir / "metadata.db"
        log_id = f"log-{uuid.uuid4().hex[:8]}"
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        async with aiosqlite.connect(db_path) as db:
            await self._ensure_tables(db)
            await db.execute(
                "INSERT INTO x_device_sync_logs (id, book_id, book_title, device_id, device_type, format_sent, status, error_message, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (log_id, book_id, book_title, device_id, device_type.value, format_sent, status.value, error_message, now_iso),
            )
            await db.commit()

        return DeviceSyncLog(
            id=log_id,
            book_id=book_id,
            book_title=book_title,
            device_id=device_id,
            device_type=device_type,
            format_sent=format_sent,
            status=status,
            error_message=error_message,
            created_at=now_dt,
        )

    async def list_sync_logs(self, library_id: str, limit: int = 50) -> List[DeviceSyncLog]:
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        logs: List[DeviceSyncLog] = []
        async with aiosqlite.connect(db_path) as db:
            await self._ensure_tables(db)
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id, book_id, book_title, device_id, device_type, format_sent, status, error_message, created_at "
                "FROM x_device_sync_logs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            for r in rows:
                logs.append(
                    DeviceSyncLog(
                        id=r["id"],
                        book_id=r["book_id"],
                        book_title=r["book_title"],
                        device_id=r["device_id"],
                        device_type=DeviceType(r["device_type"]),
                        format_sent=r["format_sent"],
                        status=DeviceSyncStatus(r["status"]),
                        error_message=r["error_message"],
                        created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc),
                    )
                )
        return logs

    async def send_to_device(
        self,
        library_id: str,
        book_id: int,
        req: SendToDeviceRequest,
        smtp_settings: Optional[SMTPSettings] = None,
    ) -> DeviceSyncLog:
        """Dispatches an e-book to a registered Kindle device via SMTP with auto-conversion if needed."""
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        # 1. Fetch book metadata and formats
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT id, title, path FROM books WHERE id = ?", (book_id,))
            book_row = await cur.fetchone()
            if not book_row:
                raise ValueError(f"Book with id {book_id} not found in library.")

            cur = await db.execute(
                "SELECT a.name FROM authors a JOIN books_authors_link bal ON a.id = bal.author WHERE bal.book = ?",
                (book_id,),
            )
            author_rows = await cur.fetchall()
            authors = [r["name"] for r in author_rows] or ["Unknown Author"]

            cur = await db.execute("SELECT format, name FROM data WHERE book = ?", (book_id,))
            format_rows = await cur.fetchall()
            formats_dict = {r["format"].upper(): r["name"] for r in format_rows}

        book_title = book_row["title"]
        book_rel_path = book_row["path"]
        first_author = authors[0]

        # 2. Resolve target device and recipient
        target_email = req.custom_recipient
        device_id = req.device_id
        device_type = DeviceType.KINDLE

        if device_id:
            device = await self.get_device(library_id, device_id)
            if not device:
                raise ValueError(f"Device '{device_id}' not found.")
            target_email = target_email or device.target_address
            device_type = device.device_type

        if not target_email:
            raise ValueError("No recipient address provided for device dispatch.")

        # 3. Choose best format (prefer EPUB, then PDF). Auto-convert if only non-EPUB is available.
        chosen_format = req.preferred_format.upper() if req.preferred_format else None
        if not chosen_format:
            if "EPUB" in formats_dict:
                chosen_format = "EPUB"
            elif "PDF" in formats_dict:
                chosen_format = "PDF"
            elif any(fmt in formats_dict for fmt in ("MOBI", "AZW3", "DOCX", "TXT")):
                # Auto-convert to EPUB
                source_fmt = next(fmt for fmt in ("MOBI", "AZW3", "DOCX", "TXT") if fmt in formats_dict)
                conv_svc = ConversionService(lib_dir)
                job = await conv_svc.create_conversion_job(book_id, target_format="EPUB", source_format=source_fmt)
                await conv_svc.run_conversion_job(job.id)
                chosen_format = "EPUB"
                # Refresh format dict
                async with aiosqlite.connect(db_path) as db:
                    db.row_factory = aiosqlite.Row
                    cur = await db.execute("SELECT format, name FROM data WHERE book = ?", (book_id,))
                    format_rows = await cur.fetchall()
                    formats_dict = {r["format"].upper(): r["name"] for r in format_rows}
            else:
                available_fmts = list(formats_dict.keys())
                error_msg = f"No Kindle-compatible format found. Available formats: {available_fmts}"
                return await self.record_sync_log(
                    lib_dir,
                    book_id=book_id,
                    book_title=book_title,
                    device_type=device_type,
                    format_sent="UNKNOWN",
                    status=DeviceSyncStatus.FAILED,
                    device_id=device_id,
                    error_message=error_msg,
                )

        if chosen_format not in formats_dict:
            error_msg = f"Requested format {chosen_format} is not available for this book."
            return await self.record_sync_log(
                lib_dir,
                book_id=book_id,
                book_title=book_title,
                device_type=device_type,
                format_sent=chosen_format,
                status=DeviceSyncStatus.FAILED,
                device_id=device_id,
                error_message=error_msg,
            )

        format_file_name = formats_dict[chosen_format]
        book_file_path = lib_dir / book_rel_path / f"{format_file_name}.{chosen_format.lower()}"
        if not book_file_path.exists():
            # Fallback search in book folder
            matches = list((lib_dir / book_rel_path).glob(f"*.{chosen_format.lower()}"))
            if matches:
                book_file_path = matches[0]
            else:
                error_msg = f"Book format file {book_file_path.name} not found on disk."
                return await self.record_sync_log(
                    lib_dir,
                    book_id=book_id,
                    book_title=book_title,
                    device_type=device_type,
                    format_sent=chosen_format,
                    status=DeviceSyncStatus.FAILED,
                    device_id=device_id,
                    error_message=error_msg,
                )

        # 4. Dispatch Email
        clean_filename = f"{sanitize_filename(book_title)} - {sanitize_filename(first_author)}.{chosen_format.lower()}"
        try:
            await self.email_service.send_book_email(
                recipient=target_email,
                subject=book_title,
                file_path=book_file_path,
                filename=clean_filename,
                settings=smtp_settings,
            )
            if device_id:
                await self._update_device_last_sync(lib_dir, device_id)

            return await self.record_sync_log(
                lib_dir,
                book_id=book_id,
                book_title=book_title,
                device_type=device_type,
                format_sent=chosen_format,
                status=DeviceSyncStatus.COMPLETED,
                device_id=device_id,
            )
        except Exception as e:
            return await self.record_sync_log(
                lib_dir,
                book_id=book_id,
                book_title=book_title,
                device_type=device_type,
                format_sent=chosen_format,
                status=DeviceSyncStatus.FAILED,
                device_id=device_id,
                error_message=str(e),
            )

    async def export_to_directory(
        self,
        library_id: str,
        book_id: int,
        req: ExportToDirectoryRequest,
    ) -> str:
        """Exports a book file to a mounted USB drive or directory with Calibre naming."""
        lib_dir = await self._get_library_dir(library_id)
        db_path = lib_dir / "metadata.db"

        target_root = Path(req.target_directory)
        target_root.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT title, path, strftime('%Y', pubdate) as pub_year FROM books WHERE id = ?", (book_id,))
            book_row = await cur.fetchone()
            if not book_row:
                raise ValueError(f"Book with id {book_id} not found.")

            cur = await db.execute(
                "SELECT a.name FROM authors a JOIN books_authors_link bal ON a.id = bal.author WHERE bal.book = ?",
                (book_id,),
            )
            author_rows = await cur.fetchall()
            authors = [r["name"] for r in author_rows] or ["Unknown Author"]

            cur = await db.execute("SELECT format, name FROM data WHERE book = ?", (book_id,))
            format_rows = await cur.fetchall()
            formats_dict = {r["format"].upper(): r["name"] for r in format_rows}

        book_title = book_row["title"]
        book_rel_path = book_row["path"]
        first_author = authors[0]
        pub_year = book_row["pub_year"] or "Unknown"

        chosen_fmt = req.format.upper() if req.format else (list(formats_dict.keys())[0] if formats_dict else "EPUB")
        if chosen_fmt not in formats_dict:
            raise ValueError(f"Format {chosen_fmt} not available for book.")

        format_file_name = formats_dict[chosen_fmt]
        source_path = lib_dir / book_rel_path / f"{format_file_name}.{chosen_fmt.lower()}"
        if not source_path.exists():
            matches = list((lib_dir / book_rel_path).glob(f"*.{chosen_fmt.lower()}"))
            if matches:
                source_path = matches[0]
            else:
                raise FileNotFoundError(f"Source file for format {chosen_fmt} not found.")

        # Target template: {Author}/{Title} ({Year})/{Title} - {Author}.{ext}
        author_clean = sanitize_filename(first_author)
        title_clean = sanitize_filename(book_title)
        dest_dir = target_root / author_clean / f"{title_clean} ({pub_year})"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{title_clean} - {author_clean}.{chosen_fmt.lower()}"

        shutil.copy2(source_path, dest_path)

        # Calibre Save-to-Disk parity: include cover.jpg and metadata.opf if present
        source_dir = source_path.parent
        cover_src = source_dir / "cover.jpg"
        if cover_src.exists():
            try:
                shutil.copy2(cover_src, dest_dir / "cover.jpg")
            except Exception:
                pass
        opf_src = source_dir / "metadata.opf"
        if opf_src.exists():
            try:
                shutil.copy2(opf_src, dest_dir / "metadata.opf")
            except Exception:
                pass


        await self.record_sync_log(
            lib_dir,
            book_id=book_id,
            book_title=book_title,
            device_type=DeviceType.USB,
            format_sent=chosen_fmt,
            status=DeviceSyncStatus.COMPLETED,
        )
        return str(dest_path)
