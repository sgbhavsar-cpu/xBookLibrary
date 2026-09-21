import pytest
from pydantic import ValidationError
from backend.domain.reading import (
    ReadingProgress,
    ReadingProgressCreateRequest,
    Annotation,
    AnnotationCreateRequest,
    Bookmark,
    BookmarkCreateRequest,
    ComicPageInfo,
    ComicManifest,
)


def test_reading_progress_validation():
    progress = ReadingProgress(
        book_id=1,
        format="EPUB",
        location="epubcfi(/6/4[chapter1]!/4/2/10)",
        progress_percent=42.5,
        total_seconds=180,
    )
    assert progress.book_id == 1
    assert progress.progress_percent == 42.5
    assert progress.total_seconds == 180

    # Test invalid percent
    with pytest.raises(ValidationError):
        ReadingProgress(
            book_id=1,
            format="EPUB",
            location="loc",
            progress_percent=150.0,
        )


def test_annotation_model():
    req = AnnotationCreateRequest(
        format="EPUB",
        location="epubcfi(/6/2)",
        selected_text="It was the best of times, it was the worst of times",
        color="yellow",
        note_text="Famous opening line",
        chapter_title="Chapter 1",
    )
    assert req.color == "yellow"
    assert "best of times" in req.selected_text

    annotation = Annotation(
        id="ann-123",
        book_id=10,
        format=req.format,
        location=req.location,
        selected_text=req.selected_text,
        color=req.color,
        note_text=req.note_text,
        chapter_title=req.chapter_title,
    )
    assert annotation.id == "ann-123"
    assert annotation.book_id == 10


def test_bookmark_model():
    req = BookmarkCreateRequest(
        format="PDF",
        location="page-15",
        title="Key Diagram",
    )
    assert req.title == "Key Diagram"

    bm = Bookmark(
        id="bm-456",
        book_id=2,
        format=req.format,
        location=req.location,
        title=req.title,
    )
    assert bm.id == "bm-456"
    assert bm.location == "page-15"


def test_comic_manifest_model():
    pages = [
        ComicPageInfo(index=0, filename="001.jpg", url="/api/libraries/1/books/5/comic/pages/0"),
        ComicPageInfo(index=1, filename="002.jpg", url="/api/libraries/1/books/5/comic/pages/1"),
    ]
    manifest = ComicManifest(
        book_id=5,
        total_pages=2,
        pages=pages,
        series_name="Spider-Man",
        issue_number=1.0,
    )
    assert manifest.total_pages == 2
    assert manifest.pages[1].filename == "002.jpg"
