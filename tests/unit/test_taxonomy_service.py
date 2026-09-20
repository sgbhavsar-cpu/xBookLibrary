"""Unit tests for custom hierarchical taxonomies and virtual bookshelves."""

from pathlib import Path

import pytest

from backend.domain.classification import ClassificationResult
from backend.services.library_manager import LibraryManager
from backend.services.taxonomy_service import TaxonomyService
from tests.fixtures.generators import create_sample_epub


@pytest.mark.asyncio
async def test_taxonomy_hierarchy_crud(tmp_path: Path):
    """Verifies creating, nesting, retrieving tree, and deleting custom category nodes."""
    lib_dir = tmp_path / "TaxonomyLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Taxonomy Lib", set_active=False)

    tax_service = TaxonomyService(lib_dir)

    # 1. Create root category
    root = await tax_service.create_category(
        name="Computer Science",
        description="Computing, software, and systems",
    )
    assert root.id is not None
    assert root.name == "Computer Science"
    assert root.path == "/Computer Science"

    # 2. Create nested child category
    child = await tax_service.create_category(
        name="Artificial Intelligence",
        parent_id=root.id,
        description="Machine learning and cognitive systems",
    )
    assert child.id is not None
    assert child.parent_id == root.id
    assert child.path == "/Computer Science/Artificial Intelligence"

    # 3. Create grandchild category
    grandchild = await tax_service.create_category(
        name="Large Language Models",
        parent_id=child.id,
    )
    assert grandchild.path == "/Computer Science/Artificial Intelligence/Large Language Models"

    # 4. Fetch full tree
    tree = await tax_service.get_taxonomy_tree()
    assert len(tree) == 1
    assert tree[0].name == "Computer Science"
    assert len(tree[0].children) == 1
    assert tree[0].children[0].name == "Artificial Intelligence"
    assert len(tree[0].children[0].children) == 1
    assert tree[0].children[0].children[0].name == "Large Language Models"

    # 5. Delete category (CASCADE)
    deleted = await tax_service.delete_category(child.id)
    assert deleted is True

    tree_after = await tax_service.get_taxonomy_tree()
    assert len(tree_after) == 1
    assert len(tree_after[0].children) == 0


@pytest.mark.asyncio
async def test_virtual_bookshelf_management(tmp_path: Path):
    """Verifies creating bookshelves, adding/removing books, and calculating book counts."""
    lib_dir = tmp_path / "ShelfLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="Shelf Lib", set_active=False)

    # Ingest 2 sample books
    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    epub1 = tmp_path / "book1.epub"
    create_sample_epub(epub1, title="Book One", author="Author A")
    b1 = await ingestion.ingest_file(epub1)

    epub2 = tmp_path / "book2.epub"
    create_sample_epub(epub2, title="Book Two", author="Author B")
    b2 = await ingestion.ingest_file(epub2)

    tax_service = TaxonomyService(lib_dir)

    # 1. Create bookshelf
    shelf = await tax_service.create_bookshelf(
        name="Currently Reading",
        description="Active reading list",
        icon="bookmark",
    )
    assert shelf.id is not None
    assert shelf.name == "Currently Reading"

    # 2. Add books to shelf
    await tax_service.add_books_to_shelf(shelf.id, [b1.id or 1, b2.id or 2])

    # 3. List bookshelves and assert count
    shelves = await tax_service.list_bookshelves()
    assert len(shelves) == 1
    assert shelves[0].book_count == 2

    # 4. Get books on shelf
    books_on_shelf = await tax_service.get_books_on_shelf(shelf.id)
    assert len(books_on_shelf) == 2
    titles = [b.title for b in books_on_shelf]
    assert "Book One" in titles
    assert "Book Two" in titles

    # 5. Remove a book from shelf
    await tax_service.remove_book_from_shelf(shelf.id, b1.id or 1)
    books_after = await tax_service.get_books_on_shelf(shelf.id)
    assert len(books_after) == 1
    assert books_after[0].title == "Book Two"


@pytest.mark.asyncio
async def test_auto_mapping_to_custom_taxonomy(tmp_path: Path):
    """Verifies that classification result maps book to best-matching custom taxonomy node."""
    lib_dir = tmp_path / "AutoMapLib"
    lib_mgr = LibraryManager()
    await lib_mgr.create_new_library(lib_dir, name="AutoMap Lib", set_active=False)

    from backend.services.ingestion_service import IngestionService

    ingestion = IngestionService(lib_dir)
    epub = tmp_path / "ai_book.epub"
    create_sample_epub(epub, title="Neural Networks Explained", author="Geoffrey H.")
    book = await ingestion.ingest_file(epub)

    tax_service = TaxonomyService(lib_dir)
    ai_cat = await tax_service.create_category(name="Artificial Intelligence")

    cls_result = ClassificationResult(
        book_id=book.id or 1,
        bisac_code="COM051260",
        bisac_heading="COMPUTERS / Artificial Intelligence / Machine Learning",
        ddc_code="006.3",
        confidence=0.92,
        suggested_tags=["Artificial Intelligence", "Neural Networks"],
    )

    mapped_nodes = await tax_service.map_book_to_taxonomy(book.id or 1, cls_result)
    assert len(mapped_nodes) == 1
    assert mapped_nodes[0].id == ai_cat.id
