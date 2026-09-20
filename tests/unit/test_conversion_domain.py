import pytest
from backend.domain.conversion import (
    ConversionJob,
    ConversionStatus,
    ConversionEngineUsed,
    ConversionRequest,
)
from backend.domain.opds import OPDSEntry, OPDSFeed, OPDSLink


def test_conversion_job_defaults_and_validation():
    job = ConversionJob(
        id="job-123",
        book_id=1,
        library_id="lib-abc",
        source_format="MOBI",
        target_format="EPUB",
    )
    assert job.status == ConversionStatus.PENDING
    assert job.percent_complete == 0
    assert job.engine_used is None
    assert job.logs == []

    # Update job state
    job.status = ConversionStatus.PROCESSING
    job.percent_complete = 50
    job.engine_used = ConversionEngineUsed.CALIBRE_CLI
    job.logs.append("Executing calibre CLI...")

    assert job.status == ConversionStatus.PROCESSING
    assert job.percent_complete == 50
    assert job.engine_used == ConversionEngineUsed.CALIBRE_CLI


def test_conversion_request_validation():
    req = ConversionRequest(
        book_id=42,
        target_format="PDF",
    )
    assert req.book_id == 42
    assert req.target_format == "PDF"
    assert req.source_format is None


def test_opds_models():
    entry = OPDSEntry(
        id="urn:xbook:book:1",
        title="Test Book",
        authors=["Ada Lovelace"],
        summary="A foundational book.",
        acquisition_links=[
            {"rel": "http://opds-spec.org/acquisition", "href": "/api/books/1/download?format=EPUB", "type": "application/epub+zip"}
        ]
    )
    feed = OPDSFeed(
        id="urn:xbook:feed:root",
        title="xBookLibrary Root",
        links=[
            OPDSLink(rel="self", href="/opds", type="application/atom+xml;profile=opds-catalog;kind=navigation")
        ],
        entries=[entry]
    )

    assert len(feed.entries) == 1
    assert feed.entries[0].title == "Test Book"
    assert feed.entries[0].authors == ["Ada Lovelace"]
