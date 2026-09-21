import asyncio
from pathlib import Path
import zipfile
import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Library
from backend.main import app


@pytest.fixture
def mock_reader_contract_library(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_dir = tmp_path / "ContractReaderLib"
    lib_dir.mkdir(parents=True)

    db_mgr = DatabaseManager(lib_dir)
    asyncio.run(db_mgr.initialize_database())

    async def seed():
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            cursor = await conn.execute(
                "INSERT INTO books (title, author_sort, path) VALUES ('Neuromancer', 'Gibson, William', 'Gibson/Neuromancer')"
            )
            book1_id = cursor.lastrowid
            await conn.execute(
                "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'EPUB', 1024, 'Neuromancer - William Gibson')",
                (book1_id,),
            )

            cursor2 = await conn.execute(
                "INSERT INTO books (title, author_sort, path) VALUES ('Akira Vol 1', 'Otomo, Katsuhiro', 'Otomo/Akira1')"
            )
            book2_id = cursor2.lastrowid
            await conn.execute(
                "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'CBZ', 2048, 'Akira Vol 1 - Katsuhiro Otomo')",
                (book2_id,),
            )
            await conn.commit()
            return book1_id, book2_id

    book1_id, book2_id = asyncio.run(seed())

    # Create mock CBZ in Akira directory
    akira_dir = lib_dir / "Otomo" / "Akira1"
    akira_dir.mkdir(parents=True, exist_ok=True)
    cbz_file = akira_dir / "Akira Vol 1 - Katsuhiro Otomo.cbz"
    with zipfile.ZipFile(str(cbz_file), "w") as zf:
        zf.writestr("page_01.jpg", b"mock binary image 1")
        zf.writestr("page_02.jpg", b"mock binary image 2")
        zf.writestr(
            "ComicInfo.xml",
            b"<ComicInfo><Series>Akira</Series><Number>1</Number></ComicInfo>",
        )

    cfg_mgr = ConfigManager()
    lib = Library(id="reader-lib", name="Reader Library", path=str(lib_dir))
    cfg_mgr.register_library(lib, set_active=True)

    return "reader-lib", book1_id, book2_id, lib_dir


@pytest.mark.asyncio
async def test_reader_progress_api_lifecycle(mock_reader_contract_library):
    lib_id, book_id, _, _ = mock_reader_contract_library

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Initial progress should be null
        res = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/progress")
        assert res.status_code == 200
        assert res.json() is None

        # 2. Save progress
        payload = {
            "format": "EPUB",
            "location": "epubcfi(/6/12[intro])",
            "progress_percent": 25.0,
            "seconds_increment": 90,
        }
        post_res = await client.post(
            f"/api/libraries/{lib_id}/books/{book_id}/progress", json=payload
        )
        assert post_res.status_code == 200
        data = post_res.json()
        assert data["book_id"] == book_id
        assert data["progress_percent"] == 25.0
        assert data["total_seconds"] == 90

        # 3. Retrieve progress again
        get_res = await client.get(
            f"/api/libraries/{lib_id}/books/{book_id}/progress?format=EPUB"
        )
        assert get_res.status_code == 200
        retrieved = get_res.json()
        assert retrieved["location"] == "epubcfi(/6/12[intro])"
        assert retrieved["progress_percent"] == 25.0


@pytest.mark.asyncio
async def test_annotations_and_bookmarks_api(mock_reader_contract_library):
    lib_id, book_id, _, _ = mock_reader_contract_library

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Create annotation
        ann_payload = {
            "format": "EPUB",
            "location": "epubcfi(/6/2)",
            "selected_text": "The sky above the port was the color of television, tuned to a dead channel.",
            "color": "blue",
            "note_text": "Classic cyberpunk intro line.",
            "chapter_title": "Chapter 1: Chiba City Blues",
        }
        res = await client.post(
            f"/api/libraries/{lib_id}/books/{book_id}/annotations", json=ann_payload
        )
        assert res.status_code == 201
        ann_data = res.json()
        ann_id = ann_data["id"]
        assert ann_data["color"] == "blue"

        # List annotations
        list_res = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/annotations")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1

        # Export markdown
        export_res = await client.get(
            f"/api/libraries/{lib_id}/books/{book_id}/annotations/export"
        )
        assert export_res.status_code == 200
        assert "The sky above the port" in export_res.text
        assert "Classic cyberpunk intro line." in export_res.text

        # Create bookmark
        bm_payload = {
            "format": "EPUB",
            "location": "epubcfi(/6/10)",
            "title": "Enter Case and Molly",
        }
        bm_res = await client.post(
            f"/api/libraries/{lib_id}/books/{book_id}/bookmarks", json=bm_payload
        )
        assert bm_res.status_code == 201
        bm_id = bm_res.json()["id"]

        # List bookmarks
        bm_list_res = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/bookmarks")
        assert len(bm_list_res.json()) == 1

        # Delete bookmark and annotation
        del_bm = await client.delete(
            f"/api/libraries/{lib_id}/books/{book_id}/bookmarks/{bm_id}"
        )
        assert del_bm.status_code == 204

        del_ann = await client.delete(
            f"/api/libraries/{lib_id}/books/{book_id}/annotations/{ann_id}"
        )
        assert del_ann.status_code == 204

        # Verify list empty
        empty_anns = await client.get(f"/api/libraries/{lib_id}/books/{book_id}/annotations")
        assert len(empty_anns.json()) == 0


@pytest.mark.asyncio
async def test_comic_api(mock_reader_contract_library):
    lib_id, _, comic_book_id, _ = mock_reader_contract_library

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Get comic manifest
        res = await client.get(
            f"/api/libraries/{lib_id}/books/{comic_book_id}/comic/manifest"
        )
        assert res.status_code == 200
        manifest = res.json()
        assert manifest["total_pages"] == 2
        assert manifest["series_name"] == "Akira"
        assert len(manifest["pages"]) == 2

        # Get first page image
        img_res = await client.get(
            f"/api/libraries/{lib_id}/books/{comic_book_id}/comic/pages/0"
        )
        assert img_res.status_code == 200
        assert img_res.content == b"mock binary image 1"
