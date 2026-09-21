import logging
import mimetypes
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Dict, List, Optional, Tuple

from backend.domain.reading import ComicManifest, ComicPageInfo
from backend.services.library_manager import LibraryManager

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


def natural_sort_key(s: str):
    """Sort strings with embedded numbers naturally (e.g. page_2 before page_10)."""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)]


class ComicService:
    """Provides comic and manga archive (CBZ/CBR) page extraction and streaming."""

    def __init__(self, library_manager: Optional[LibraryManager] = None):
        self.library_manager = library_manager or LibraryManager()
        # In-memory cache for page lists: (library_id, book_id) -> list of archive entry names
        self._manifest_cache: Dict[Tuple[str, int], List[str]] = {}

    def _get_comic_file_path(self, library_id: str, book_id: int) -> Optional[str]:
        """Locate the physical CBZ or CBR file path for a book."""
        db_mgr = self.library_manager.get_database_manager(library_id)
        # Query formats table in SQLite
        import sqlite3

        conn = sqlite3.connect(db_mgr.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                """
                SELECT f.format, f.name, b.path
                FROM data f
                JOIN books b ON b.id = f.book
                WHERE f.book = ? AND f.format IN ('CBZ', 'CBR')
                LIMIT 1
                """,
                (book_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            lib = self.library_manager.get_library(library_id)
            if not lib:
                return None

            filename = f"{row['name']}.{row['format'].lower()}"
            full_path = os.path.join(lib.path, row["path"], filename)
            if os.path.exists(full_path):
                return full_path

            # Also check uppercase extension
            alt_path = os.path.join(lib.path, row["path"], f"{row['name']}.{row['format'].upper()}")
            if os.path.exists(alt_path):
                return alt_path

            return None
        finally:
            conn.close()

    def get_manifest(self, library_id: str, book_id: int) -> ComicManifest:
        """Enumerate pages in comic archive and parse ComicInfo.xml if present."""
        cache_key = (library_id, book_id)
        file_path = self._get_comic_file_path(library_id, book_id)
        if not file_path or not os.path.exists(file_path):
            return ComicManifest(book_id=book_id, total_pages=0, pages=[])

        series_name = None
        issue_number = None

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                all_names = zf.namelist()

                # Filter image files (ignoring __MACOSX and hidden files)
                image_names = [
                    name
                    for name in all_names
                    if not name.startswith("__MACOSX")
                    and not os.path.basename(name).startswith(".")
                    and os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS
                ]
                image_names.sort(key=natural_sort_key)
                self._manifest_cache[cache_key] = image_names

                # Attempt to parse ComicInfo.xml
                comic_info_entry = next((n for n in all_names if n.lower() == "comicinfo.xml"), None)
                if comic_info_entry:
                    try:
                        xml_bytes = zf.read(comic_info_entry)
                        root = ET.fromstring(xml_bytes)
                        series_elem = root.find("Series")
                        if series_elem is not None and series_elem.text:
                            series_name = series_elem.text.strip()
                        num_elem = root.find("Number")
                        if num_elem is not None and num_elem.text:
                            try:
                                issue_number = float(num_elem.text.strip())
                            except Exception:
                                pass
                    except Exception as e:
                        logger.debug(f"Could not parse ComicInfo.xml: {e}")

                pages = [
                    ComicPageInfo(
                        index=idx,
                        filename=os.path.basename(name),
                        url=f"/api/libraries/{library_id}/books/{book_id}/comic/pages/{idx}",
                    )
                    for idx, name in enumerate(image_names)
                ]

                return ComicManifest(
                    book_id=book_id,
                    total_pages=len(pages),
                    pages=pages,
                    series_name=series_name,
                    issue_number=issue_number,
                )
        except zipfile.BadZipFile:
            logger.warning(f"File {file_path} is not a valid zip archive.")
            return ComicManifest(book_id=book_id, total_pages=0, pages=[])

    def get_page_image(
        self, library_id: str, book_id: int, page_index: int
    ) -> Optional[Tuple[bytes, str]]:
        """Retrieve binary bytes and MIME type for a specific page index."""
        cache_key = (library_id, book_id)
        if cache_key not in self._manifest_cache:
            manifest = self.get_manifest(library_id, book_id)
            if not manifest.pages:
                return None

        image_names = self._manifest_cache.get(cache_key, [])
        if page_index < 0 or page_index >= len(image_names):
            return None

        file_path = self._get_comic_file_path(library_id, book_id)
        if not file_path:
            return None

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                entry_name = image_names[page_index]
                image_bytes = zf.read(entry_name)
                mime_type, _ = mimetypes.guess_type(entry_name)
                if not mime_type:
                    mime_type = "image/jpeg"
                return image_bytes, mime_type
        except Exception as e:
            logger.error(f"Error reading comic page {page_index}: {e}")
            return None
