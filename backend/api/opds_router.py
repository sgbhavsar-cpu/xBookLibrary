from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response

from backend.config import ConfigManager
from backend.services.calibre_sync import CalibreSyncService
from backend.services.opds_service import OPDSService

router = APIRouter(tags=["OPDS Feed Server"])

ATOM_XML_NAV_MIME = "application/atom+xml;profile=opds-catalog;kind=navigation;charset=utf-8"
ATOM_XML_ACQ_MIME = "application/atom+xml;profile=opds-catalog;kind=acquisition;charset=utf-8"
OPENSEARCH_XML_MIME = "application/opensearchdescription+xml;charset=utf-8"
OPDS_JSON_MIME = "application/opds+json;charset=utf-8"


def _get_active_sync_service() -> CalibreSyncService:
    cfg_mgr = ConfigManager()
    active_lib = cfg_mgr.get_active_library()
    if not active_lib:
        raise HTTPException(status_code=404, detail="No active library configured")
    return CalibreSyncService(Path(active_lib.path))


@router.get("/opds", response_class=Response)
@router.get("/api/opds/v1.2", response_class=Response)
async def get_opds_root_feed(request: Request):
    """OPDS 1.2 Root Navigation Catalog Feed."""
    base_url = str(request.base_url).rstrip("/")
    xml_content = OPDSService.build_root_feed_xml(base_url)
    return Response(content=xml_content, media_type=ATOM_XML_NAV_MIME)


@router.get("/opds/books", response_class=Response)
async def get_opds_books_feed(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """OPDS 1.2 All Books Acquisition Feed."""
    sync_service = _get_active_sync_service()
    books = await sync_service.get_books(page=page, limit=limit)
    base_url = str(request.base_url).rstrip("/")

    xml_content = OPDSService.build_books_acquisition_feed_xml(
        books=books,
        base_url=base_url,
        title="All Books",
        feed_id="urn:xbook:opds:all-books",
        page=page,
        limit=limit,
    )
    return Response(content=xml_content, media_type=ATOM_XML_ACQ_MIME)


@router.get("/opds/recent", response_class=Response)
async def get_opds_recent_feed(
    request: Request,
    limit: int = Query(30, ge=1, le=100),
):
    """OPDS 1.2 Recent Additions Acquisition Feed."""
    sync_service = _get_active_sync_service()
    books = await sync_service.get_books(page=1, limit=limit)
    base_url = str(request.base_url).rstrip("/")

    xml_content = OPDSService.build_books_acquisition_feed_xml(
        books=books,
        base_url=base_url,
        title="Recent Additions",
        feed_id="urn:xbook:opds:recent",
    )
    return Response(content=xml_content, media_type=ATOM_XML_ACQ_MIME)


@router.get("/opds/opensearch.xml", response_class=Response)
async def get_opensearch_description(request: Request):
    """OpenSearch 1.1 Description document."""
    base_url = str(request.base_url).rstrip("/")
    xml_content = OPDSService.build_opensearch_description_xml(base_url)
    return Response(content=xml_content, media_type=OPENSEARCH_XML_MIME)


@router.get("/opds/search", response_class=Response)
async def search_opds_books(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """OPDS 1.2 Search Results Acquisition Feed."""
    sync_service = _get_active_sync_service()
    books = await sync_service.get_books(page=page, limit=limit, query=q)
    base_url = str(request.base_url).rstrip("/")

    xml_content = OPDSService.build_books_acquisition_feed_xml(
        books=books,
        base_url=base_url,
        title=f"Search: {q}",
        feed_id=f"urn:xbook:opds:search:{q}",
        page=page,
        limit=limit,
    )
    return Response(content=xml_content, media_type=ATOM_XML_ACQ_MIME)


@router.get("/api/opds/v2.0", response_class=Response)
async def get_opds_2_catalog(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
):
    """OPDS 2.0 Readium JSON Catalog Feed."""
    import json
    sync_service = _get_active_sync_service()
    books = await sync_service.get_books(page=page, limit=limit)
    base_url = str(request.base_url).rstrip("/")

    data = OPDSService.build_opds_2_json(books=books, base_url=base_url)
    return Response(content=json.dumps(data), media_type=OPDS_JSON_MIME)
