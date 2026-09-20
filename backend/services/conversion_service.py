import asyncio
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from backend.domain.conversion import (
    ConversionEngineUsed,
    ConversionJob,
    ConversionStatus,
)
from backend.domain.entities import Book
from backend.services.converters import CBZToPdfConverter, TxtToEpubConverter
from backend.services.ingestion_service import IngestionService
from backend.services.storage_service import StorageService, sanitize_filename


class ConversionService:
    """
    Orchestrates background book format conversions.
    Supports Calibre's ebook-convert CLI auto-detection with pure-Python fallbacks.
    """

    def __init__(self, library_path: Path):
        self.library_path = Path(library_path)
        self.db_path = self.library_path / "metadata.db"
        self.storage = StorageService(self.library_path)
        self.ingestion = IngestionService(self.library_path)
        self._jobs: Dict[str, ConversionJob] = {}

    def get_job(self, job_id: str) -> Optional[ConversionJob]:
        return self._jobs.get(job_id)

    def list_jobs(self, book_id: Optional[int] = None) -> List[ConversionJob]:
        if book_id is not None:
            return [j for j in self._jobs.values() if j.book_id == book_id]
        return list(self._jobs.values())

    async def get_book(self, book_id: int) -> Optional[Book]:
        if not self.db_path.exists():
            return None
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            try:
                return await self.ingestion._get_book_by_id(db, book_id)
            except Exception:
                return None

    async def create_conversion_job(
        self,
        book_id: int,
        target_format: str,
        source_format: Optional[str] = None,
    ) -> ConversionJob:
        book = await self.get_book(book_id)
        if not book:
            raise ValueError(f"Book not found: {book_id}")

        norm_target = target_format.upper().strip()

        # Find source format
        avail_formats = {f.format.upper(): f for f in book.formats}
        if source_format:
            norm_source = source_format.upper().strip()
            if norm_source not in avail_formats:
                raise ValueError(f"Book does not have requested source format: {source_format}")
            source_fmt_obj = avail_formats[norm_source]
        else:
            # Pick first available format that is not target_format
            candidates = [f for f in book.formats if f.format.upper() != norm_target]
            if not candidates:
                raise ValueError(f"No alternative source formats available to convert to {norm_target}")
            source_fmt_obj = candidates[0]

        job_id = f"conv-{uuid.uuid4()}"
        job = ConversionJob(
            id=job_id,
            book_id=book_id,
            library_id=self.library_path.name,
            source_format=source_fmt_obj.format.upper(),
            target_format=norm_target,
            status=ConversionStatus.PENDING,
            percent_complete=0,
            logs=["Conversion job queued"],
        )
        self._jobs[job_id] = job
        return job

    async def execute_conversion_async(self, job_id: str) -> ConversionJob:
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        job.status = ConversionStatus.PROCESSING
        job.percent_complete = 10
        job.logs.append("Fetching book source files from library storage...")

        try:
            book = await self.get_book(job.book_id)
            if not book:
                raise ValueError(f"Book {job.book_id} not found in library")

            # Resolve source file path
            source_fmt = next((f for f in book.formats if f.format.upper() == job.source_format), None)
            if not source_fmt:
                raise FileNotFoundError(f"Format {job.source_format} not found on book record")

            book_dir = self.library_path / book.path
            source_file = book_dir / f"{source_fmt.name}.{job.source_format.lower()}"
            if not source_file.exists():
                # Fallback search in book directory
                matches = list(book_dir.glob(f"*.{job.source_format.lower()}"))
                if matches:
                    source_file = matches[0]
                else:
                    raise FileNotFoundError(f"Source file {source_file} not found on disk")

            # Determine output file path
            output_filename = f"{book.title} - {', '.join(book.authors)}" if book.authors else book.title
            clean_output_name = sanitize_filename(output_filename)
            output_file = book_dir / f"{clean_output_name}.{job.target_format.lower()}"

            job.percent_complete = 30

            # Determine converter engine
            calibre_cli = shutil.which("ebook-convert")

            # Check if pure-Python converter applies
            is_cbz_to_pdf = job.source_format == "CBZ" and job.target_format == "PDF"
            is_txt_to_epub = job.source_format in ("TXT", "MD") and job.target_format == "EPUB"

            if (is_cbz_to_pdf or is_txt_to_epub) or not calibre_cli:
                job.engine_used = ConversionEngineUsed.PYTHON_NATIVE
                job.logs.append("Running native pure-Python converter...")
                job.percent_complete = 50

                if is_cbz_to_pdf:
                    CBZToPdfConverter.convert(source_file, output_file)
                elif is_txt_to_epub:
                    TxtToEpubConverter.convert(
                        source_file,
                        output_file,
                        title=book.title,
                        author=", ".join(book.authors) if book.authors else None,
                    )
                else:
                    if not calibre_cli:
                        raise RuntimeError(
                            f"Cannot convert {job.source_format} to {job.target_format}: Calibre ebook-convert is not installed and no pure-python converter is registered for this pair."
                        )
            else:
                job.engine_used = ConversionEngineUsed.CALIBRE_CLI
                job.logs.append(f"Executing Calibre CLI: ebook-convert '{source_file.name}' '{output_file.name}'")
                job.percent_complete = 40

                process = await asyncio.create_subprocess_exec(
                    calibre_cli,
                    str(source_file),
                    str(output_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0:
                    err_msg = stderr.decode(errors="replace")
                    raise RuntimeError(f"Calibre CLI conversion failed (code {process.returncode}): {err_msg}")

            job.percent_complete = 85
            job.logs.append("Registering converted format with library database...")

            # Register format with Calibre SQLite metadata.db
            file_size = output_file.stat().st_size
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO data (book, format, uncompressed_size, name)
                    VALUES (?, ?, ?, ?)
                    """,
                    (job.book_id, job.target_format, file_size, clean_output_name),
                )
                await db.commit()

            job.status = ConversionStatus.COMPLETED
            job.percent_complete = 100
            job.output_file_path = str(output_file)
            job.output_size_bytes = file_size
            job.completed_at = datetime.now(timezone.utc)
            job.logs.append(f"Conversion completed successfully: {job.target_format} ({file_size} bytes)")

        except Exception as e:
            job.status = ConversionStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            job.logs.append(f"Conversion error: {str(e)}")

        return job
