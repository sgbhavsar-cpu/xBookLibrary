# Data Model: Core Metadata Editing & Multi-Format Ingestion

**Feature**: `015-core-metadata-editor-and-import`

---

## 1. Domain Entities & Request Models

### BookMetadataUpdateRequest
The unified data transfer model for manual single-book editing:

```python
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuthorInput(BaseModel):
    name: str
    sort: Optional[str] = None


class BookMetadataUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    title_sort: Optional[str] = None
    authors: List[str] = Field(..., min_items=1)
    author_sort: Optional[str] = None
    publisher: Optional[str] = None
    pubdate: Optional[datetime] = None
    rating: Optional[int] = Field(None, ge=0, le=10, description="Calibre 0-10 scale (0-5 stars)")
    series: Optional[str] = None
    series_index: Optional[float] = Field(None, ge=0.0)
    tags: List[str] = Field(default_factory=list)
    identifiers: Dict[str, str] = Field(default_factory=dict, description="e.g. {'isbn': '9780553803716', 'google': '...'}")
    comments: Optional[str] = Field(None, description="HTML or Markdown description")
    custom_values: Dict[str, Any] = Field(default_factory=dict, description="e.g. {'read_status': 'Completed', 'rating': 5}")
```

### Online Metadata Fetch Models
Structures for searching and returning ranked candidate records from online providers:

```python
class OnlineMetadataQuery(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None


class OnlineMetadataCandidate(BaseModel):
    provider: str  # 'google_books', 'openlibrary', 'crossref'
    confidence: float
    title: str
    authors: List[str]
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    description: Optional[str] = None
    isbn: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    cover_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
```

### Bulk Metadata Update Model
Model for updating multiple books simultaneously:

```python
class BulkMetadataUpdateRequest(BaseModel):
    book_ids: List[int] = Field(..., min_items=1)
    add_tags: List[str] = Field(default_factory=list)
    remove_tags: List[str] = Field(default_factory=list)
    set_author: Optional[str] = None
    set_publisher: Optional[str] = None
    set_rating: Optional[int] = Field(None, ge=0, le=10)
    set_series: Optional[str] = None
    auto_number_series: bool = False
    starting_series_index: float = 1.0
    series_index_increment: float = 1.0
    custom_values: Dict[str, Any] = Field(default_factory=dict)
```

---

## 2. Calibre SQLite Relational Mapping (`metadata.db`)

Every update maps to canonical Calibre tables without creating custom schema divergence:

| Entity Field | Calibre Table | Relationship & Synchronization Details |
| :--- | :--- | :--- |
| `title` | `books.title` | Direct update; updates `books.sort` via article stripping rules (`The`, `A`, `An`). |
| `title_sort` | `books.sort` | Saved into Calibre title sort column. |
| `authors` | `authors`, `books_authors_link` | Finds or creates author in `authors (id, name, sort)`. Replaces entries in `books_authors_link`. Sets `books.author_sort`. |
| `publisher` | `publishers`, `books_publishers_link` | Finds or creates in `publishers (id, name, sort)`. Updates link table. |
| `pubdate` | `books.pubdate` | Formatted as ISO-8601 string: `YYYY-MM-DDTHH:MM:SS+00:00`. |
| `rating` | `ratings`, `books_ratings_link` | Calibre ratings table stores integer `2, 4, 6, 8, 10` (representing 1-5 stars). |
| `series`, `series_index` | `series`, `books_series_link`, `books.series_index` | Finds or creates series name in `series`. Updates link table and `books.series_index`. |
| `tags` | `tags`, `books_tags_link` | Cleans tag strings. Replaces links in `books_tags_link`. |
| `identifiers` | `identifiers` | Deletes existing and re-inserts `(book, type, val)` rows (e.g. `type='isbn', val='978...'`). |
| `comments` | `comments` | Updates `text` in `comments WHERE book = ?`. |
| `custom_values` | `custom_columns`, `books_custom_column_*` | Updates specific typed column table (e.g. integer, bool, or string table). |
| `formats` | `data` | Tracks physical files: `format`, `name`, `uncompressed_size`. |

---

## 3. OPF File Representation (`metadata.opf`)

Whenever metadata or covers are saved, the system rewrites `metadata.opf` inside the book's directory (`library/{author}/{title}/metadata.opf`):

```xml
<?xml version='1.0' encoding='utf-8'?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="uuid_id" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier opf:scheme="calibre" id="calibre_id">1</dc:identifier>
    <dc:identifier opf:scheme="uuid" id="uuid_id">urn:uuid:...</dc:identifier>
    <dc:identifier opf:scheme="ISBN">9780553803716</dc:identifier>
    <dc:title>Foundation</dc:title>
    <dc:creator opf:file-as="Asimov, Isaac" opf:role="aut">Isaac Asimov</dc:creator>
    <dc:publisher>Gnome Press</dc:publisher>
    <dc:date>1951-05-01T00:00:00+00:00</dc:date>
    <dc:description>&lt;p&gt;The classic sci-fi epic.&lt;/p&gt;</dc:description>
    <dc:subject>Science Fiction</dc:subject>
    <dc:subject>Space Opera</dc:subject>
    <meta name="calibre:series" content="Foundation"/>
    <meta name="calibre:series_index" content="1.0"/>
    <meta name="calibre:rating" content="10"/>
  </metadata>
  <guide>
    <reference href="cover.jpg" title="Cover" type="cover"/>
  </guide>
</package>
```
