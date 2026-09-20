import tempfile
from pathlib import Path
import pytest

from backend.config import ConfigManager
from backend.database.connection import DatabaseManager
from backend.domain.custom_columns import (
    CustomColumnCreateRequest,
    CustomColumnDatatype,
)
from backend.services.custom_columns_service import CustomColumnsService
from backend.services.library_manager import LibraryManager
from backend.services.series_service import SeriesService
from backend.services.virtual_library_service import VirtualLibraryService


@pytest.fixture
def mock_library_env(tmp_path: Path, monkeypatch):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir(parents=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))

    lib_dir = tmp_path / "MainLibrary"
    lib_dir.mkdir(parents=True)

    db_mgr = DatabaseManager(lib_dir)
    import asyncio
    import aiosqlite
    asyncio.run(db_mgr.initialize_database())

    # Add a mock book
    async def add_book():
        async with aiosqlite.connect(db_mgr.db_path) as conn:
            cursor = await conn.execute(
                "INSERT INTO books (title, path) VALUES ('Foundation and Empire', 'Asimov/Foundation')"
            )
            await conn.commit()
            return cursor.lastrowid

    book_id = asyncio.run(add_book())

    from backend.domain.entities import Library
    cfg_mgr = ConfigManager()
    cfg_mgr.register_library(Library(id="test-lib", name="Test Lib", path=str(lib_dir)))

    lib_mgr = LibraryManager(config_manager=cfg_mgr)
    return lib_mgr, book_id


@pytest.mark.asyncio
async def test_custom_columns_crud_and_presets(mock_library_env):
    lib_mgr, book_id = mock_library_env
    cc_service = CustomColumnsService(library_manager=lib_mgr)

    # 1. Install presets
    presets = await cc_service.install_default_presets("test-lib")
    assert len(presets) >= 4
    preset_labels = [p.label for p in presets]
    assert "read_status" in preset_labels
    assert "pages" in preset_labels

    # 2. Set custom values for book
    await cc_service.set_book_custom_values(
        "test-lib",
        book_id,
        {
            "read_status": "Reading",
            "pages": 280,
            "rating": 5,
        },
    )

    # 3. Read back custom values
    custom_vals = await cc_service.get_book_custom_values("test-lib", book_id)
    assert custom_vals.book_id == book_id
    assert custom_vals.values["read_status"] == "Reading"
    assert custom_vals.values["pages"] == 280
    assert custom_vals.values["rating"] == 5

    # 4. Update a single value
    await cc_service.set_book_custom_values(
        "test-lib",
        book_id,
        {"read_status": "Completed"},
    )
    updated = await cc_service.get_book_custom_values("test-lib", book_id)
    assert updated.values["read_status"] == "Completed"
    assert updated.values["pages"] == 280  # unchanged


@pytest.mark.asyncio
async def test_series_service_workflow(mock_library_env):
    lib_mgr, book_id = mock_library_env
    series_svc = SeriesService(library_manager=lib_mgr)

    # 1. Assign series to book
    series_info = await series_svc.set_book_series(
        "test-lib", book_id, series_name="Foundation Series", series_index=2.0
    )
    assert series_info is not None
    assert series_info.name == "Foundation Series"
    assert series_info.series_index == 2.0

    # 2. Query series list
    all_series = await series_svc.get_series_list("test-lib")
    assert len(all_series) == 1
    assert all_series[0].name == "Foundation Series"
    assert all_series[0].book_count == 1

    # 3. Read book series
    book_series = await series_svc.get_book_series("test-lib", book_id)
    assert book_series is not None
    assert book_series.name == "Foundation Series"
    assert book_series.series_index == 2.0

    # 4. Remove series
    await series_svc.set_book_series("test-lib", book_id, series_name=None)
    book_series_after = await series_svc.get_book_series("test-lib", book_id)
    assert book_series_after is None


@pytest.mark.asyncio
async def test_virtual_library_service_and_filtering(mock_library_env):
    lib_mgr, book_id = mock_library_env
    vl_svc = VirtualLibraryService(library_manager=lib_mgr)

    # 1. Save virtual library
    vl = await vl_svc.save_virtual_library(
        "test-lib", name="Currently Reading", query="#read_status:Reading"
    )
    assert vl.name == "Currently Reading"
    assert vl.query == "#read_status:Reading"

    # 2. List virtual libraries
    vls = await vl_svc.get_virtual_libraries("test-lib")
    assert len(vls) == 1
    assert vls[0].name == "Currently Reading"

    # 3. Test query matching
    book_data = {
        "title": "Foundation and Empire",
        "authors": ["Isaac Asimov"],
        "tags": ["Science Fiction", "Classic"],
        "series": "Foundation",
    }

    # Match custom field
    assert vl_svc.matches_query(
        "#read_status:Reading",
        book_data,
        custom_values={"read_status": "Reading"},
    )
    assert not vl_svc.matches_query(
        "#read_status:Completed",
        book_data,
        custom_values={"read_status": "Reading"},
    )

    # Match series and tag
    assert vl_svc.matches_query('series:"Foundation"', book_data)
    assert vl_svc.matches_query('tag:"Science Fiction"', book_data)
    assert vl_svc.matches_query('tag:Classic not series:Dune', book_data)

    # 4. Delete virtual library
    deleted = await vl_svc.delete_virtual_library("test-lib", "Currently Reading")
    assert deleted is True
    remaining = await vl_svc.get_virtual_libraries("test-lib")
    assert len(remaining) == 0
