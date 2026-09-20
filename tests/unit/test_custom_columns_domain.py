import pytest
from backend.domain.custom_columns import (
    BookCustomValues,
    CustomColumnCreateRequest,
    CustomColumnDatatype,
    CustomColumnDefinition,
    SeriesInfo,
    VirtualLibrary,
    STANDARD_CUSTOM_COLUMN_PRESETS,
)


def test_custom_column_definition():
    col = CustomColumnDefinition(
        id=1,
        label="read_status",
        name="Read Status",
        datatype=CustomColumnDatatype.ENUMERATION,
        display={"enum_values": ["Unread", "Reading", "Completed"]},
    )
    assert col.id == 1
    assert col.display_label == "#read_status"
    assert col.datatype == CustomColumnDatatype.ENUMERATION
    assert "Reading" in col.display["enum_values"]


def test_book_custom_values_and_series():
    vals = BookCustomValues(
        book_id=10,
        values={
            "read_status": "Reading",
            "pages": 320,
            "rating": 5,
        },
    )
    assert vals.book_id == 10
    assert vals.values["read_status"] == "Reading"
    assert vals.values["pages"] == 320

    series = SeriesInfo(
        id=3,
        name="Foundation",
        series_index=2.5,
        book_count=7,
    )
    assert series.name == "Foundation"
    assert series.series_index == 2.5
    assert series.book_count == 7


def test_virtual_library_model():
    vl = VirtualLibrary(
        name="Sci-Fi Classics",
        query='tags:"Science Fiction" and rating:>4',
        book_count=12,
    )
    assert vl.name == "Sci-Fi Classics"
    assert "Science Fiction" in vl.query
    assert vl.book_count == 12


def test_standard_presets():
    assert len(STANDARD_CUSTOM_COLUMN_PRESETS) >= 4
    labels = [p.label for p in STANDARD_CUSTOM_COLUMN_PRESETS]
    assert "read_status" in labels
    assert "rating" in labels
    assert "pages" in labels
    assert "difficulty" in labels
