from pathlib import Path
import pytest
from httpx import ASGITransport, AsyncClient

from backend.config import ConfigManager
from backend.main import app
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import create_mock_calibre_library


@pytest.fixture
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XBOOKLIBRARY_CONFIG_DIR", str(cfg_dir))
    return cfg_dir


@pytest.fixture
async def active_opds_library(tmp_path: Path, isolated_env: Path):
    calibre_dir = tmp_path / "OPDSLib"
    create_mock_calibre_library(calibre_dir)

    lib_mgr = LibraryManager()
    lib = await lib_mgr.adopt_calibre_library(calibre_dir, name="OPDS Test Library", set_active=True)
    return lib


@pytest.mark.asyncio
async def test_opds_root_feed(active_opds_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/opds")
        assert res.status_code == 200
        assert "application/atom+xml" in res.headers["content-type"]
        assert "profile=opds-catalog" in res.headers["content-type"]
        assert "kind=navigation" in res.headers["content-type"]

        xml_body = res.text
        assert "urn:xbook:opds:root" in xml_body
        assert "All Books" in xml_body
        assert "Recent Additions" in xml_body


@pytest.mark.asyncio
async def test_opds_books_acquisition_feed(active_opds_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/opds/books")
        assert res.status_code == 200
        assert "application/atom+xml" in res.headers["content-type"]
        assert "kind=acquisition" in res.headers["content-type"]

        xml_body = res.text
        assert "Foundation" in xml_body
        assert "Neuromancer" in xml_body
        assert "http://opds-spec.org/acquisition" in xml_body


@pytest.mark.asyncio
async def test_opds_opensearch_and_query(active_opds_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # OpenSearch description
        res_desc = await client.get("/opds/opensearch.xml")
        assert res_desc.status_code == 200
        assert "application/opensearchdescription+xml" in res_desc.headers["content-type"]
        assert "OpenSearchDescription" in res_desc.text

        # Search query
        res_search = await client.get("/opds/search", params={"q": "Foundation"})
        assert res_search.status_code == 200
        assert "Foundation" in res_search.text
        assert "Neuromancer" not in res_search.text


@pytest.mark.asyncio
async def test_opds_2_json_catalog(active_opds_library):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/opds/v2.0")
        assert res.status_code == 200
        assert "application/opds+json" in res.headers["content-type"]

        data = res.json()
        assert "metadata" in data
        assert "publications" in data
        assert len(data["publications"]) >= 2
        titles = [p["metadata"]["title"] for p in data["publications"]]
        assert "Foundation" in titles
        assert "Neuromancer" in titles
