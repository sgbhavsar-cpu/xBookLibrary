"""Comprehensive metadata editing and Calibre library management service."""

import io
import logging
import shutil
from pathlib import Path
from typing import Dict, List

import aiosqlite
from PIL import Image

from backend.domain.entities import Book, BookFormat
from backend.domain.metadata_editor import (
    BookDeleteResponse,
    BookMetadataUpdateRequest,
    BulkDeleteRequest,
    BulkDeleteResult,
    BulkMetadataUpdateRequest,
    BulkMetadataUpdateResult,
    FormatAddResponse,
    FormatDeleteResponse,
)
from backend.services.opf_sync_service import OpfSyncService


logger = logging.getLogger(__name__)


class MetadataEditorService:
    """Handles Calibre SQLite metadata edits, cover updates, formats, and bulk updates."""

    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.db_path = library_path / "metadata.db"

    async def get_book_metadata(self, book_id: int) -> Book:
        """Loads a comprehensive Book entity from Calibre SQLite tables."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"metadata.db not found at {self.db_path}")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await self._ensure_tables(db)
            return await self._get_book_entity(db, book_id)

    async def _ensure_tables(self, db: aiosqlite.Connection) -> None:
        """Ensures optional Calibre tables exist."""
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rating INTEGER NOT NULL UNIQUE
            );
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS books_ratings_link (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                FOREIGN KEY(book) REFERENCES books(id) ON DELETE CASCADE,
                FOREIGN KEY(rating) REFERENCES ratings(id) ON DELETE CASCADE,
                UNIQUE(book, rating)
            );
            """
        )
        await db.commit()

    async def _get_book_entity(self, db: aiosqlite.Connection, book_id: int) -> Book:
        sql = (
            "SELECT id, title, sort, author_sort, pubdate, isbn, path, "
            "has_cover, uuid, series_index FROM books WHERE id = ?"
        )
        async with db.execute(sql, (book_id,)) as cur:
            b = await cur.fetchone()

        if not b:
            raise ValueError(f"Book with id {book_id} not found")

        # Authors
        authors = []
        async with db.execute(
            """
            SELECT a.name FROM authors a
            JOIN books_authors_link bal ON a.id = bal.author
            WHERE bal.book = ?
            ORDER BY bal.id ASC
            """,
            (book_id,),
        ) as cur:
            for r in await cur.fetchall():
                authors.append(r["name"])

        # Publisher
        publisher = None
        async with db.execute(
            """
            SELECT p.name FROM publishers p
            JOIN books_publishers_link bpl ON p.id = bpl.publisher
            WHERE bpl.book = ?
            """,
            (book_id,),
        ) as cur:
            row = await cur.fetchone()
            if row:
                publisher = row["name"]

        # Series & Series Index
        series_name = None
        series_index = (
            b["series_index"]
            if "series_index" in b.keys() and b["series_index"] is not None
            else 1.0
        )
        async with db.execute(
            """
            SELECT s.name FROM series s
            JOIN books_series_link bsl ON s.id = bsl.series
            WHERE bsl.book = ?
            """,
            (book_id,),
        ) as cur:
            row = await cur.fetchone()
            if row:
                series_name = row["name"]

        # Rating
        rating = None
        async with db.execute(
            """
            SELECT r.rating FROM ratings r
            JOIN books_ratings_link brl ON r.id = brl.rating
            WHERE brl.book = ?
            """,
            (book_id,),
        ) as cur:
            row = await cur.fetchone()
            if row:
                rating = row["rating"]

        # Tags
        tags = []
        async with db.execute(
            """
            SELECT t.name FROM tags t
            JOIN books_tags_link btl ON t.id = btl.tag
            WHERE btl.book = ?
            ORDER BY t.name ASC
            """,
            (book_id,),
        ) as cur:
            for r in await cur.fetchall():
                tags.append(r["name"])

        # Description / Comments
        description = None
        async with db.execute("SELECT text FROM comments WHERE book = ?", (book_id,)) as cur:
            row = await cur.fetchone()
            if row:
                description = row["text"]

        # Identifiers
        identifiers: Dict[str, str] = {}
        async with db.execute(
            "SELECT type, val FROM identifiers WHERE book = ?", (book_id,)
        ) as cur:
            for r in await cur.fetchall():
                identifiers[r["type"]] = r["val"]

        # Formats
        formats: List[BookFormat] = []
        async with db.execute(
            "SELECT id, format, uncompressed_size, name FROM data WHERE book = ?", (book_id,)
        ) as cur:
            for r in await cur.fetchall():
                fmt = r["format"]
                fmt_name = r["name"]
                formats.append(
                    BookFormat(
                        id=r["id"],
                        book_id=book_id,
                        format=fmt,
                        uncompressed_size=r["uncompressed_size"],
                        name=fmt_name,
                        file_path=f"{b['path']}/{fmt_name}.{fmt.lower()}",
                    )
                )

        pub_year = None
        if b["pubdate"]:
            try:
                pub_year = int(str(b["pubdate"])[:4])
            except (ValueError, TypeError):
                pass

        custom_values = {}
        if rating is not None:
            custom_values["rating"] = rating

        return Book(
            id=book_id,
            title=b["title"],
            sort_title=b["sort"],
            authors=authors,
            publisher=publisher,
            publication_year=pub_year,
            isbn=b["isbn"],
            path=b["path"],
            has_cover=bool(b["has_cover"]),
            formats=formats,
            tags=tags,
            series_name=series_name,
            series_index=series_index,
            identifiers=identifiers,
            description=description,
            custom_values=custom_values,
            uuid=b["uuid"],
        )

    async def update_book_metadata(self, book_id: int, req: BookMetadataUpdateRequest) -> Book:
        """Transactionally updates book metadata across Calibre normalized SQLite tables."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"metadata.db not found at {self.db_path}")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await self._ensure_tables(db)

            # Verify book exists
            async with db.execute(
                "SELECT id, path, title, sort FROM books WHERE id = ?", (book_id,)
            ) as cur:
                book_row = await cur.fetchone()
            if not book_row:
                raise ValueError(f"Book {book_id} does not exist")

            # 1. Update Title and Title Sort
            if req.title is not None:
                sort_val = req.sort_title if req.sort_title is not None else req.title
                await db.execute(
                    "UPDATE books SET title = ?, sort = ?, "
                    "last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (req.title, sort_val, book_id),
                )
            elif req.sort_title is not None:
                await db.execute(
                    "UPDATE books SET sort = ?, last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (req.sort_title, book_id),
                )

            # 2. Update Authors & Author Sort
            if req.authors is not None:
                await db.execute("DELETE FROM books_authors_link WHERE book = ?", (book_id,))
                for author_name in req.authors:
                    clean_name = author_name.strip()
                    if clean_name:
                        author_id = await self._get_or_create_author(db, clean_name)
                        await db.execute(
                            "INSERT OR IGNORE INTO books_authors_link (book, author) VALUES (?, ?)",
                            (book_id, author_id),
                        )
                primary_author = (
                    req.authors[0].strip() if req.authors and req.authors[0].strip() else "Unknown"
                )
                author_sort = req.author_sort if req.author_sort is not None else primary_author
                await db.execute(
                    "UPDATE books SET author_sort = ?, "
                    "last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (author_sort, book_id),
                )
            elif req.author_sort is not None:
                await db.execute(
                    "UPDATE books SET author_sort = ?, "
                    "last_modified = CURRENT_TIMESTAMP WHERE id = ?",
                    (req.author_sort, book_id),
                )

            # 3. Update Publisher
            if req.publisher is not None:
                await db.execute("DELETE FROM books_publishers_link WHERE book = ?", (book_id,))
                clean_pub = req.publisher.strip()
                if clean_pub:
                    pub_id = await self._get_or_create_publisher(db, clean_pub)
                    await db.execute(
                        "INSERT OR IGNORE INTO books_publishers_link "
                        "(book, publisher) VALUES (?, ?)",
                        (book_id, pub_id),
                    )

            # 4. Update Publication Date
            if req.pubdate is not None:
                clean_date = req.pubdate.strip()
                if clean_date:
                    formatted_date = (
                        f"{clean_date}-01-01"
                        if len(clean_date) == 4 and clean_date.isdigit()
                        else clean_date
                    )
                    await db.execute(
                        "UPDATE books SET pubdate = ? WHERE id = ?", (formatted_date, book_id)
                    )
                else:
                    await db.execute("UPDATE books SET pubdate = NULL WHERE id = ?", (book_id,))

            # 5. Update Rating
            if req.rating is not None:
                await db.execute("DELETE FROM books_ratings_link WHERE book = ?", (book_id,))
                if req.rating > 0:
                    rating_id = await self._get_or_create_rating(db, req.rating)
                    await db.execute(
                        "INSERT OR IGNORE INTO books_ratings_link (book, rating) VALUES (?, ?)",
                        (book_id, rating_id),
                    )

            # 6. Update Tags
            if req.tags is not None:
                await db.execute("DELETE FROM books_tags_link WHERE book = ?", (book_id,))
                for tag in req.tags:
                    clean_tag = tag.strip()
                    if clean_tag:
                        tag_id = await self._get_or_create_tag(db, clean_tag)
                        await db.execute(
                            "INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (?, ?)",
                            (book_id, tag_id),
                        )

            # 7. Update Series & Series Index
            if req.series_name is not None:
                await db.execute("DELETE FROM books_series_link WHERE book = ?", (book_id,))
                clean_series = req.series_name.strip()
                if clean_series:
                    series_id = await self._get_or_create_series(db, clean_series)
                    await db.execute(
                        "INSERT OR IGNORE INTO books_series_link (book, series) VALUES (?, ?)",
                        (book_id, series_id),
                    )
                    idx = req.series_index if req.series_index is not None else 1.0
                    await db.execute(
                        "UPDATE books SET series_index = ? WHERE id = ?", (idx, book_id)
                    )
                else:
                    await db.execute("UPDATE books SET series_index = 1.0 WHERE id = ?", (book_id,))
            elif req.series_index is not None:
                await db.execute(
                    "UPDATE books SET series_index = ? WHERE id = ?", (req.series_index, book_id)
                )

            # 8. Update ISBN
            if req.isbn is not None:
                await db.execute(
                    "UPDATE books SET isbn = ? WHERE id = ?", (req.isbn.strip() or None, book_id)
                )

            # 9. Update Identifiers
            if req.identifiers is not None:
                await db.execute("DELETE FROM identifiers WHERE book = ?", (book_id,))
                for id_type, id_val in req.identifiers.items():
                    if id_type.strip() and id_val.strip():
                        await db.execute(
                            "INSERT OR REPLACE INTO identifiers (book, type, val) VALUES (?, ?, ?)",
                            (book_id, id_type.strip().lower(), id_val.strip()),
                        )

            # 10. Update Comments / Description
            if req.comments is not None:
                await db.execute("DELETE FROM comments WHERE book = ?", (book_id,))
                if req.comments.strip():
                    await db.execute(
                        "INSERT INTO comments (book, text) VALUES (?, ?)",
                        (book_id, req.comments.strip()),
                    )

            await db.commit()

            # Retrieve updated book
            book = await self._get_book_entity(db, book_id)

        # 11. Synchronize metadata.opf
        try:
            book_dir = self.library_path / book.path
            OpfSyncService.sync_opf_file(book_dir, book)
        except Exception as e:
            logger.warning(f"Could not synchronize metadata.opf for book {book_id}: {e}")

        return book

    async def save_book_cover(self, book_id: int, image_bytes: bytes) -> bool:
        """Normalizes and replaces cover.jpg in the book folder and updates has_cover."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await self._ensure_tables(db)
            async with db.execute("SELECT path FROM books WHERE id = ?", (book_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError(f"Book {book_id} not found")

            book_dir = self.library_path / row["path"]
            book_dir.mkdir(parents=True, exist_ok=True)
            cover_path = book_dir / "cover.jpg"

            # Normalize image to RGB JPEG using Pillow
            with Image.open(io.BytesIO(image_bytes)) as img:
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(cover_path, "JPEG", quality=90)

            await db.execute("UPDATE books SET has_cover = 1 WHERE id = ?", (book_id,))
            await db.commit()

            # Retrieve book and update metadata.opf
            book = await self._get_book_entity(db, book_id)

        try:
            OpfSyncService.sync_opf_file(book_dir, book)
        except Exception as e:
            logger.warning(f"Could not sync metadata.opf after cover save: {e}")

        return True

    async def attach_format(
        self, book_id: int, format_name: str, filename_base: str, file_bytes: bytes
    ) -> FormatAddResponse:
        """Attaches a new format file to an existing book container."""
        fmt_upper = format_name.upper().lstrip(".")
        ext = fmt_upper.lower()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT path FROM books WHERE id = ?", (book_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError(f"Book {book_id} not found")

            book_dir = self.library_path / row["path"]
            book_dir.mkdir(parents=True, exist_ok=True)

            clean_name = filename_base or f"book_{book_id}"
            dest_file = book_dir / f"{clean_name}.{ext}"

            # Write file
            dest_file.write_bytes(file_bytes)
            uncompressed_size = len(file_bytes)

            # Insert or replace into data table
            await db.execute("DELETE FROM data WHERE book = ? AND format = ?", (book_id, fmt_upper))
            await db.execute(
                "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, ?, ?, ?)",
                (book_id, fmt_upper, uncompressed_size, clean_name),
            )
            await db.commit()

            # Gather all current formats
            formats: List[str] = []
            async with db.execute("SELECT format FROM data WHERE book = ?", (book_id,)) as cur:
                for r in await cur.fetchall():
                    formats.append(r["format"])

        return FormatAddResponse(
            book_id=book_id,
            format=fmt_upper,
            file_path=f"{row['path']}/{clean_name}.{ext}",
            uncompressed_size=uncompressed_size,
            formats=formats,
        )

    async def delete_format(self, book_id: int, format_name: str) -> FormatDeleteResponse:
        """Deletes a specific format from disk and removes its record from the data table."""
        fmt_upper = format_name.upper().lstrip(".")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT path FROM books WHERE id = ?", (book_id,)) as cur:
                b_row = await cur.fetchone()
            if not b_row:
                raise ValueError(f"Book {book_id} not found")

            async with db.execute(
                "SELECT name, format FROM data WHERE book = ? AND format = ?", (book_id, fmt_upper)
            ) as cur:
                d_row = await cur.fetchone()

            if not d_row:
                raise ValueError(f"Format {fmt_upper} not found for book {book_id}")

            book_dir = self.library_path / b_row["path"]
            file_path = book_dir / f"{d_row['name']}.{fmt_upper.lower()}"
            if file_path.exists():
                file_path.unlink()

            await db.execute("DELETE FROM data WHERE book = ? AND format = ?", (book_id, fmt_upper))
            await db.commit()

            # Gather remaining formats
            remaining: List[str] = []
            async with db.execute("SELECT format FROM data WHERE book = ?", (book_id,)) as cur:
                for r in await cur.fetchall():
                    remaining.append(r["format"])

        return FormatDeleteResponse(
            book_id=book_id,
            deleted_format=fmt_upper,
            remaining_formats=remaining,
        )

    async def bulk_update_books(self, req: BulkMetadataUpdateRequest) -> BulkMetadataUpdateResult:
        """Batch-updates multiple books with shared tags, authors, publishers, or series."""
        total = len(req.book_ids)
        updated = 0
        failed: List[int] = []
        errors: List[str] = []

        current_series_idx = req.series_start_index

        for idx, book_id in enumerate(req.book_ids):
            try:
                # Prepare single-book update request
                single_req = BookMetadataUpdateRequest()

                if req.set_author:
                    single_req.authors = [req.set_author]
                if req.set_publisher:
                    single_req.publisher = req.set_publisher
                if req.set_rating is not None:
                    single_req.rating = req.set_rating

                if req.set_series:
                    single_req.series_name = req.set_series
                    if req.auto_increment_series:
                        single_req.series_index = current_series_idx + idx
                    else:
                        single_req.series_index = req.series_start_index

                # Fetch current book to merge tags if necessary
                if req.add_tags or req.remove_tags:
                    current_book = await self.get_book_metadata(book_id)
                    current_tags = set(current_book.tags or [])
                    # Add tags
                    for t in req.add_tags:
                        if t.strip():
                            current_tags.add(t.strip())
                    # Remove tags
                    for t in req.remove_tags:
                        current_tags.discard(t.strip())
                    single_req.tags = list(current_tags)

                await self.update_book_metadata(book_id, single_req)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to bulk update book {book_id}: {e}")
                failed.append(book_id)
                errors.append(f"Book {book_id}: {str(e)}")

        return BulkMetadataUpdateResult(
            total_requested=total,
            updated_count=updated,
            failed_ids=failed,
            errors=errors,
        )

    async def delete_book(self, book_id: int) -> BookDeleteResponse:
        """Completely deletes a book from Calibre SQLite database, vector index, and filesystem."""
        if not self.db_path.exists():
            raise FileNotFoundError(f"metadata.db not found at {self.db_path}")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON;")

            # 1. Fetch book path and title
            async with db.execute("SELECT title, path FROM books WHERE id = ?", (book_id,)) as cur:
                row = await cur.fetchone()
            if not row:
                raise ValueError(f"Book with id {book_id} not found")

            title = row["title"]
            rel_path = row["path"]

            # 2. Delete relations & metadata links
            link_tables = [
                "books_authors_link",
                "books_tags_link",
                "books_series_link",
                "books_publishers_link",
                "books_ratings_link",
                "books_languages_link",
                "books_plugin_data",
            ]
            for tbl in link_tables:
                try:
                    await db.execute(f"DELETE FROM {tbl} WHERE book = ?", (book_id,))
                except Exception:
                    pass

            # Check for custom column tables
            try:
                async with db.execute("SELECT id FROM custom_columns") as cur:
                    custom_cols = await cur.fetchall()
                    for col in custom_cols:
                        try:
                            await db.execute(f"DELETE FROM custom_column_{col['id']} WHERE book = ?", (book_id,))
                        except Exception:
                            pass
            except Exception:
                pass

            # Delete data, comments, identifiers
            await db.execute("DELETE FROM data WHERE book = ?", (book_id,))
            await db.execute("DELETE FROM comments WHERE book = ?", (book_id,))
            await db.execute("DELETE FROM identifiers WHERE book = ?", (book_id,))

            # Clean index status table if present
            try:
                await db.execute("DELETE FROM x_index_status WHERE book_id = ?", (book_id,))
            except Exception:
                pass

            # 3. Delete book record itself
            await db.execute("DELETE FROM books WHERE id = ?", (book_id,))

            # 4. Prune orphaned lookup records
            await db.execute("DELETE FROM authors WHERE id NOT IN (SELECT DISTINCT author FROM books_authors_link)")
            await db.execute("DELETE FROM tags WHERE id NOT IN (SELECT DISTINCT tag FROM books_tags_link)")
            await db.execute("DELETE FROM series WHERE id NOT IN (SELECT DISTINCT series FROM books_series_link)")
            await db.execute("DELETE FROM publishers WHERE id NOT IN (SELECT DISTINCT publisher FROM books_publishers_link)")
            try:
                await db.execute("DELETE FROM ratings WHERE id NOT IN (SELECT DISTINCT rating FROM books_ratings_link)")
            except Exception:
                pass

            await db.commit()

        # 5. Remove vector embeddings from LanceDB (if any)
        try:
            vector_dir = self.library_path / ".vectors"
            if vector_dir.exists():
                import lancedb
                ldb = lancedb.connect(str(vector_dir))
                tables_res = ldb.list_tables()
                existing_tables = (
                    tables_res.tables if hasattr(tables_res, "tables") else list(ldb.table_names())
                )
                if "book_chunks" in existing_tables:
                    tbl = ldb.open_table("book_chunks")
                    if tbl.count_rows() > 0:
                        tbl.delete(f"book_id = {book_id}")
        except Exception as e:
            logger.warning(f"Could not remove LanceDB vectors for book {book_id}: {e}")

        # 6. Delete book directory on filesystem
        deleted_from_disk = False
        if rel_path:
            book_dir = self.library_path / rel_path
            try:
                if book_dir.exists():
                    shutil.rmtree(book_dir, ignore_errors=True)
                    deleted_from_disk = True

                # Check if author parent dir is empty; if so, remove it
                author_dir = book_dir.parent
                if author_dir.exists() and author_dir.resolve() != self.library_path.resolve():
                    try:
                        if not any(author_dir.iterdir()):
                            author_dir.rmdir()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"Error deleting book files on disk at {book_dir}: {e}")

        return BookDeleteResponse(
            book_id=book_id,
            title=title,
            deleted_from_disk=deleted_from_disk,
            status="deleted",
        )

    async def bulk_delete_books(self, req: BulkDeleteRequest) -> BulkDeleteResult:
        """Batch-deletes multiple books from database and disk."""
        total = len(req.book_ids)
        deleted = 0
        failed: List[int] = []
        errors: List[str] = []

        for book_id in req.book_ids:
            try:
                await self.delete_book(book_id)
                deleted += 1
            except Exception as e:
                logger.error(f"Failed to delete book {book_id}: {e}")
                failed.append(book_id)
                errors.append(f"Book {book_id}: {str(e)}")

        return BulkDeleteResult(
            total_requested=total,
            deleted_count=deleted,
            failed_ids=failed,
            errors=errors,
        )

    # ------------------ Relational Lookup Helpers ------------------

    async def _get_or_create_author(self, db: aiosqlite.Connection, name: str) -> int:
        async with db.execute("SELECT id FROM authors WHERE name = ?", (name,)) as cur:
            row = await cur.fetchone()
            if row:
                return row["id"]
        cur = await db.execute("INSERT INTO authors (name, sort) VALUES (?, ?)", (name, name))
        return cur.lastrowid

    async def _get_or_create_tag(self, db: aiosqlite.Connection, name: str) -> int:
        async with db.execute("SELECT id FROM tags WHERE name = ?", (name,)) as cur:
            row = await cur.fetchone()
            if row:
                return row["id"]
        cur = await db.execute("INSERT INTO tags (name) VALUES (?)", (name,))
        return cur.lastrowid

    async def _get_or_create_publisher(self, db: aiosqlite.Connection, name: str) -> int:
        async with db.execute("SELECT id FROM publishers WHERE name = ?", (name,)) as cur:
            row = await cur.fetchone()
            if row:
                return row["id"]
        cur = await db.execute("INSERT INTO publishers (name, sort) VALUES (?, ?)", (name, name))
        return cur.lastrowid

    async def _get_or_create_series(self, db: aiosqlite.Connection, name: str) -> int:
        async with db.execute("SELECT id FROM series WHERE name = ?", (name,)) as cur:
            row = await cur.fetchone()
            if row:
                return row["id"]
        cur = await db.execute("INSERT INTO series (name, sort) VALUES (?, ?)", (name, name))
        return cur.lastrowid

    async def _get_or_create_rating(self, db: aiosqlite.Connection, rating: int) -> int:
        async with db.execute("SELECT id FROM ratings WHERE rating = ?", (rating,)) as cur:
            row = await cur.fetchone()
            if row:
                return row["id"]
        cur = await db.execute("INSERT INTO ratings (rating) VALUES (?)", (rating,))
        return cur.lastrowid
