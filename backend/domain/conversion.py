from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


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
    id: str = Field(..., description="Unique job identifier")
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    logs: List[str] = Field(default_factory=list)


class ConversionRequest(BaseModel):
    book_id: int
    source_format: Optional[str] = None
    target_format: str
    options: Dict[str, Any] = Field(default_factory=dict)
