"""Ingestion service for single and batch book files with smart deduplication."""

import hashlib
import shutil
import uuid
from pathlib import Path
from typing import Optional

import aiosqlite

from backend.domain.entities import Book, BookFormat, TocNode
from backend.domain.parsers import ParsedBookPayload
from backend.parsers import ParserRegistry
from backend.services.storage_service import StorageService, sanitize_filename


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash of a file efficiently using chunks."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class IngestionService:
    """Handles parsing, file layout placement, SQLite persistence, and format merging."""

    def __init__(self, library_root: Path):
        self.library_root = library_root
        self.db_path = library_root / "metadata.db"
        self.storage = StorageService(library_root)

    async def find_duplicate(self, source_file: Path) -> Optional[dict]:
        """Detects whether a source file matches an existing library book before ingestion."""
        if not source_file.exists():
            return None

        file_hash = compute_sha256(source_file)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT book_id FROM x_file_hashes WHERE sha256 = ?", (file_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    b = await self._get_book_by_id(db, row["book_id"])
                    return {
                        "matched_by": "hash",
                        "book_id": b.id,
                        "title": b.title,
                        "authors": b.authors,
                        "existing_formats": [f.format for f in b.formats],
                    }

        try:
            parser = ParserRegistry.get_parser(source_file)
            payload = parser.parse(source_file)
            primary_author = payload.authors[0] if payload.authors else "Unknown Author"
            title = payload.title or source_file.stem
            isbn = payload.identifiers.get("isbn")

            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                existing_book_id = None
                matched_by = "title_author"

                if isbn:
                    async with db.execute(
                        "SELECT book FROM identifiers WHERE type='isbn' AND val = ?", (isbn,)
                    ) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            existing_book_id = row["book"]
                            matched_by = "isbn"

                if not existing_book_id:
                    query = """
                    SELECT b.id FROM books b
                    JOIN books_authors_link bal ON b.id = bal.book
                    JOIN authors a ON bal.author = a.id
                    WHERE lower(b.title) = lower(?) AND lower(a.name) = lower(?)
                    """
                    async with db.execute(query, (title, primary_author)) as cursor:
                        row = await cursor.fetchone()
                        if row:
                            existing_book_id = row["id"]

                if existing_book_id:
                    b = await self._get_book_by_id(db, existing_book_id)
                    return {
                        "matched_by": matched_by,
                        "book_id": b.id,
                        "title": b.title,
                        "authors": b.authors,
                        "existing_formats": [f.format for f in b.formats],
                    }
        except Exception:
            pass

        return None

    async def ingest_file(
        self,
        source_file: Path,
        conflict_action: str = "merge",
    ) -> Book:
        """Ingests a book file into the library with conflict resolution
        ('merge', 'create_new', or 'skip')."""
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")

        file_hash = compute_sha256(source_file)
        file_size = source_file.stat().st_size
        ext = source_file.suffix.lower()
        format_name = ext.lstrip(".").upper()

        # 1. Check for byte-identical duplicate via x_file_hashes
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT book_id FROM x_file_hashes WHERE sha256 = ?", (file_hash,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    book_id = row["book_id"]
                    return await self._get_book_by_id(db, book_id)

        # 2. Parse file using appropriate parser
        parser = ParserRegistry.get_parser(source_file)
        payload = parser.parse(source_file)

        primary_author = payload.authors[0] if payload.authors else "Unknown Author"
        title = payload.title or source_file.stem
        isbn = payload.identifiers.get("isbn")

        # 3. Check if book already exists (by ISBN or Title + Primary Author)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            existing_book_id: Optional[int] = None

            if isbn:
                async with db.execute(
                    "SELECT book FROM identifiers WHERE type='isbn' AND val = ?", (isbn,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        existing_book_id = row["book"]

            if not existing_book_id:
                query = """
                SELECT b.id FROM books b
                JOIN books_authors_link bal ON b.id = bal.book
                JOIN authors a ON bal.author = a.id
                WHERE lower(b.title) = lower(?) AND lower(a.name) = lower(?)
                """
                async with db.execute(query, (title, primary_author)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        existing_book_id = row["id"]

            if existing_book_id:
                if conflict_action == "skip":
                    return await self._get_book_by_id(db, existing_book_id)
                elif conflict_action == "create_new":
                    return await self._create_book(
                        db,
                        source_file,
                        format_name,
                        file_hash,
                        file_size,
                        payload,
                        primary_author,
                        title,
                    )
                else:  # merge
                    return await self._merge_format(
                        db,
                        existing_book_id,
                        source_file,
                        format_name,
                        file_hash,
                        file_size,
                        payload,
                    )
            else:
                # Create brand new book
                return await self._create_book(
                    db,
                    source_file,
                    format_name,
                    file_hash,
                    file_size,
                    payload,
                    primary_author,
                    title,
                )

    async def _merge_format(
        self,
        db: aiosqlite.Connection,
        book_id: int,
        source_file: Path,
        format_name: str,
        file_hash: str,
        file_size: int,
        payload: ParsedBookPayload,
    ) -> Book:
        """Attaches a new file format to an existing book record."""
        async with db.execute(
            "SELECT path, title, author_sort FROM books WHERE id = ?", (book_id,)
        ) as cur:
            b_row = await cur.fetchone()
            rel_path = b_row["path"]

        dest_dir = self.library_root / rel_path
        dest_dir.mkdir(parents=True, exist_ok=True)

        clean_title = sanitize_filename(payload.title or "book")
        clean_author = sanitize_filename(payload.authors[0] if payload.authors else "author")
        dest_filename_base = f"{clean_title} - {clean_author}"
        dest_file = dest_dir / f"{dest_filename_base}.{format_name.lower()}"

        # Copy file into book directory
        shutil.copy2(source_file, dest_file)

        # Check if format record already exists in `data`
        async with db.execute(
            "SELECT id FROM data WHERE book = ? AND format = ?", (book_id, format_name)
        ) as cur:
            d_row = await cur.fetchone()
            if d_row:
                await db.execute(
                    "UPDATE data SET uncompressed_size = ?, name = ? WHERE id = ?",
                    (file_size, dest_filename_base, d_row["id"]),
                )
            else:
                await db.execute(
                    "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, ?, ?, ?)",
                    (book_id, format_name, file_size, dest_filename_base),
                )

        # Record hash
        await db.execute(
            """
            INSERT OR REPLACE INTO x_file_hashes (book_id, format, sha256, file_path)
            VALUES (?, ?, ?, ?)
            """,
            (book_id, format_name, file_hash, str(dest_file)),
        )

        await db.commit()
        book = await self._get_book_by_id(db, book_id)
        # Update metadata.opf
        self.storage.write_metadata_opf(dest_dir, book)
        return book

    async def _create_book(
        self,
        db: aiosqlite.Connection,
        source_file: Path,
        format_name: str,
        file_hash: str,
        file_size: int,
        payload: ParsedBookPayload,
        primary_author: str,
        title: str,
    ) -> Book:
        """Creates a new book record, Calibre directory structure, and metadata."""
        rel_dir = self.storage.get_book_relative_dir(
            primary_author, title, payload.publication_year
        )
        base_rel_dir = rel_dir
        counter = 1
        while (self.library_root / rel_dir).exists():
            rel_dir = f"{base_rel_dir} ({counter})"
            counter += 1
        dest_dir = self.library_root / rel_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        clean_title = sanitize_filename(title)
        clean_author = sanitize_filename(primary_author)
        dest_filename_base = f"{clean_title} - {clean_author}"
        dest_file = dest_dir / f"{dest_filename_base}.{format_name.lower()}"

        shutil.copy2(source_file, dest_file)

        # Save Cover if available
        has_cover = 0
        if payload.cover_bytes:
            saved = self.storage.save_cover_image(dest_dir, payload.cover_bytes)
            has_cover = 1 if saved else 0

        # Insert or retrieve author
        author_id = await self._get_or_create_author(db, primary_author)

        # Insert Book
        book_uuid = str(uuid.uuid4())
        isbn = payload.identifiers.get("isbn")
        pubdate = f"{payload.publication_year}-01-01" if payload.publication_year else None

        cursor = await db.execute(
            """
            INSERT INTO books (title, sort, author_sort, pubdate, isbn, path, has_cover, uuid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, title, primary_author, pubdate, isbn, rel_dir, has_cover, book_uuid),
        )
        book_id = cursor.lastrowid

        # Link Author
        await db.execute(
            "INSERT OR IGNORE INTO books_authors_link (book, author) VALUES (?, ?)",
            (book_id, author_id),
        )

        # Insert Data format
        await db.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, ?, ?, ?)",
            (book_id, format_name, file_size, dest_filename_base),
        )

        # Insert Identifiers
        for id_type, id_val in payload.identifiers.items():
            await db.execute(
                "INSERT OR IGNORE INTO identifiers (book, type, val) VALUES (?, ?, ?)",
                (book_id, id_type, id_val),
            )

        # Insert Tags
        for tag in payload.tags:
            tag_id = await self._get_or_create_tag(db, tag)
            await db.execute(
                "INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (?, ?)",
                (book_id, tag_id),
            )

        # Insert Publisher if present
        if payload.publisher:
            pub_id = await self._get_or_create_publisher(db, payload.publisher)
            await db.execute(
                "INSERT OR IGNORE INTO books_publishers_link (book, publisher) VALUES (?, ?)",
                (book_id, pub_id),
            )

        # Insert Comments / Description
        if payload.description:
            await db.execute(
                "INSERT OR REPLACE INTO comments (book, text) VALUES (?, ?)",
                (book_id, payload.description),
            )

        # Insert Table of Contents into x_toc_nodes
        for idx, toc_item in enumerate(payload.table_of_contents):
            await db.execute(
                """
                INSERT INTO x_toc_nodes
                (book_id, title, level, page_number, anchor_href, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    book_id,
                    toc_item.title,
                    toc_item.level,
                    toc_item.page_number,
                    toc_item.anchor_href,
                    idx,
                ),
            )

        # Insert File Hash
        await db.execute(
            """
            INSERT INTO x_file_hashes (book_id, format, sha256, file_path)
            VALUES (?, ?, ?, ?)
            """,
            (book_id, format_name, file_hash, str(dest_file)),
        )

        await db.commit()
        book = await self._get_book_by_id(db, book_id)

        # Write metadata.opf
        self.storage.write_metadata_opf(dest_dir, book)
        return book

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

    async def _get_book_by_id(self, db: aiosqlite.Connection, book_id: int) -> Book:
        async with db.execute(
            "SELECT id, title, sort, pubdate, isbn, path, has_cover FROM books WHERE id = ?",
            (book_id,),
        ) as cur:
            b = await cur.fetchone()

        # Authors
        authors = []
        author_query = (
            "SELECT a.name FROM authors a "
            "JOIN books_authors_link bal ON a.id = bal.author "
            "WHERE bal.book = ?"
        )
        async with db.execute(author_query, (book_id,)) as cur:
            for r in await cur.fetchall():
                authors.append(r["name"])

        # Publisher
        publisher = None
        pub_query = (
            "SELECT p.name FROM publishers p "
            "JOIN books_publishers_link bpl ON p.id = bpl.publisher "
            "WHERE bpl.book = ?"
        )
        async with db.execute(pub_query, (book_id,)) as cur:
            p_row = await cur.fetchone()
            if p_row:
                publisher = p_row["name"]

        # Formats
        formats = []
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

        # Tags
        tags = []
        tag_query = (
            "SELECT t.name FROM tags t "
            "JOIN books_tags_link btl ON t.id = btl.tag "
            "WHERE btl.book = ?"
        )
        async with db.execute(tag_query, (book_id,)) as cur:
            for r in await cur.fetchall():
                tags.append(r["name"])

        # Description
        description = None
        async with db.execute("SELECT text FROM comments WHERE book = ?", (book_id,)) as cur:
            c_row = await cur.fetchone()
            if c_row:
                description = c_row["text"]

        # TOC
        toc = []
        toc_query = (
            "SELECT id, title, level, page_number, anchor_href, order_index "
            "FROM x_toc_nodes WHERE book_id = ? ORDER BY order_index"
        )
        async with db.execute(toc_query, (book_id,)) as cur:
            for r in await cur.fetchall():
                toc.append(
                    TocNode(
                        id=r["id"],
                        book_id=book_id,
                        title=r["title"],
                        level=r["level"],
                        page_number=r["page_number"],
                        anchor_href=r["anchor_href"],
                        order_index=r["order_index"],
                    )
                )

        pub_year = None
        if b["pubdate"]:
            try:
                pub_year = int(str(b["pubdate"])[:4])
            except (ValueError, TypeError):
                pass

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
            description=description,
            toc=toc,
        )
