import aiosqlite
import lancedb
import pytest

from backend.database.schema import CALIBRE_SCHEMA_DDL
from backend.providers.embedding_provider import MockEmbeddingProvider
from backend.services.rag_indexer import RAGIndexer


@pytest.fixture
def mock_embedder():
    return MockEmbeddingProvider(dimension=768)


@pytest.fixture
async def temp_library(tmp_path):
    lib_path = tmp_path / "TestLibrary"
    lib_path.mkdir(parents=True, exist_ok=True)
    db_file = lib_path / "metadata.db"

    async with aiosqlite.connect(str(db_file)) as db:
        await db.executescript(CALIBRE_SCHEMA_DDL)
        # Insert a sample book
        cursor = await db.execute(
            """INSERT INTO books (title, author_sort, path)
               VALUES ('The Quantum Mind', 'Smith, Alice',
                       'Alice Smith/The Quantum Mind (2024)')"""
        )
        book_id = cursor.lastrowid
        await db.execute("INSERT INTO authors (name, sort) VALUES ('Alice Smith', 'Smith, Alice')")
        await db.execute("INSERT INTO books_authors_link (book, author) VALUES (?, 1)", (book_id,))
        await db.commit()

    # Create dummy book folder and text file
    book_folder = lib_path / "Alice Smith" / "The Quantum Mind (2024)"
    book_folder.mkdir(parents=True, exist_ok=True)
    txt_file = book_folder / "book.txt"
    txt_file.write_text(
        "Chapter 1: The Principle of Superposition\n\n"
        "In quantum physics, superposition describes the ability of a physical "
        "system to exist simultaneously in multiple states.\n\n"
        "This principle underpins quantum computers and quantum teleportation.\n\n"
        "Chapter 2: Quantum Entanglement\n\n"
        "Entanglement occurs when pairs or groups of particles interact in ways "
        "such that the quantum state cannot be described independently.\n\n"
        "Einstein called this spooky action at a distance.",
        encoding="utf-8",
    )

    async with aiosqlite.connect(str(db_file)) as db:
        await db.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) "
            "VALUES (?, 'TXT', 500, 'book')",
            (book_id,),
        )
        await db.commit()

    return {"lib_path": lib_path, "db_file": db_file, "book_id": book_id}


def test_hierarchical_chunking_with_breadcrumbs(mock_embedder):
    indexer = RAGIndexer(
        embedding_provider=mock_embedder,
        target_chunk_tokens=50,
        overlap_tokens=10,
    )

    chapters = [
        {
            "index": 0,
            "title": "Chapter 1: Superposition",
            "content": "Superposition is a fundamental principle. " * 10,
        },
        {
            "index": 1,
            "title": "Chapter 2: Entanglement",
            "content": "Entanglement is another cornerstone. " * 8,
        },
    ]

    chunks = indexer.chunk_book(
        book_id=42,
        library_id="test_lib",
        title="Quantum Mind",
        authors="Alice Smith",
        chapters=chapters,
    )

    assert len(chunks) >= 2
    # Verify breadcrumb injection
    expected_prefix = '[Book: "Quantum Mind" by Alice Smith | Chapter: "Chapter 1: Superposition"]'
    assert chunks[0].content.startswith(expected_prefix)
    assert chunks[0].book_id == 42
    assert chunks[0].library_id == "test_lib"
    assert chunks[0].chapter_title == "Chapter 1: Superposition"


@pytest.mark.asyncio
async def test_lancedb_indexing_and_delta_skip(temp_library, mock_embedder):
    lib_path = temp_library["lib_path"]
    db_file = temp_library["db_file"]
    book_id = temp_library["book_id"]

    indexer = RAGIndexer(embedding_provider=mock_embedder)

    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row

        # 1. First index run -> should succeed and create records in LanceDB & x_index_status
        result = await indexer.index_book(
            book_id=book_id,
            library_id="test_lib",
            library_path=lib_path,
            db=db,
        )

        assert result["status"] == "indexed"
        assert result["chunks_indexed"] > 0

        # Check SQLite x_index_status
        query = "SELECT * FROM x_index_status WHERE book_id = ?"
        async with db.execute(query, (book_id,)) as cursor:
            row = await cursor.fetchone()
            assert row is not None
            assert row["status"] == "indexed"
            assert row["chunk_count"] == result["chunks_indexed"]

        # Check LanceDB table in <lib_path>/.vectors/
        vector_dir = lib_path / ".vectors"
        assert vector_dir.exists()
        ldb = lancedb.connect(str(vector_dir))
        tbl = ldb.open_table("book_chunks")
        assert tbl.count_rows() == result["chunks_indexed"]

        # 2. Second index run without file changes -> should delta skip!
        skip_result = await indexer.index_book(
            book_id=book_id,
            library_id="test_lib",
            library_path=lib_path,
            db=db,
            force=False,
        )
        assert skip_result["status"] == "skipped"
        assert skip_result["reason"] == "already_indexed"

        # 3. Force reindex -> should re-index without duplicating rows
        force_result = await indexer.index_book(
            book_id=book_id,
            library_id="test_lib",
            library_path=lib_path,
            db=db,
            force=True,
        )
        assert force_result["status"] == "indexed"
        assert tbl.count_rows() == force_result["chunks_indexed"]
