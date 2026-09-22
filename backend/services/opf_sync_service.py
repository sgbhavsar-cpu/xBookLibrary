"""Service for generating and atomically writing Calibre metadata.opf files."""

import logging
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from backend.domain.entities import Book

logger = logging.getLogger(__name__)


class OpfSyncService:
    """Generates standard Calibre Dublin Core 2.0 metadata.opf XML files."""

    @staticmethod
    def generate_opf_xml(book: Book, cover_filename: Optional[str] = "cover.jpg") -> bytes:
        """Constructs Dublin Core compliant OPF XML bytes matching Calibre desktop format."""
        package = ET.Element(
            "package",
            {
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "uuid_id",
                "version": "2.0",
            },
        )

        metadata = ET.SubElement(
            package,
            "metadata",
            {
                "xmlns:dc": "http://purl.org/dc/elements/1.1/",
                "xmlns:opf": "http://www.idpf.org/2007/opf",
                "xmlns:calibre": "http://calibre.kovidgoyal.net/2009/metadata",
            },
        )

        # Title
        title_el = ET.SubElement(metadata, "dc:title")
        title_el.text = book.title or "Unknown"

        # Title Sort
        if book.sort_title:
            ET.SubElement(
                metadata,
                "meta",
                {"name": "calibre:title_sort", "content": book.sort_title},
            )

        # Authors
        authors = book.authors if book.authors else ["Unknown"]
        for author in authors:
            author_el = ET.SubElement(
                metadata,
                "dc:creator",
                {"opf:role": "aut"},
            )
            author_el.text = author

        # Publisher
        if book.publisher:
            pub_el = ET.SubElement(metadata, "dc:publisher")
            pub_el.text = book.publisher

        # Date / Year
        if book.publication_year:
            date_el = ET.SubElement(metadata, "dc:date")
            date_el.text = f"{book.publication_year}-01-01T00:00:00+00:00"

        # Description / Comments
        if book.description:
            desc_el = ET.SubElement(metadata, "dc:description")
            desc_el.text = book.description

        # Language
        lang_el = ET.SubElement(metadata, "dc:language")
        lang_el.text = book.language or "eng"

        # Identifiers
        if book.uuid:
            uuid_el = ET.SubElement(
                metadata,
                "dc:identifier",
                {"id": "uuid_id", "opf:scheme": "uuid"},
            )
            uuid_el.text = book.uuid

        if book.isbn:
            isbn_el = ET.SubElement(
                metadata,
                "dc:identifier",
                {"opf:scheme": "ISBN"},
            )
            isbn_el.text = book.isbn

        if book.identifiers:
            for id_type, id_val in book.identifiers.items():
                if id_type.lower() not in ("uuid", "isbn"):
                    id_el = ET.SubElement(
                        metadata,
                        "dc:identifier",
                        {"opf:scheme": id_type.upper()},
                    )
                    id_el.text = str(id_val)

        # Tags / Subjects
        for tag in book.tags or []:
            tag_el = ET.SubElement(metadata, "dc:subject")
            tag_el.text = tag

        # Series & Series Index
        if book.series_name:
            ET.SubElement(
                metadata,
                "meta",
                {"name": "calibre:series", "content": book.series_name},
            )
            ET.SubElement(
                metadata,
                "meta",
                {"name": "calibre:series_index", "content": str(book.series_index or 1.0)},
            )

        # Rating (if present in custom_values or rating)
        rating_val = book.custom_values.get("rating") if book.custom_values else None
        if rating_val is not None:
            ET.SubElement(
                metadata,
                "meta",
                {"name": "calibre:rating", "content": str(rating_val)},
            )

        # Cover meta & guide
        manifest = ET.SubElement(package, "manifest")
        guide = ET.SubElement(package, "guide")

        if cover_filename:
            ET.SubElement(
                metadata,
                "meta",
                {"name": "cover", "content": "cover"},
            )
            ET.SubElement(
                manifest,
                "item",
                {
                    "id": "cover",
                    "href": cover_filename,
                    "media-type": "image/jpeg",
                },
            )
            ET.SubElement(
                guide,
                "reference",
                {
                    "type": "cover",
                    "title": "Cover",
                    "href": cover_filename,
                },
            )

        tree = ET.ElementTree(package)
        ET.indent(tree, space="  ", level=0)
        return ET.tostring(package, encoding="utf-8", xml_declaration=True)

    @classmethod
    def sync_opf_file(cls, book_dir: Path, book: Book) -> Path:
        """Atomically writes metadata.opf into the specified book directory."""
        book_dir.mkdir(parents=True, exist_ok=True)
        opf_path = book_dir / "metadata.opf"
        cover_path = book_dir / "cover.jpg"
        cover_name = "cover.jpg" if cover_path.exists() or book.has_cover else None

        xml_content = cls.generate_opf_xml(book, cover_name)

        # Atomic file write pattern
        with tempfile.NamedTemporaryFile(dir=book_dir, delete=False, suffix=".tmp") as tmp_file:
            tmp_file.write(xml_content)
            tmp_path = Path(tmp_file.name)

        try:
            os.replace(tmp_path, opf_path)
        except Exception as err:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise err

        logger.debug(f"Synchronized metadata.opf for book {book.id} at {opf_path}")
        return opf_path
