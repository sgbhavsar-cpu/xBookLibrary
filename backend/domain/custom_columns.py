from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomColumnDatatype(str, Enum):
    ENUMERATION = "enumeration"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    TEXT = "text"
    COMMENTS = "comments"
    RATING = "rating"
    SERIES = "series"


class CustomColumnDefinition(BaseModel):
    id: int = Field(..., description="Unique Calibre custom column integer ID")
    label: str = Field(..., description="Internal lookup label, e.g. 'read_status'")
    name: str = Field(..., description="User-friendly display name, e.g. 'Read Status'")
    datatype: CustomColumnDatatype = Field(..., description="Column data type")
    is_multiple: bool = Field(default=False, description="Whether multiple tags/values are supported")
    normalized: bool = Field(default=False, description="Whether stored in a normalized link table")
    display: Dict[str, Any] = Field(default_factory=dict, description="Display options e.g. enum_values")
    editable: bool = Field(default=True, description="Whether editable in UI")

    @property
    def display_label(self) -> str:
        """Returns Calibre-style prefixed label e.g. #read_status."""
        return f"#{self.label}" if not self.label.startswith("#") else self.label


class CustomColumnCreateRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=50, description="Column identifier without #")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    datatype: CustomColumnDatatype
    is_multiple: bool = False
    display: Dict[str, Any] = Field(default_factory=dict)


class BookCustomValues(BaseModel):
    book_id: int
    values: Dict[str, Any] = Field(default_factory=dict, description="Map of column label to value")


class SeriesInfo(BaseModel):
    id: Optional[int] = None
    name: str
    series_index: float = 1.0
    book_count: Optional[int] = None


class VirtualLibrary(BaseModel):
    name: str
    query: str
    book_count: Optional[int] = None
    description: Optional[str] = None


# Standard Calibre Presets
STANDARD_CUSTOM_COLUMN_PRESETS = [
    CustomColumnCreateRequest(
        label="read_status",
        name="Read Status",
        datatype=CustomColumnDatatype.ENUMERATION,
        display={"enum_values": ["Unread", "Reading", "Completed", "Abandoned"]},
    ),
    CustomColumnCreateRequest(
        label="rating",
        name="Rating",
        datatype=CustomColumnDatatype.RATING,
        display={},
    ),
    CustomColumnCreateRequest(
        label="pages",
        name="Pages",
        datatype=CustomColumnDatatype.INT,
        display={},
    ),
    CustomColumnCreateRequest(
        label="difficulty",
        name="Difficulty",
        datatype=CustomColumnDatatype.ENUMERATION,
        display={"enum_values": ["Introductory", "Intermediate", "Advanced"]},
    ),
    CustomColumnCreateRequest(
        label="notes",
        name="Personal Notes",
        datatype=CustomColumnDatatype.COMMENTS,
        display={},
    ),
]
