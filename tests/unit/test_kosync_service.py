"""Unit tests for KosyncService."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest

from backend.domain.devices import KosyncProgress
from backend.domain.entities import Library
from backend.services.kosync_service import KosyncService
from tests.fixtures.generators import create_mock_calibre_library


@pytest.fixture
def mock_calibre_lib(tmp_path: Path) -> Path:
    lib_dir = tmp_path / "KosyncDevLib"
    create_mock_calibre_library(lib_dir)
    return lib_dir


@pytest.fixture
def mock_lib_mgr(mock_calibre_lib: Path) -> MagicMock:
    mock_lib = Library(
        id="lib-kosync",
        name="Kosync Library",
        path=str(mock_calibre_lib),
    )
    lib_mgr = MagicMock()
    lib_mgr.get_active_library.return_value = mock_lib
    lib_mgr.list_libraries.return_value = [mock_lib]
    return lib_mgr


@pytest.mark.asyncio
async def test_kosync_save_and_retrieve_progress(mock_lib_mgr: MagicMock, mock_calibre_lib: Path):
    svc = KosyncService(library_manager=mock_lib_mgr)

    doc_hash = "abc123def456"
    prog = KosyncProgress(
        document=doc_hash,
        progress="/6/4[chapter1]!/4/2/1:0",
        percentage=0.45,
        device="Kindle Paperwhite",
        device_id="dev-pw-1",
        timestamp=1726914000,
    )

    await svc.save_progress(prog, lib_dir=mock_calibre_lib, lib_id="lib-kosync")

    retrieved = await svc.get_progress(doc_hash, lib_dir=mock_calibre_lib)
    assert retrieved is not None
    assert retrieved.document == doc_hash
    assert retrieved.percentage == 0.45
    assert retrieved.device == "Kindle Paperwhite"

    # Test update
    prog_updated = KosyncProgress(
        document=doc_hash,
        progress="/6/8[chapter2]!/4/2/1:0",
        percentage=0.60,
        device="Kobo Clara",
        device_id="dev-kobo-2",
        timestamp=1726915000,
    )
    await svc.save_progress(prog_updated, lib_dir=mock_calibre_lib, lib_id="lib-kosync")

    retrieved_updated = await svc.get_progress(doc_hash, lib_dir=mock_calibre_lib)
    assert retrieved_updated is not None
    assert retrieved_updated.percentage == 0.60
    assert retrieved_updated.device == "Kobo Clara"


@pytest.mark.asyncio
async def test_kosync_non_existent_document(mock_lib_mgr: MagicMock, mock_calibre_lib: Path):
    svc = KosyncService(library_manager=mock_lib_mgr)
    retrieved = await svc.get_progress("non_existent_hash", lib_dir=mock_calibre_lib)
    assert retrieved is None
