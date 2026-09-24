"""Directory watcher service using watchfiles and fallback polling for automated intake processing."""

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
from backend.services.post_ingestion import trigger_post_ingestion_pipeline

logger = logging.getLogger(__name__)


class WatcherService:
    """Monitors an intake directory and automatically ingests dropped book files."""

    def __init__(
        self,
        library_path: Path,
        import_dir: Path,
        library_id: Optional[str] = None,
        conflict_action: str = "merge",
        delete_source_after_import: bool = True,
        auto_download_metadata: bool = False,
        auto_index_rag: bool = False,
        auto_generate_summary: bool = False,
    ):
        self.library_path = library_path
        self.import_dir = import_dir
        self.library_id = library_id
        self.conflict_action = conflict_action
        self.delete_source_after_import = delete_source_after_import
        self.auto_download_metadata = auto_download_metadata
        self.auto_index_rag = auto_index_rag
        self.auto_generate_summary = auto_generate_summary

        self.db_path = library_path / "metadata.db"
        self.job_manager = JobManager(self.db_path)
        self.ingestion_service = IngestionService(library_path)
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._processing_files: Set[Path] = set()

    @property
    def supported_extensions(self) -> Set[str]:
        return ParserRegistry.get_supported_extensions()

    async def _wait_for_file_ready(self, file_path: Path, max_wait: float = 12.0) -> bool:
        """Ensures a file is fully written and unlocked before ingestion."""
        start = asyncio.get_event_loop().time()
        last_size = -1
        while (asyncio.get_event_loop().time() - start) < max_wait:
            if not file_path.exists():
                return False
            try:
                current_size = file_path.stat().st_size
                if current_size > 0 and current_size == last_size:
                    # Verify readable
                    with open(file_path, "rb") as f:
                        f.read(min(current_size, 4096))
                    return True
                last_size = current_size
            except (PermissionError, OSError):
                pass
            await asyncio.sleep(0.4)
        return False

    async def _safe_delete_file(self, file_path: Path) -> bool:
        """Removes a file from the drop folder after successful ingestion with Windows retry logic."""
        for attempt in range(10):
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info("Successfully deleted imported file from drop folder: %s", file_path)
                return True
            except PermissionError:
                # File might still be locked momentarily by parser or OS handle
                await asyncio.sleep(0.3)
            except Exception as e:
                logger.warning("Could not delete drop folder file %s: %s", file_path, e)
                break
        return False

    async def scan_once(self) -> List[IngestionJob]:
        """Scans the intake directory once for existing files and ingests them."""
        self.import_dir.mkdir(parents=True, exist_ok=True)
        jobs: List[IngestionJob] = []

        try:
            items = sorted(self.import_dir.iterdir(), key=lambda p: p.name)
        except Exception as e:
            logger.error("Failed to read drop folder directory %s: %s", self.import_dir, e)
            return jobs

        for item in items:
            if item.is_file() and item.suffix.lower() in self.supported_extensions:
                resolved = item.resolve()
                if resolved not in self._processing_files:
                    job = await self.process_file(item)
                    jobs.append(job)

        return jobs

    async def process_file(self, file_path: Path) -> IngestionJob:
        """Processes a single file with job tracking, removal, and post-ingestion workflows."""
        resolved_path = file_path.resolve()
        if resolved_path in self._processing_files:
            logger.debug("File %s is already being processed, skipping duplicate trigger.", resolved_path)
            return IngestionJob(
                id=uuid.uuid4().hex,
                source_path=str(resolved_path),
                status=IngestionStatus.PROCESSING,
            )

        self._processing_files.add(resolved_path)
        try:
            # 1. Wait for file write/lock stability
            is_ready = await self._wait_for_file_ready(file_path)
            if not is_ready:
                logger.warning("File %s was not ready or disappeared before processing.", file_path)
                return IngestionJob(
                    id=uuid.uuid4().hex,
                    source_path=str(file_path),
                    status=IngestionStatus.FAILED,
                    error_message="File not accessible or incomplete write",
                )

            job_id = uuid.uuid4().hex
            job = await self.job_manager.create_job(
                job_id=job_id,
                source_path=str(file_path),
                library_id=self.library_id,
            )

            await self.job_manager.update_status(job_id, IngestionStatus.PROCESSING)

            try:
                book = await self.ingestion_service.ingest_file(
                    file_path, conflict_action=self.conflict_action
                )
                await self.job_manager.update_status(job_id, IngestionStatus.COMPLETED, book_id=book.id)
                job.status = IngestionStatus.COMPLETED
                job.book_id = book.id

                # 2. Remove file from drop folder if configured
                if self.delete_source_after_import:
                    await self._safe_delete_file(file_path)

                # 3. Trigger automated post-ingestion tasks (metadata, RAG, summary)
                asyncio.create_task(
                    trigger_post_ingestion_pipeline(
                        book_id=book.id,
                        library_path=self.library_path,
                        library_id=self.library_id,
                        auto_download_metadata=self.auto_download_metadata,
                        auto_index_rag=self.auto_index_rag,
                        auto_generate_summary=self.auto_generate_summary,
                    )
                )
            except Exception as e:
                logger.exception("Error ingesting file %s: %s", file_path, e)
                await self.job_manager.update_status(
                    job_id, IngestionStatus.FAILED, error_message=str(e)
                )
                job.status = IngestionStatus.FAILED
                job.error_message = str(e)

            return job
        finally:
            self._processing_files.discard(resolved_path)

    async def run(self) -> None:
        """Continuously watches the import folder until stopped with event & polling hybrid."""
        self.import_dir.mkdir(parents=True, exist_ok=True)
        self._stop_event.clear()

        # First scan existing files on startup
        try:
            await self.scan_once()
        except Exception as e:
            logger.error("Error during initial drop folder scan: %s", e)

        # Start periodic fallback poll task (every 8s) for network drives or missed OS events
        async def periodic_poll():
            while not self._stop_event.is_set():
                try:
                    await asyncio.sleep(8)
                    if not self._stop_event.is_set() and self.import_dir.exists():
                        await self.scan_once()
                except asyncio.CancelledError:
                    break
                except Exception as ex:
                    logger.error("Periodic drop folder scan error: %s", ex)

        poll_task = asyncio.create_task(periodic_poll())

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
        except Exception as e:
            logger.error("Drop folder awatch encountered error: %s", e)
        finally:
            poll_task.cancel()
            try:
                await poll_task
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
