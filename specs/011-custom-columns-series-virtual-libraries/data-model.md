# Data Model: 011 Custom Columns, Series & Virtual Libraries

## 1. Domain Entities (`backend/domain/custom_columns.py`)

### `CustomColumnDefinition`
Represents the metadata definition of a custom column:
```python
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
    id: int
    label: str  # e.g. "read_status"
    name: str   # e.g. "Read Status"
    datatype: CustomColumnDatatype
    is_multiple: bool = False
    normalized: bool = False
    display: Dict[str, Any] = Field(default_factory=dict)
    editable: bool = True
```

### `CustomColumnCreateRequest`
```python
class CustomColumnCreateRequest(BaseModel):
    label: str
    name: str
    datatype: CustomColumnDatatype
    display: Dict[str, Any] = Field(default_factory=dict)
```

### `BookCustomValues`
```python
class BookCustomValues(BaseModel):
    book_id: int
    values: Dict[str, Any] = Field(default_factory=dict)
    # Key is column label (e.g. "read_status"), value is str, int, float, bool, or list
```

### `SeriesInfo`
```python
class SeriesInfo(BaseModel):
    id: Optional[int] = None
    name: str
    series_index: float = 1.0
```

### `VirtualLibrary`
```python
class VirtualLibrary(BaseModel):
    name: str
    query: str
    book_count: Optional[int] = None
    description: Optional[str] = None
```
