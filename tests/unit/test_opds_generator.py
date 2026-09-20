import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from backend.domain.entities import Book, BookFormat
from backend.services.opds_service import OPDSService


def test_build_root_feed_xml():
    xml_str = OPDSService.build_root_feed_xml("http://localhost:8000")
    assert "<?xml version=" in xml_str
    assert "<feed" in xml_str
    assert "urn:xbook:opds:root" in xml_str
    assert "All Books" in xml_str
    assert "Recent Additions" in xml_str
    assert "Browse by Category" in xml_str

    # Parse XML
    root = ET.fromstring(xml_str)
    assert root.tag == "{http://www.w3.org/2005/Atom}feed"
    entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    assert len(entries) >= 4


def test_build_books_acquisition_feed_xml():
    b1 = Book(
        id=1,
        title="Dune",
        sort_title="Dune",
        authors=["Frank Herbert"],
        author_sort="Herbert, Frank",
        formats=[
            BookFormat(format="EPUB", uncompressed_size=1024, name="Dune - Frank Herbert.epub"),
            BookFormat(format="PDF", uncompressed_size=2048, name="Dune - Frank Herbert.pdf")
        ],
        tags=["Sci-Fi", "Classics"],
        description="Arrakis awaits.",
        last_modified=datetime.now(timezone.utc),
    )

    xml_str = OPDSService.build_books_acquisition_feed_xml([b1], "http://localhost:8000")
    assert "urn:xbook:book:1" in xml_str
    assert "Dune" in xml_str
    assert "Frank Herbert" in xml_str
    assert "application/epub+zip" in xml_str
    assert "application/pdf" in xml_str
    assert "http://opds-spec.org/acquisition" in xml_str
    assert "http://opds-spec.org/image" in xml_str

    root = ET.fromstring(xml_str)
    entries = root.findall("{http://www.w3.org/2005/Atom}entry")
    assert len(entries) == 1
    entry = entries[0]
    title_el = entry.find("{http://www.w3.org/2005/Atom}title")
    assert title_el is not None and title_el.text == "Dune"


def test_build_opensearch_description_xml():
    xml_str = OPDSService.build_opensearch_description_xml("http://localhost:8000")
    assert "OpenSearchDescription" in xml_str
    assert "http://localhost:8000/opds/search?q={searchTerms}" in xml_str
    root = ET.fromstring(xml_str)
    assert "OpenSearchDescription" in root.tag


def test_build_opds_2_json():
    b1 = Book(
        id=2,
        title="Foundation",
        sort_title="Foundation",
        authors=["Isaac Asimov"],
        formats=[
            BookFormat(format="EPUB", uncompressed_size=5000, name="Foundation.epub")
        ],
        tags=["Sci-Fi"],
        description="Psychohistory in action.",
    )

    data = OPDSService.build_opds_2_json([b1], "http://localhost:8000")
    assert "metadata" in data
    assert "publications" in data
    assert len(data["publications"]) == 1
    pub = data["publications"][0]
    assert pub["metadata"]["title"] == "Foundation"
    assert pub["metadata"]["author"] == ["Isaac Asimov"]
    assert len(pub["links"]) == 1
    assert pub["links"][0]["rel"] == "http://opds-spec.org/acquisition"
    assert pub["links"][0]["type"] == "application/epub+zip"
