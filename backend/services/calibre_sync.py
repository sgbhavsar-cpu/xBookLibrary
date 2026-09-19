"""Calibre library introspection and zero-copy synchronization service."""

from pathlib import Path
from typing import List, Optional

import aiosqlite

from backend.domain.entities import Book, BookFormat


class InvalidCalibreLibraryError(Exception):
    """Raised when the specified directory is not a valid Calibre library."""

    pass


class CalibreSyncService:
    """Introspects and queries existing Calibre metadata.db instances."""

    def __init__(self, library_path: Path):
        self.library_path = library_path
        self.db_path = library_path / "metadata.db"

    @classmethod
    async def validate_calibre_directory(cls, library_path: Path) -> bool:
        """Validates that a directory contains a valid Calibre metadata.db with core tables."""
        if not library_path.exists() or not library_path.is_dir():
            raise InvalidCalibreLibraryError(f"Directory does not exist: {library_path}")

        db_file = library_path / "metadata.db"
        if not db_file.exists() or not db_file.is_file():
            raise InvalidCalibreLibraryError(f"metadata.db not found in {library_path}")

        try:
            async with aiosqlite.connect(db_file) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ) as cursor:
                    rows = await cursor.fetchall()
                    tables = {row["name"] for row in rows}

                required_tables = {"books", "authors", "books_authors_link", "data"}
                missing = required_tables - tables
                if missing:
                    raise InvalidCalibreLibraryError(
                        f"Database is missing mandatory Calibre tables: {', '.join(missing)}"
                    )
                return True
        except Exception as e:
            if isinstance(e, InvalidCalibreLibraryError):
                raise
            raise InvalidCalibreLibraryError(f"Cannot open SQLite metadata.db: {e}") from e

    async def augment_schema(self) -> None:
        """Non-destructively creates xBookLibrary extension tables and ensures .vectors/ exists."""
        await self.validate_calibre_directory(self.library_path)

        # Create .vectors directory (Constitution Principle I)
        vectors_dir = self.library_path / ".vectors"
        vectors_dir.mkdir(parents=True, exist_ok=True)

        # Apply x_ extension tables DDL
        extension_ddl = """
        CREATE TABLE IF NOT EXISTS x_toc_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            parent_id INTEGER,
            title TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 0,
            page_number INTEGER,
            anchor_href TEXT,
            order_index INTEGER NOT NULL,
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY(parent_id) REFERENCES x_toc_nodes(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS toc_book_idx ON x_toc_nodes (book_id, order_index);

        CREATE TABLE IF NOT EXISTS x_file_hashes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            format TEXT NOT NULL,
            sha256 TEXT NOT NULL UNIQUE,
            file_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS hash_idx ON x_file_hashes (sha256);

        CREATE TABLE IF NOT EXISTS x_ingestion_jobs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            source_path TEXT,
            book_id INTEGER,
            total_files INTEGER DEFAULT 0,
            processed_files INTEGER DEFAULT 0,
            error_log TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS x_library_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(extension_ddl)
            await db.commit()

    async def get_book_count(self) -> int:
        """Returns total books count in the library."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM books") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_books(
        self, page: int = 1, limit: int = 50, query: Optional[str] = None
    ) -> List[Book]:
        """Queries books from the Calibre database with authors, tags, and formats mapped."""
        offset = (page - 1) * limit
        sql = "SELECT id, title, sort, pubdate, isbn, path, has_cover FROM books"
        params = []

        if query:
            sql += " WHERE title LIKE ? OR author_sort LIKE ?"
            params.extend([f"%{query}%", f"%{query}%"])

        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        books: List[Book] = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute(sql, params) as cursor:
                book_rows = await cursor.fetchall()

            for b in book_rows:
                book_id = b["id"]

                # Fetch Authors
                authors = []
                author_sql = """
                SELECT a.name FROM authors a
                JOIN books_authors_link bal ON a.id = bal.author
                WHERE bal.book = ?
                """
                async with db.execute(author_sql, (book_id,)) as auth_cursor:
                    for a_row in await auth_cursor.fetchall():
                        authors.append(a_row["name"])

                # Fetch Formats
                formats = []
                data_sql = "SELECT id, format, uncompressed_size, name FROM data WHERE book = ?"
                async with db.execute(data_sql, (book_id,)) as data_cursor:
                    for d_row in await data_cursor.fetchall():
                        fmt = d_row["format"]
                        fmt_name = d_row["name"]
                        ext = fmt.lower()
                        file_path = f"{b['path']}/{fmt_name}.{ext}"
                        formats.append(
                            BookFormat(
                                id=d_row["id"],
                                book_id=book_id,
                                format=fmt,
                                uncompressed_size=d_row["uncompressed_size"],
                                name=fmt_name,
                                file_path=file_path,
                            )
                        )

                # Fetch Tags
                tags = []
                tag_sql = """
                SELECT t.name FROM tags t
                JOIN books_tags_link btl ON t.id = btl.tag
                WHERE btl.book = ?
                """
                async with db.execute(tag_sql, (book_id,)) as tag_cursor:
                    for t_row in await tag_cursor.fetchall():
                        tags.append(t_row["name"])

                # Extract publication year
                pub_year = None
                if b["pubdate"]:
                    try:
                        pub_year = int(str(b["pubdate"])[:4])
                    except (ValueError, TypeError):
                        pass

                books.append(
                    Book(
                        id=book_id,
                        title=b["title"],
                        sort_title=b["sort"],
                        authors=authors,
                        publication_year=pub_year,
                        isbn=b["isbn"],
                        path=b["path"],
                        has_cover=bool(b["has_cover"]),
                        formats=formats,
                        tags=tags,
                    )
                )

        return books
