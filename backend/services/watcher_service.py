"""Directory watcher service using watchfiles for automated intake processing."""

import asyncio
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Set
from watchfiles import Change, awatch

from backend.domain.entities import IngestionJob, IngestionStatus
from backend.parsers import ParserRegistry
from backend.services.ingestion_service import IngestionService
from backend.services.job_worker import JobManager

logger = logging.getLogger(__name__)


class WatcherService:
    """Monitors an intake directory and automatically ingests dropped book files."""

    def __init__(
        self,
        library_path: Path,
        import_dir: Path,
        library_id: Optional[str] = None,
    ):
        self.library_path = library_path
        self.import_dir = import_dir
        self.library_id = library_id
        self.db_path = library_path / "metadata.db"
        self.job_manager = JobManager(self.db_path)
        self.ingestion_service = IngestionService(library_path)
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None

    @property
    def supported_extensions(self) -> Set[str]:
        return ParserRegistry.get_supported_extensions()

    async def scan_once(self) -> List[IngestionJob]:
        """Scans the intake directory once for existing files and ingests them."""
        self.import_dir.mkdir(parents=True, exist_ok=True)
        jobs: List[IngestionJob] = []

        for item in self.import_dir.iterdir():
            if item.is_file() and item.suffix.lower() in self.supported_extensions:
                job = await self.process_file(item)
                jobs.append(job)

        return jobs

    async def process_file(self, file_path: Path) -> IngestionJob:
        """Processes a single file with job tracking."""
        job_id = uuid.uuid4().hex
        job = await self.job_manager.create_job(
            job_id=job_id,
            source_path=str(file_path),
            library_id=self.library_id,
        )

        await self.job_manager.update_status(job_id, IngestionStatus.PROCESSING)

        try:
            # Wait briefly for file write completion if dropped recently
            await asyncio.sleep(0.1)
            book = await self.ingestion_service.ingest_file(file_path)
            await self.job_manager.update_status(
                job_id, IngestionStatus.COMPLETED, book_id=book.id
            )
            job.status = IngestionStatus.COMPLETED
            job.book_id = book.id
        except Exception as e:
            logger.exception("Error ingesting file %s: %s", file_path, e)
            await self.job_manager.update_status(
                job_id, IngestionStatus.FAILED, error_message=str(e)
            )
            job.status = IngestionStatus.FAILED
            job.error_message = str(e)

        return job

    async def run(self) -> None:
        """Continuously watches the import folder until stopped."""
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self._stop_event.clear()

        # First scan existing files
        await self.scan_once()

        try:
            async for changes in awatch(self.import_dir, stop_event=self._stop_event):
                for change_type, path_str in changes:
                    if change_type in (Change.added, Change.modified):
                        file_path = Path(path_str)
                        if (
                            file_path.is_file()
                            and file_path.suffix.lower() in self.supported_extensions
                        ):
                            await self.process_file(file_path)
        except asyncio.CancelledError:
            pass

    def start(self) -> asyncio.Task:
        """Starts the watcher as an asynchronous background task."""
        self._task = asyncio.create_task(self.run())
        return self._task

    async def stop(self) -> None:
        """Stops the watcher task gracefully."""
        self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
