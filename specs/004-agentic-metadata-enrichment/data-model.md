# Data Model: Agentic Metadata Enrichment & Multimodal Reconciliation

**Feature Branch**: `004-agentic-metadata-enrichment`  
**Date**: 2026-09-20  

---

## 1. Domain Entities & Value Objects

### 1.1 `CandidateMetadata` (Normalized Provider Output)
Represents the bibliographic output returned by any provider (OpenLibrary, Google Books, CrossRef, LiteLLM Vision):

```python
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class CoverCandidate(BaseModel):
    url: Optional[str] = None
    bytes_data: Optional[bytes] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: str = "image/jpeg"
    source: str

class CandidateMetadata(BaseModel):
    source: str  # "openlibrary" | "google_books" | "crossref" | "litellm_vision"
    isbn: Optional[str] = None
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    language: Optional[str] = None
    identifiers: Dict[str, str] = Field(default_factory=dict)  # "doi", "asin", "goodreads"
    tags: List[str] = Field(default_factory=list)              # subjects, categories
    series_name: Optional[str] = None
    series_index: Optional[float] = None
    cover: Optional[CoverCandidate] = None
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
```

---

### 1.2 `ProposedField` (Field-by-Field Diff Entry)
Encapsulates current value versus proposed value with provenance:

```python
class ProposedField(BaseModel):
    field_name: str
    current_value: Optional[Any] = None
    proposed_value: Optional[Any] = None
    source: str
    confidence: float = 1.0
    is_conflicting: bool = False
```

---

### 1.3 `MetadataProposal` (Ephemeral Staging Object)
Persisted to `.vectors/staging/<proposal_id>.json` when strict human review is required (e.g. non-ISBN search or LLM vision extraction):

```python
from datetime import datetime
from enum import Enum

class ProposalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DISCARDED = "DISCARDED"

class MetadataProposal(BaseModel):
    id: str  # e.g., "prop-1a2b3c4d"
    book_id: int
    created_at: datetime
    status: ProposalStatus = ProposalStatus.PENDING
    is_exact_isbn: bool = False
    composite_confidence: float
    fields: Dict[str, ProposedField]
    candidate_covers: List[CoverCandidate] = Field(default_factory=list)
```

---

## 2. Filesystem & Cache Layout

All assets follow Constitution Principle I (Portability First):

```
<Library Root>/
├── metadata.db                     # Calibre SQLite database (books, authors, data, etc.)
├── <Author>/<Title> (<Year>)/       # Calibre book folders
│   ├── cover.jpg
│   ├── metadata.opf
│   └── <Title> - <Author>.<ext>
└── .vectors/                       # xBookLibrary internal data
    ├── cache/                      # 7-day TTL HTTP response cache
    │   └── <sha256_query_hash>.json
    └── staging/                    # Ephemeral candidate proposals awaiting review
        ├── prop-1a2b3c4d.json
        └── prop-1a2b3c4d_cover.jpg
```

---

## 3. Database Modifications & Calibre Schema Preservation

- **Zero Schema Additions**: Pending proposals reside entirely in `.vectors/staging/*.json` without requiring extra tables in `metadata.db`.
- **Atomic Commits**: Upon proposal approval, updates are committed to standard Calibre tables (`books`, `authors`, `books_authors_link`, `tags`, `books_tags_link`, `comments`, `identifiers`) and `metadata.opf` is rewritten in place.
