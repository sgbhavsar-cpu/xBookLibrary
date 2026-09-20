from pathlib import Path
import aiosqlite
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.entities import Library
from backend.main import app


@pytest.fixture
def mock_contract_library(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_dir = tmp_path / "ContractLib"
    lib_dir.mkdir(parents=True)

    db_mgr = DatabaseManager(lib_dir)
    import asyncio
    asyncio.run(db_mgr.initialize_database())

    # Add a mock book
    async def add_book():
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            cursor = await conn.execute(
                "INSERT INTO books (title, path) VALUES ('Dune Messiah', 'Herbert/Dune')"
            )
            await conn.commit()
            return cursor.lastrowid

    book_id = asyncio.run(add_book())

    cfg_mgr = ConfigManager()
    lib = Library(id="contract-lib", name="Contract Library", path=str(lib_dir))
    cfg_mgr.register_library(lib, set_active=True)

    return "contract-lib", book_id, lib_dir


@pytest.mark.asyncio
async def test_custom_columns_and_presets_api(mock_contract_library):
    lib_id, book_id, _ = mock_contract_library
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Install presets
        res = await client.post(f"/api/libraries/{lib_id}/custom-columns/presets")
        assert res.status_code == 200
        presets = res.json()
        assert len(presets) >= 4
        labels = [p["label"] for p in presets]
        assert "read_status" in labels
        assert "pages" in labels

        # 2. Create custom text column
        res = await client.post(
            f"/api/libraries/{lib_id}/custom-columns",
            json={
                "label": "location",
                "name": "Physical Shelf Location",
                "datatype": "text",
            },
        )
        assert res.status_code == 201
        created = res.json()
        assert created["label"] == "location"

        # 3. List all custom columns
        res = await client.get(f"/api/libraries/{lib_id}/custom-columns")
        assert res.status_code == 200
        all_cols = res.json()
        assert any(c["label"] == "location" for c in all_cols)

        # 4. Set book custom values
        res = await client.put(
            f"/api/books/{book_id}/custom-values?library_id={lib_id}",
            json={
                "read_status": "Reading",
                "pages": 420,
                "location": "Shelf A-3",
            },
        )
        assert res.status_code == 200
        vals = res.json()
        assert vals["values"]["read_status"] == "Reading"
        assert vals["values"]["pages"] == 420
        assert vals["values"]["location"] == "Shelf A-3"

        # 5. Read book custom values
        res = await client.get(f"/api/books/{book_id}/custom-values?library_id={lib_id}")
        assert res.status_code == 200
        get_vals = res.json()
        assert get_vals["values"]["read_status"] == "Reading"
        assert get_vals["values"]["pages"] == 420


@pytest.mark.asyncio
async def test_series_api_lifecycle(mock_contract_library):
    lib_id, book_id, _ = mock_contract_library
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Update book series
        res = await client.put(
            f"/api/books/{book_id}/series?library_id={lib_id}",
            json={"name": "Dune Chronicles", "series_index": 2.0},
        )
        assert res.status_code == 200
        s_data = res.json()
        assert s_data["name"] == "Dune Chronicles"
        assert s_data["series_index"] == 2.0

        # 2. Get book series
        res = await client.get(f"/api/books/{book_id}/series?library_id={lib_id}")
        assert res.status_code == 200
        get_s = res.json()
        assert get_s["name"] == "Dune Chronicles"
        assert get_s["series_index"] == 2.0

        # 3. List series in library
        res = await client.get(f"/api/libraries/{lib_id}/series")
        assert res.status_code == 200
        series_list = res.json()
        assert len(series_list) == 1
        assert series_list[0]["name"] == "Dune Chronicles"
        assert series_list[0]["book_count"] == 1


@pytest.mark.asyncio
async def test_virtual_libraries_api_lifecycle(mock_contract_library):
    lib_id, _, _ = mock_contract_library
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create virtual library
        res = await client.post(
            f"/api/libraries/{lib_id}/virtual-libraries",
            json={"name": "Sci-Fi Favorites", "query": 'tags:"Sci-Fi" and rating:>4'},
        )
        assert res.status_code == 200
        created_vl = res.json()
        assert created_vl["name"] == "Sci-Fi Favorites"

        # 2. List virtual libraries
        res = await client.get(f"/api/libraries/{lib_id}/virtual-libraries")
        assert res.status_code == 200
        vls = res.json()
        assert len(vls) == 1
        assert vls[0]["name"] == "Sci-Fi Favorites"

        # 3. Delete virtual library
        res = await client.delete(f"/api/libraries/{lib_id}/virtual-libraries/Sci-Fi Favorites")
        assert res.status_code == 200

        # 4. Confirm deleted
        res = await client.get(f"/api/libraries/{lib_id}/virtual-libraries")
        assert res.status_code == 200
        assert len(res.json()) == 0
