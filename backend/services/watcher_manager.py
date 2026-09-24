"""Singleton manager for the background drop folder watcher service."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from backend.config import ConfigManager
from backend.services.watcher_service import WatcherService

logger = logging.getLogger(__name__)


class DropFolderWatcherManager:
    """Manages the background drop folder watcher lifecycle."""

    def __init__(self):
        self._watcher: Optional[WatcherService] = None
        self._task: Optional[asyncio.Task] = None
        self._active_folder: Optional[str] = None
        self._active_library_id: Optional[str] = None
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def sync_with_config(self) -> None:
        """Starts, updates, or stops the watcher based on the current persisted configuration."""
        async with self._lock:
            cfg_mgr = ConfigManager()
            cfg = cfg_mgr.load()
            prefs = cfg.preferences
            active_lib = cfg_mgr.get_active_library()

            should_run = (
                prefs.auto_import_enabled
                and prefs.auto_import_folder
                and bool(prefs.auto_import_folder.strip())
                and active_lib is not None
            )

            if not should_run:
                if self.is_running:
                    logger.info("Stopping Drop Folder background watcher (disabled or unconfigured).")
                    await self._stop_internal()
                return

            folder_str = prefs.auto_import_folder.strip()
            folder_path = Path(folder_str)

            # Check if already running with exact same parameters
            if (
                self.is_running
                and self._active_folder == folder_str
                and self._active_library_id == active_lib.id
            ):
                logger.debug("Drop Folder watcher is already running for %s", folder_str)
                return

            # If running with different parameters, stop first
            if self.is_running:
                logger.info("Reconfiguring Drop Folder background watcher for new parameters.")
                await self._stop_internal()

            # Ensure folder exists
            try:
                folder_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed to create drop folder %s: %s", folder_path, e)
                return

            # Instantiate and start new watcher
            self._watcher = WatcherService(
                library_path=Path(active_lib.path),
                import_dir=folder_path,
                library_id=active_lib.id,
                conflict_action=prefs.auto_import_action,
                delete_source_after_import=prefs.delete_source_after_import,
                auto_download_metadata=prefs.auto_download_metadata,
                auto_index_rag=prefs.auto_index_rag,
                auto_generate_summary=prefs.auto_generate_summary,
            )
            self._active_folder = folder_str
            self._active_library_id = active_lib.id
            self._task = self._watcher.start()
            logger.info(
                "Started Drop Folder background watcher for '%s' -> library '%s' (delete_imported=%s, meta=%s, rag=%s, summary=%s)",
                folder_str,
                active_lib.name,
                prefs.delete_source_after_import,
                prefs.auto_download_metadata,
                prefs.auto_index_rag,
                prefs.auto_generate_summary,
            )

    async def stop(self) -> None:
        """Stops the watcher task gracefully."""
        async with self._lock:
            await self._stop_internal()

    async def _stop_internal(self) -> None:
        if self._watcher:
            await self._watcher.stop()
            self._watcher = None
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._active_folder = None
        self._active_library_id = None


# Global singleton instance
drop_folder_watcher_manager = DropFolderWatcherManager()
