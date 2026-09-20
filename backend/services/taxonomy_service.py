"""Service for managing custom hierarchical taxonomies and virtual bookshelves."""

from pathlib import Path
from typing import Dict, List, Optional

import aiosqlite

from backend.domain.classification import Bookshelf, ClassificationResult, TaxonomyNode
from backend.domain.entities import Book


class TaxonomyService:
    """Manages custom category trees (x_taxonomies) and virtual bookshelves (x_bookshelves)."""

    def __init__(self, library_root: Path):
        self.library_root = library_root
        self.db_path = library_root / "metadata.db"

    # --- Custom Taxonomy Hierarchy ---

    async def create_category(
        self,
        name: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> TaxonomyNode:
        """Creates a category node and computes its materialized path."""
        clean_name = name.strip()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if parent_id:
                async with db.execute(
                    "SELECT path FROM x_taxonomies WHERE id = ?", (parent_id,)
                ) as cur:
                    parent_row = await cur.fetchone()
                    if not parent_row:
                        raise ValueError(f"Parent category {parent_id} not found")
                    parent_path = parent_row["path"]
                    path = f"{parent_path}/{clean_name}"
            else:
                path = f"/{clean_name}"

            cur = await db.execute(
                """
                INSERT INTO x_taxonomies (parent_id, name, path, description)
                VALUES (?, ?, ?, ?)
                """,
                (parent_id, clean_name, path, description),
            )
            node_id = cur.lastrowid
            await db.commit()

            return TaxonomyNode(
                id=node_id,
                parent_id=parent_id,
                name=clean_name,
                path=path,
                description=description,
                children=[],
            )

    async def get_taxonomy_tree(self) -> List[TaxonomyNode]:
        """Returns all categories structured as a hierarchical tree."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, parent_id, name, path, description, order_index "
                "FROM x_taxonomies ORDER BY order_index, name"
            ) as cur:
                rows = await cur.fetchall()

        nodes_by_id: Dict[int, TaxonomyNode] = {}
        for r in rows:
            node = TaxonomyNode(
                id=r["id"],
                parent_id=r["parent_id"],
                name=r["name"],
                path=r["path"],
                description=r["description"],
                order_index=r["order_index"],
                children=[],
            )
            nodes_by_id[node.id or 0] = node

        root_nodes: List[TaxonomyNode] = []
        for node in nodes_by_id.values():
            if node.parent_id and node.parent_id in nodes_by_id:
                nodes_by_id[node.parent_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes

    async def delete_category(self, category_id: int) -> bool:
        """Deletes a category node and all its descendant subcategories."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT path FROM x_taxonomies WHERE id = ?", (category_id,)
            ) as cur:
                row = await cur.fetchone()
                if not row:
                    return False
                prefix = row["path"]

            # Delete all nodes starting with this path prefix
            await db.execute(
                "DELETE FROM x_taxonomies WHERE path = ? OR path LIKE ?",
                (prefix, f"{prefix}/%"),
            )
            await db.commit()
            return True

    # --- Virtual Bookshelves ---

    async def create_bookshelf(
        self,
        name: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        is_smart: bool = False,
        rule_expression: Optional[str] = None,
    ) -> Bookshelf:
        """Creates a new virtual bookshelf."""
        clean_name = name.strip()
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                """
                INSERT INTO x_bookshelves (name, description, icon, is_smart, rule_expression)
                VALUES (?, ?, ?, ?, ?)
                """,
                (clean_name, description, icon, 1 if is_smart else 0, rule_expression),
            )
            shelf_id = cur.lastrowid
            await db.commit()

            return Bookshelf(
                id=shelf_id,
                name=clean_name,
                description=description,
                icon=icon,
                is_smart=is_smart,
                rule_expression=rule_expression,
                book_count=0,
            )

    async def list_bookshelves(self) -> List[Bookshelf]:
        """Lists all bookshelves with current book counts."""
        query = (
            "SELECT s.id, s.name, s.description, s.icon, s.is_smart, s.rule_expression, "
            "COUNT(bbl.book_id) as book_count "
            "FROM x_bookshelves s "
            "LEFT JOIN x_books_bookshelves_link bbl ON s.id = bbl.bookshelf_id "
            "GROUP BY s.id "
            "ORDER BY s.name"
        )
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query) as cur:
                rows = await cur.fetchall()

        shelves = []
        for r in rows:
            shelves.append(
                Bookshelf(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    icon=r["icon"],
                    is_smart=bool(r["is_smart"]),
                    rule_expression=r["rule_expression"],
                    book_count=r["book_count"],
                )
            )
        return shelves

    async def add_books_to_shelf(self, shelf_id: int, book_ids: List[int]) -> None:
        """Adds a list of book IDs to a bookshelf."""
        async with aiosqlite.connect(self.db_path) as db:
            for b_id in book_ids:
                await db.execute(
                    "INSERT OR IGNORE INTO x_books_bookshelves_link "
                    "(book_id, bookshelf_id) VALUES (?, ?)",
                    (b_id, shelf_id),
                )
            await db.commit()

    async def remove_book_from_shelf(self, shelf_id: int, book_id: int) -> None:
        """Removes a book from a bookshelf."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM x_books_bookshelves_link WHERE bookshelf_id = ? AND book_id = ?",
                (shelf_id, book_id),
            )
            await db.commit()

    async def get_books_on_shelf(self, shelf_id: int) -> List[Book]:
        """Retrieves full Book instances belonging to a specific bookshelf."""
        from backend.services.ingestion_service import IngestionService

        ingestion = IngestionService(self.library_root)
        books: List[Book] = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT book_id FROM x_books_bookshelves_link WHERE bookshelf_id = ?",
                (shelf_id,),
            ) as cur:
                rows = await cur.fetchall()

            for r in rows:
                try:
                    book = await ingestion._get_book_by_id(db, r["book_id"])
                    books.append(book)
                except Exception:
                    continue

        return books

    async def map_book_to_taxonomy(
        self, book_id: int, classification: ClassificationResult
    ) -> List[TaxonomyNode]:
        """Maps a classified book to matching nodes in the custom taxonomy tree."""
        search_terms = set(
            [classification.bisac_heading.lower()]
            + [t.lower() for t in classification.suggested_tags]
            + [w.lower() for w in classification.bisac_heading.split(" / ")]
        )

        matched_nodes: List[TaxonomyNode] = []

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, parent_id, name, path, description, order_index FROM x_taxonomies"
            ) as cur:
                rows = await cur.fetchall()

            for r in rows:
                cat_name = r["name"].lower()
                if any(cat_name == term or cat_name in term for term in search_terms):
                    node = TaxonomyNode(
                        id=r["id"],
                        parent_id=r["parent_id"],
                        name=r["name"],
                        path=r["path"],
                        description=r["description"],
                        order_index=r["order_index"],
                    )
                    matched_nodes.append(node)
                    await db.execute(
                        "INSERT OR IGNORE INTO x_books_taxonomies_link "
                        "(book_id, taxonomy_id, confidence) VALUES (?, ?, ?)",
                        (book_id, node.id, classification.confidence),
                    )

            await db.commit()

        return matched_nodes
