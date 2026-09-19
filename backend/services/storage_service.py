"""Storage service: Calibre directory layout, path sanitization, and OPF generation."""

import re
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

from backend.domain.entities import Book


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize strings for Windows/POSIX filesystem safety."""
    if not name or not name.strip():
        return "Unknown"
    # Remove characters illegal on Windows and POSIX: \ / : * ? " < > |
    clean = re.sub(r'[\\/*?:"<>|]', "_", name.strip())
    # Collapse multiple whitespaces/underscores
    clean = re.sub(r"[\s_]+", " ", clean).strip()
    return clean[:max_length] if clean else "Unknown"


class StorageService:
    """Handles Calibre-standard folder structures, cover persistence, and OPF writing."""

    def __init__(self, library_root: Path):
        self.library_root = library_root

    def get_book_relative_dir(
        self, primary_author: str, title: str, year: Optional[int] = None
    ) -> str:
        """Constructs: <Author>/<Title> (<Year>) or <Author>/<Title>."""
        clean_author = sanitize_filename(primary_author or "Unknown")
        clean_title = sanitize_filename(title or "Unknown")
        if year:
            return f"{clean_author}/{clean_title} ({year})"
        return f"{clean_author}/{clean_title}"

    def get_book_absolute_dir(self, relative_dir: str) -> Path:
        return self.library_root / Path(relative_dir)

    def save_cover_image(
        self, book_dir: Path, image_bytes: bytes, max_dimension: int = 1200
    ) -> bool:
        """Optimize and save cover.jpg inside the book folder."""
        try:
            book_dir.mkdir(parents=True, exist_ok=True)
            cover_file = book_dir / "cover.jpg"
            img = Image.open(BytesIO(image_bytes))

            # Convert to RGB if RGBA/P
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Resize if exceeding max dimensions while preserving aspect ratio
            img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            img.save(cover_file, "JPEG", quality=85, optimize=True)
            return True
        except Exception:
            return False

    def write_metadata_opf(self, book_dir: Path, book: Book) -> Path:
        """Generates standard Calibre metadata.opf XML."""
        book_dir.mkdir(parents=True, exist_ok=True)
        opf_file = book_dir / "metadata.opf"

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
            },
        )

        # Title
        title_el = ET.SubElement(metadata, "dc:title")
        title_el.text = book.title

        # Authors
        for author in book.authors or ["Unknown"]:
            author_el = ET.SubElement(metadata, "dc:creator", {"opf:role": "aut"})
            author_el.text = author

        # Publisher & Date
        if book.publisher:
            pub_el = ET.SubElement(metadata, "dc:publisher")
            pub_el.text = book.publisher
        if book.publication_year:
            date_el = ET.SubElement(metadata, "dc:date")
            date_el.text = str(book.publication_year)

        # Description
        if book.description:
            desc_el = ET.SubElement(metadata, "dc:description")
            desc_el.text = book.description

        # Identifiers
        if book.isbn:
            isbn_el = ET.SubElement(metadata, "dc:identifier", {"opf:scheme": "ISBN"})
            isbn_el.text = book.isbn

        for id_type, id_val in book.identifiers.items():
            id_el = ET.SubElement(metadata, "dc:identifier", {"opf:scheme": id_type.upper()})
            id_el.text = id_val

        # Tags / Subjects
        for tag in book.tags:
            subject_el = ET.SubElement(metadata, "dc:subject")
            subject_el.text = tag

        # Series
        if book.series_name:
            ET.SubElement(metadata, "meta", {"name": "calibre:series", "content": book.series_name})
            ET.SubElement(
                metadata,
                "meta",
                {"name": "calibre:series_index", "content": str(book.series_index or 1.0)},
            )

        tree = ET.ElementTree(package)
        ET.indent(tree, space="  ", level=0)
        tree.write(opf_file, encoding="utf-8", xml_declaration=True)
        return opf_file
