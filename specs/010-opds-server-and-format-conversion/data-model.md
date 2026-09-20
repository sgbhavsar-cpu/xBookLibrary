# Data Model: 010 OPDS 1.2/2.0 Feed Server & Format Conversion Engine

## 1. Conversion Job Entity

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ConversionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConversionEngineUsed(str, Enum):
    CALIBRE_CLI = "calibre_cli"
    PYTHON_NATIVE = "python_native"

class ConversionJob(BaseModel):
    id: str = Field(..., description="Unique job UUID")
    book_id: int = Field(..., description="Target Calibre book ID")
    library_id: str = Field(..., description="Associated Library ID")
    source_format: str = Field(..., description="Source format string (e.g. MOBI, CBZ, TXT)")
    target_format: str = Field(..., description="Target format string (e.g. EPUB, PDF)")
    status: ConversionStatus = Field(default=ConversionStatus.PENDING)
    percent_complete: int = Field(default=0, ge=0, le=100)
    engine_used: Optional[ConversionEngineUsed] = None
    output_file_path: Optional[str] = None
    output_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)

class ConversionRequest(BaseModel):
    book_id: int
    source_format: Optional[str] = None  # Auto-select primary format if omitted
    target_format: str  # EPUB, PDF, TXT
    options: Dict[str, Any] = Field(default_factory=dict)
```

## 2. OPDS Navigation Link & Entry Models

```python
class OPDSEntry(BaseModel):
    id: str
    title: str
    updated: datetime
    authors: List[str] = Field(default_factory=list)
    summary: Optional[str] = None
    cover_url: Optional[str] = None
    acquisition_links: List[Dict[str, str]] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

class OPDSFeed(BaseModel):
    id: str
    title: str
    updated: datetime
    author_name: str = "xBookLibrary"
    icon_url: Optional[str] = None
    links: List[Dict[str, str]] = Field(default_factory=list)
    entries: List[OPDSEntry] = Field(default_factory=list)
```
