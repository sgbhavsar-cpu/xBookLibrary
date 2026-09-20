import aiosqlite
import pytest

from backend.database.schema import CALIBRE_SCHEMA_DDL
from backend.domain.rag import SearchResult
from backend.providers.embedding_provider import MockEmbeddingProvider
from backend.services.rag_indexer import RAGIndexer
from backend.services.rag_search import RAGSearchService


@pytest.fixture
def mock_embedder():
    return MockEmbeddingProvider(dimension=768)


@pytest.fixture
async def indexed_library(tmp_path, mock_embedder):
    lib_path = tmp_path / "SearchLibrary"
    lib_path.mkdir(parents=True, exist_ok=True)
    db_file = lib_path / "metadata.db"

    # Set up books in SQLite
    async with aiosqlite.connect(str(db_file)) as db:
        await db.executescript(CALIBRE_SCHEMA_DDL)

        # Book 1: Physics
        c1 = await db.execute(
            """INSERT INTO books (title, author_sort, path)
               VALUES ('Quantum Foundations', 'Dirac, Paul',
                       'Paul Dirac/Quantum Foundations (1930)')"""
        )
        b1_id = c1.lastrowid
        await db.execute("INSERT INTO authors (name, sort) VALUES ('Paul Dirac', 'Dirac, Paul')")
        await db.execute("INSERT INTO books_authors_link (book, author) VALUES (?, 1)", (b1_id,))

        # Book 2: Biology
        c2 = await db.execute(
            """INSERT INTO books (title, author_sort, path)
               VALUES ('Cellular Genetics', 'Mendel, Gregor',
                       'Gregor Mendel/Cellular Genetics (1866)')"""
        )
        b2_id = c2.lastrowid
        await db.execute(
            "INSERT INTO authors (name, sort) VALUES ('Gregor Mendel', 'Mendel, Gregor')"
        )
        await db.execute("INSERT INTO books_authors_link (book, author) VALUES (?, 2)", (b2_id,))

        await db.commit()

    # Create dummy files
    p1 = lib_path / "Paul Dirac" / "Quantum Foundations (1930)"
    p1.mkdir(parents=True, exist_ok=True)
    (p1 / "book.txt").write_text(
        "Chapter 1: The Transformation Theory\n\n"
        "Quantum mechanics requires wave function transformation and superposition.\n\n"
        "Chapter 2: Commutation Relations\n\n"
        "The Poisson bracket of classical mechanics translates into quantum commutators.",
        encoding="utf-8",
    )

    p2 = lib_path / "Gregor Mendel" / "Cellular Genetics (1866)"
    p2.mkdir(parents=True, exist_ok=True)
    (p2 / "book.txt").write_text(
        "Chapter 1: Heredity in Pea Plants\n\n"
        "Dominant and recessive alleles determine phenotype traits.\n\n"
        "Chapter 2: Independent Assortment\n\n"
        "Alleles of different genes get sorted into gametes independently.",
        encoding="utf-8",
    )

    async with aiosqlite.connect(str(db_file)) as db:
        await db.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) "
            "VALUES (?, 'TXT', 100, 'book')",
            (b1_id,),
        )
        await db.execute(
            "INSERT INTO data (book, format, uncompressed_size, name) "
            "VALUES (?, 'TXT', 100, 'book')",
            (b2_id,),
        )
        await db.commit()

    # Index both books
    indexer = RAGIndexer(embedding_provider=mock_embedder)
    async with aiosqlite.connect(str(db_file)) as db:
        db.row_factory = aiosqlite.Row
        await indexer.index_book(b1_id, "search_lib", lib_path, db)
        await indexer.index_book(b2_id, "search_lib", lib_path, db)

    return {
        "lib_path": lib_path,
        "db_file": db_file,
        "book1_id": b1_id,
        "book2_id": b2_id,
    }


@pytest.mark.asyncio
async def test_hybrid_search_rrf_ranking(indexed_library, mock_embedder):
    lib_path = indexed_library["lib_path"]
    search_service = RAGSearchService(embedding_provider=mock_embedder)

    # 1. Search for quantum physics concept
    results = await search_service.search(
        library_path=lib_path,
        query="wave function superposition transformation",
        top_k=3,
        mode="hybrid",
    )

    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    # The top result should be Dirac's quantum book
    assert results[0].book_id == indexed_library["book1_id"]
    assert "Dirac" in results[0].authors
    assert results[0].score > 0.0


@pytest.mark.asyncio
async def test_search_filtering_by_book_id(indexed_library, mock_embedder):
    lib_path = indexed_library["lib_path"]
    search_service = RAGSearchService(embedding_provider=mock_embedder)

    # Search for a broad term "Chapter" but scoped only to Book 2 (Genetics)
    results = await search_service.search(
        library_path=lib_path,
        query="Chapter",
        book_id=indexed_library["book2_id"],
        top_k=5,
        mode="hybrid",
    )

    assert len(results) > 0
    for r in results:
        assert r.book_id == indexed_library["book2_id"]
        assert "Mendel" in r.authors
