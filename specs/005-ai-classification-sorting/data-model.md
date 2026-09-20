# Data Model: AI Classification & Taxonomy Sorting

**Feature**: `005-ai-classification-sorting`  
**Date**: 2026-09-20  

---

## Domain Entities (Pydantic Models)

### `ClassificationResult`
Represents the automated classification evaluation for a book.
```python
class ClassificationResult(BaseModel):
    book_id: int
    bisac_code: str  # e.g., 'COM051010'
    bisac_heading: str  # e.g., 'COMPUTERS / Programming / Software Development'
    ddc_code: str  # e.g., '005.1'
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_tags: List[str] = Field(default_factory=list)
    secondary_bisac: Optional[str] = None
    secondary_ddc: Optional[str] = None
    reasoning: Optional[str] = None
    applied: bool = False
    proposal_id: Optional[str] = None
```

### `TaxonomyNode`
Represents a category in the user's custom hierarchical taxonomy tree.
```python
class TaxonomyNode(BaseModel):
    id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str
    path: str  # Full materialized path, e.g. '/Computer Science/Artificial Intelligence'
    description: Optional[str] = None
    order_index: int = 0
    children: List["TaxonomyNode"] = Field(default_factory=list)
```

### `Bookshelf`
Represents a manual or smart virtual collection.
```python
class Bookshelf(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_smart: bool = False
    rule_expression: Optional[str] = None  # e.g. 'ddc:005.*' or 'bisac:COM*'
    book_count: int = 0
    created_at: Optional[datetime] = None
```

---

## Calibre Isolated Extension Schema (DDL)

```sql
-- BISAC and DDC Classifications
CREATE TABLE IF NOT EXISTS x_classifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL UNIQUE,
    bisac_code TEXT NOT NULL,
    bisac_heading TEXT NOT NULL,
    ddc_code TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    secondary_bisac TEXT,
    secondary_ddc TEXT,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS bisac_idx ON x_classifications (bisac_code);
CREATE INDEX IF NOT EXISTS ddc_idx ON x_classifications (ddc_code);

-- User-Defined Custom Taxonomy Hierarchy
CREATE TABLE IF NOT EXISTS x_taxonomies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent_id INTEGER,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    description TEXT,
    order_index INTEGER DEFAULT 0,
    FOREIGN KEY(parent_id) REFERENCES x_taxonomies(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS tax_path_idx ON x_taxonomies (path);

-- Book to Custom Taxonomy Mapping
CREATE TABLE IF NOT EXISTS x_books_taxonomies_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    taxonomy_id INTEGER NOT NULL,
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(taxonomy_id) REFERENCES x_taxonomies(id) ON DELETE CASCADE,
    UNIQUE(book_id, taxonomy_id)
);
CREATE INDEX IF NOT EXISTS btl_tax_idx ON x_books_taxonomies_link (book_id, taxonomy_id);

-- Virtual Bookshelves / Smart Collections
CREATE TABLE IF NOT EXISTS x_bookshelves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    is_smart INTEGER DEFAULT 0,
    rule_expression TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Book to Bookshelf Mapping
CREATE TABLE IF NOT EXISTS x_books_bookshelves_link (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    bookshelf_id INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY(bookshelf_id) REFERENCES x_bookshelves(id) ON DELETE CASCADE,
    UNIQUE(book_id, bookshelf_id)
);
CREATE INDEX IF NOT EXISTS bbl_shelf_idx ON x_books_bookshelves_link (bookshelf_id, book_id);
```
