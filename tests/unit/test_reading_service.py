import io
import os
import zipfile
import pytest
import aiosqlite

from backend.domain.reading import (
    AnnotationCreateRequest,
    BookmarkCreateRequest,
    ReadingProgressCreateRequest,
)
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager
from backend.services.reading_service import ReadingService
from backend.services.comic_service import ComicService, natural_sort_key
from backend.config import ConfigManager
from backend.domain.entities import Library


@pytest.fixture
async def temp_library(tmp_path, monkeypatch):
    """Creates an isolated temporary Calibre library with books and custom columns."""
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_path = tmp_path / "CalibreLib"
    lib_path.mkdir(parents=True, exist_ok=True)
    db_path = lib_path / "metadata.db"

    async with aiosqlite.connect(str(db_path)) as conn:
        await conn.execute("""
            CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author_sort TEXT,
                path TEXT NOT NULL DEFAULT ''
            )
        """)
        await conn.execute("""
            CREATE TABLE data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book INTEGER NOT NULL,
                format TEXT NOT NULL,
                name TEXT NOT NULL
            )
        """)
        await conn.execute("INSERT INTO books (id, title, author_sort, path) VALUES (1, 'Dune', 'Herbert, Frank', 'Dune')")
        await conn.execute("INSERT INTO books (id, title, author_sort, path) VALUES (2, 'Watchmen', 'Moore, Alan', 'Watchmen')")
        await conn.execute("INSERT INTO data (book, format, name) VALUES (1, 'EPUB', 'Dune - Frank Herbert')")
        await conn.execute("INSERT INTO data (book, format, name) VALUES (2, 'CBZ', 'Watchmen - Alan Moore')")
        await conn.commit()

    lib_id = "test_read_lib"
    cfg_mgr = ConfigManager()
    cfg_mgr.register_library(Library(id=lib_id, name="Test Reading Lib", path=str(lib_path)))
    manager = LibraryManager(config_manager=cfg_mgr)
    return lib_id, lib_path, manager


@pytest.mark.asyncio
async def test_reading_progress_save_and_get(temp_library):
    lib_id, _, manager = temp_library
    service = ReadingService(library_manager=manager)

    # Initial progress should be None
    prog = await service.get_progress(lib_id, book_id=1)
    assert prog is None

    # Save progress
    req = ReadingProgressCreateRequest(
        format="EPUB",
        location="epubcfi(/6/14)",
        progress_percent=35.5,
        seconds_increment=120,
    )
    saved = await service.save_progress(lib_id, book_id=1, req=req)
    assert saved.book_id == 1
    assert saved.progress_percent == 35.5
    assert saved.total_seconds == 120

    # Save second progress update (incrementing seconds)
    req2 = ReadingProgressCreateRequest(
        format="EPUB",
        location="epubcfi(/6/28)",
        progress_percent=60.0,
        seconds_increment=60,
    )
    saved2 = await service.save_progress(lib_id, book_id=1, req=req2)
    assert saved2.progress_percent == 60.0
    assert saved2.total_seconds == 180

    # Retrieve progress
    retrieved = await service.get_progress(lib_id, book_id=1, format_name="EPUB")
    assert retrieved is not None
    assert retrieved.progress_percent == 60.0
    assert retrieved.total_seconds == 180


@pytest.mark.asyncio
async def test_reading_progress_calibre_sync(temp_library):
    lib_id, _, manager = temp_library
    cc_service = CustomColumnsService(library_manager=manager)
    await cc_service.install_default_presets(lib_id)

    service = ReadingService(library_manager=manager, custom_columns_service=cc_service)

    # Reading at 50% should set #read_status to 'reading'
    req = ReadingProgressCreateRequest(
        format="EPUB",
        location="epubcfi(/6/10)",
        progress_percent=50.0,
        seconds_increment=30,
    )
    await service.save_progress(lib_id, book_id=1, req=req)

    vals = await cc_service.get_book_custom_values(lib_id, book_id=1)
    assert vals.values.get("read_status") == "reading"

    # Reading at 99% should set #read_status to 'completed'
    req_done = ReadingProgressCreateRequest(
        format="EPUB",
        location="epubcfi(/6/100)",
        progress_percent=99.0,
        seconds_increment=15,
    )
    await service.save_progress(lib_id, book_id=1, req=req_done)

    vals_done = await cc_service.get_book_custom_values(lib_id, book_id=1)
    assert vals_done.values.get("read_status") == "completed"


@pytest.mark.asyncio
async def test_annotations_crud_and_export(temp_library):
    lib_id, _, manager = temp_library
    service = ReadingService(library_manager=manager)

    # Create annotation
    ann_req = AnnotationCreateRequest(
        format="EPUB",
        location="epubcfi(/6/4)",
        selected_text="Fear is the mind-killer.",
        color="purple",
        note_text="Litany against fear.",
        chapter_title="Chapter 1",
    )
    ann = await service.create_annotation(lib_id, book_id=1, req=ann_req)
    assert ann.id.startswith("ann-")
    assert ann.selected_text == "Fear is the mind-killer."

    # List annotations
    anns = await service.list_annotations(lib_id, book_id=1)
    assert len(anns) == 1
    assert anns[0].color == "purple"

    # Export markdown
    md = await service.export_annotations_markdown(lib_id, book_id=1)
    assert "Fear is the mind-killer." in md
    assert "Litany against fear." in md
    assert "Chapter 1" in md

    # Delete annotation
    deleted = await service.delete_annotation(lib_id, ann.id)
    assert deleted is True

    anns_after = await service.list_annotations(lib_id, book_id=1)
    assert len(anns_after) == 0


@pytest.mark.asyncio
async def test_bookmarks_crud(temp_library):
    lib_id, _, manager = temp_library
    service = ReadingService(library_manager=manager)

    # Create bookmark
    bm_req = BookmarkCreateRequest(
        format="EPUB",
        location="epubcfi(/6/50)",
        title="Climax Scene",
    )
    bm = await service.create_bookmark(lib_id, book_id=1, req=bm_req)
    assert bm.id.startswith("bm-")

    bms = await service.list_bookmarks(lib_id, book_id=1)
    assert len(bms) == 1
    assert bms[0].title == "Climax Scene"

    # Delete bookmark
    del_ok = await service.delete_bookmark(lib_id, bm.id)
    assert del_ok is True
    assert len(await service.list_bookmarks(lib_id, book_id=1)) == 0


def test_natural_sort_key():
    items = ["page_10.jpg", "page_1.jpg", "page_2.jpg", "page_20.jpg"]
    sorted_items = sorted(items, key=natural_sort_key)
    assert sorted_items == ["page_1.jpg", "page_2.jpg", "page_10.jpg", "page_20.jpg"]


@pytest.mark.asyncio
async def test_comic_service(temp_library):
    lib_id, lib_path, manager = temp_library

    # Create mock CBZ file in Watchmen directory
    watchmen_dir = lib_path / "Watchmen"
    watchmen_dir.mkdir(parents=True, exist_ok=True)
    cbz_path = watchmen_dir / "Watchmen - Alan Moore.cbz"

    with zipfile.ZipFile(str(cbz_path), "w") as zf:
        zf.writestr("page_2.jpg", b"fake image 2")
        zf.writestr("page_1.jpg", b"fake image 1")
        zf.writestr("page_10.jpg", b"fake image 10")
        zf.writestr(
            "ComicInfo.xml",
            b"<ComicInfo><Series>Watchmen</Series><Number>1</Number></ComicInfo>",
        )

    comic_svc = ComicService(library_manager=manager)
    manifest = comic_svc.get_manifest(lib_id, book_id=2)
    assert manifest.total_pages == 3
    assert manifest.series_name == "Watchmen"
    assert manifest.issue_number == 1.0
    assert manifest.pages[0].filename == "page_1.jpg"
    assert manifest.pages[1].filename == "page_2.jpg"
    assert manifest.pages[2].filename == "page_10.jpg"

    # Stream page image
    img_data, mime = comic_svc.get_page_image(lib_id, book_id=2, page_index=0)
    assert img_data == b"fake image 1"
    assert "image" in mime
