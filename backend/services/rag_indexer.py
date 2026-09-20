"""Hierarchical document chunking and LanceDB vector indexing service."""

import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite
import lancedb
import pyarrow as pa

from backend.domain.rag import VectorChunk
from backend.parsers import ParserRegistry
from backend.providers.embedding_provider import BaseEmbeddingProvider


class RAGIndexer:
    """Handles parsing, hierarchical chunking, embedding generation, and LanceDB storage."""

    def __init__(
        self,
        embedding_provider: BaseEmbeddingProvider,
        target_chunk_tokens: int = 768,
        overlap_tokens: int = 100,
    ):
        self.embedding_provider = embedding_provider
        self.target_chunk_tokens = target_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def chunk_book(
        self,
        book_id: int,
        library_id: str,
        title: str,
        authors: str,
        chapters: list[dict[str, Any]],
    ) -> list[VectorChunk]:
        """Hierarchically segments book chapters into token-bounded semantic chunks.

        Prepends hierarchical context breadcrumb headers:
        [Book: "{title}" by {authors} | Chapter: "{chapter_title}"]
        """
        chunks: list[VectorChunk] = []
        chunk_counter = 0

        # Estimate ~4 characters per token
        target_chars = self.target_chunk_tokens * 4
        overlap_chars = self.overlap_tokens * 4

        for ch in chapters:
            ch_idx = ch.get("index", ch.get("chapter_index", 0))
            ch_title = ch.get("title", ch.get("chapter_title", f"Chapter {ch_idx + 1}"))
            raw_text = ch.get("content", ch.get("text", "")).strip()

            if not raw_text:
                continue

            breadcrumb = f'[Book: "{title}" by {authors} | Chapter: "{ch_title}"]\n\n'

            # If the chapter text is small enough, it forms a single chunk
            if len(raw_text) <= target_chars:
                token_count = max(1, (len(breadcrumb) + len(raw_text)) // 4)
                chunk = VectorChunk(
                    chunk_id=f"{book_id}_c{chunk_counter}",
                    book_id=book_id,
                    library_id=library_id,
                    book_title=title,
                    authors=authors,
                    chapter_index=ch_idx,
                    chapter_title=ch_title,
                    content=breadcrumb + raw_text,
                    token_count=token_count,
                    created_at=datetime.now(timezone.utc),
                )
                chunks.append(chunk)
                chunk_counter += 1
                continue

            # Split by double newline paragraphs or sentence breaks
            paragraphs = [p.strip() for p in raw_text.split("\n\n") if p.strip()]
            current_buffer = ""

            for para in paragraphs:
                if len(current_buffer) + len(para) <= target_chars:
                    current_buffer = f"{current_buffer}\n\n{para}" if current_buffer else para
                else:
                    if current_buffer:
                        full_content = breadcrumb + current_buffer
                        token_count = max(1, len(full_content) // 4)
                        chunk = VectorChunk(
                            chunk_id=f"{book_id}_c{chunk_counter}",
                            book_id=book_id,
                            library_id=library_id,
                            book_title=title,
                            authors=authors,
                            chapter_index=ch_idx,
                            chapter_title=ch_title,
                            content=full_content,
                            token_count=token_count,
                            created_at=datetime.now(timezone.utc),
                        )
                        chunks.append(chunk)
                        chunk_counter += 1

                        # Compute sliding window overlap
                        if len(current_buffer) > overlap_chars:
                            current_buffer = current_buffer[-overlap_chars:] + "\n\n" + para
                        else:
                            current_buffer = para
                    else:
                        # Single huge paragraph, hard break
                        start = 0
                        while start < len(para):
                            end = min(start + target_chars, len(para))
                            slice_text = para[start:end]
                            full_content = breadcrumb + slice_text
                            chunk = VectorChunk(
                                chunk_id=f"{book_id}_c{chunk_counter}",
                                book_id=book_id,
                                library_id=library_id,
                                book_title=title,
                                authors=authors,
                                chapter_index=ch_idx,
                                chapter_title=ch_title,
                                content=full_content,
                                token_count=max(1, len(full_content) // 4),
                                created_at=datetime.now(timezone.utc),
                            )
                            chunks.append(chunk)
                            chunk_counter += 1
                            start += target_chars - overlap_chars

            if current_buffer:
                full_content = breadcrumb + current_buffer
                chunk = VectorChunk(
                    chunk_id=f"{book_id}_c{chunk_counter}",
                    book_id=book_id,
                    library_id=library_id,
                    book_title=title,
                    authors=authors,
                    chapter_index=ch_idx,
                    chapter_title=ch_title,
                    content=full_content,
                    token_count=max(1, len(full_content) // 4),
                    created_at=datetime.now(timezone.utc),
                )
                chunks.append(chunk)
                chunk_counter += 1

        return chunks

    def _extract_chapters_from_file(self, file_path: Path) -> list[dict[str, Any]]:
        """Extracts chapters or section text from a book file."""
        ext = file_path.suffix.lower()

        if ext == ".txt":
            content = file_path.read_text(encoding="utf-8", errors="replace")
            # Split by Chapter headings if present
            parts = re.split(r"(?i)(chapter\s+\d+[^:\n]*[:\n])", content)
            if len(parts) > 1:
                chapters = []
                idx = 0
                for i in range(1, len(parts), 2):
                    heading = parts[i].strip()
                    body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                    chapters.append({"index": idx, "title": heading, "content": body})
                    idx += 1
                return chapters
            return [{"index": 0, "title": "Full Document", "content": content}]

        # Use unified parser registry
        try:
            parser = ParserRegistry.get_parser(file_path)
            payload = parser.parse(file_path)
            full_text = payload.sample_text or payload.description or payload.title
            return [{"index": 0, "title": "Main Content", "content": full_text}]
        except Exception:
            return [{"index": 0, "title": "Document", "content": ""}]

    def _compute_checksum(self, file_path: Path) -> str:
        """Calculates SHA256 checksum of a physical book file."""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _get_or_create_table(self, library_path: Path) -> Any:
        """Opens or initializes the LanceDB book_chunks table inside <library_path>/.vectors/."""
        vector_dir = library_path / ".vectors"
        vector_dir.mkdir(parents=True, exist_ok=True)
        db = lancedb.connect(str(vector_dir))

        table_name = "book_chunks"
        tables_res = db.list_tables()
        existing_tables = (
            tables_res.tables if hasattr(tables_res, "tables") else list(db.table_names())
        )
        if table_name in existing_tables:
            return db.open_table(table_name)

        # Create table with PyArrow schema
        schema = pa.schema(
            [
                pa.field("chunk_id", pa.string()),
                pa.field("book_id", pa.int64()),
                pa.field("library_id", pa.string()),
                pa.field("book_title", pa.string()),
                pa.field("authors", pa.string()),
                pa.field("chapter_index", pa.int32()),
                pa.field("chapter_title", pa.string()),
                pa.field("content", pa.string()),
                pa.field(
                    "vector",
                    pa.list_(pa.float32(), self.embedding_provider.dimension),
                ),
                pa.field("token_count", pa.int32()),
                pa.field("created_at", pa.string()),
            ]
        )
        return db.create_table(table_name, schema=schema)

    async def index_book(
        self,
        book_id: int,
        library_id: str,
        library_path: Path,
        db: aiosqlite.Connection,
        force: bool = False,
    ) -> dict[str, Any]:
        """Indexes a single book into LanceDB, skipping if checksum matches existing index."""
        # 1. Fetch book details
        async with db.execute(
            """SELECT b.id, b.title, b.path,
                      (SELECT GROUP_CONCAT(a.name, ', ')
                       FROM books_authors_link bal
                       JOIN authors a ON a.id = bal.author
                       WHERE bal.book = b.id) AS authors
               FROM books b
               WHERE b.id = ?""",
            (book_id,),
        ) as cursor:
            book_row = await cursor.fetchone()

        if not book_row:
            return {"status": "error", "error": f"Book ID {book_id} not found"}

        title = book_row["title"]
        authors = book_row["authors"] or "Unknown"
        rel_path = book_row["path"]

        # 2. Locate physical book file
        async with db.execute(
            "SELECT format, name FROM data WHERE book = ? ORDER BY id ASC",
            (book_id,),
        ) as cursor:
            data_rows = await cursor.fetchall()

        if not data_rows:
            return {"status": "error", "error": f"No data formats found for book {book_id}"}

        # Select primary format (TXT, EPUB, PDF, DOCX, MOBI)
        primary = data_rows[0]
        file_name = f"{primary['name']}.{primary['format'].lower()}"
        file_path = library_path / rel_path / file_name

        if not file_path.exists():
            return {"status": "error", "error": f"Book file {file_path} does not exist on disk"}

        checksum = self._compute_checksum(file_path)

        # 3. Incremental delta check
        if not force:
            async with db.execute(
                "SELECT checksum, chunk_count, status FROM x_index_status WHERE book_id = ?",
                (book_id,),
            ) as cursor:
                status_row = await cursor.fetchone()
                if (
                    status_row
                    and status_row["status"] == "indexed"
                    and status_row["checksum"] == checksum
                ):
                    return {
                        "status": "skipped",
                        "reason": "already_indexed",
                        "book_id": book_id,
                        "chunks_indexed": status_row["chunk_count"],
                    }

        # 4. Extract chapters & generate chunks
        chapters = self._extract_chapters_from_file(file_path)
        chunks = self.chunk_book(
            book_id=book_id,
            library_id=library_id,
            title=title,
            authors=authors,
            chapters=chapters,
        )

        if not chunks:
            return {
                "status": "empty",
                "book_id": book_id,
                "chunks_indexed": 0,
                "message": "No extractable text content found",
            }

        # 5. Batch embed chunk contents
        texts = [c.content for c in chunks]
        vectors = await self.embedding_provider.embed_texts(texts)

        # 6. Store in LanceDB
        tbl = self._get_or_create_table(library_path)

        # Ensure idempotency: delete prior book records if table has entries
        if tbl.count_rows() > 0:
            tbl.delete(f"book_id = {book_id}")

        records = [
            {
                "chunk_id": c.chunk_id,
                "book_id": c.book_id,
                "library_id": c.library_id,
                "book_title": c.book_title,
                "authors": c.authors,
                "chapter_index": c.chapter_index,
                "chapter_title": c.chapter_title,
                "content": c.content,
                "vector": v,
                "token_count": c.token_count,
                "created_at": c.created_at.isoformat(),
            }
            for c, v in zip(chunks, vectors, strict=False)
        ]
        tbl.add(records)

        # 7. Update SQLite x_index_status
        await db.execute(
            """INSERT INTO x_index_status
               (book_id, library_id, indexed_at, chunk_count, checksum, status)
               VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, 'indexed')
               ON CONFLICT(book_id) DO UPDATE SET
                   library_id = excluded.library_id,
                   indexed_at = CURRENT_TIMESTAMP,
                   chunk_count = excluded.chunk_count,
                   checksum = excluded.checksum,
                   status = 'indexed',
                   error_message = NULL""",
            (book_id, library_id, len(chunks), checksum),
        )
        await db.commit()

        return {
            "status": "indexed",
            "book_id": book_id,
            "chunks_indexed": len(chunks),
        }
