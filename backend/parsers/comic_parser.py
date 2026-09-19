"""Comic archive parser implementation (CBZ and CBR)."""

import io
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Optional

from PIL import Image

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
)


class ComicParser(BookParserStrategy):
    """Extracts metadata from ComicInfo.xml and first image cover from CBZ/CBR archives."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext == ".cbr":
            # If rarfile is unavailable or unrar missing, fallback to filename
            try:
                import rarfile

                rf = rarfile.RarFile(file_path)
                return self._parse_archive(rf, file_path, "CBR")
            except Exception:
                return ParsedBookPayload(
                    title=file_path.stem,
                    authors=["Unknown Comic Author"],
                    raw_format="CBR",
                )

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                return self._parse_archive(zf, file_path, "CBZ")
        except zipfile.BadZipFile as e:
            raise CorruptedBookError(f"Corrupted CBZ archive: {e}") from e

    def _parse_archive(self, archive, file_path: Path, raw_format: str) -> ParsedBookPayload:
        namelist = archive.namelist()
        title = file_path.stem
        authors = []
        series_name = None
        series_index = None
        pub_year: Optional[int] = None
        description = None
        publisher = None
        tags = []

        # 1. Parse ComicInfo.xml if present
        comic_info_names = [n for n in namelist if n.lower().endswith("comicinfo.xml")]
        if comic_info_names:
            try:
                xml_data = archive.read(comic_info_names[0])
                root = ET.fromstring(xml_data)

                title_el = root.find("Title")
                if title_el is not None and title_el.text:
                    title = title_el.text.strip()

                series_el = root.find("Series")
                if series_el is not None and series_el.text:
                    series_name = series_el.text.strip()

                number_el = root.find("Number")
                if number_el is not None and number_el.text:
                    try:
                        series_index = float(number_el.text.strip())
                    except ValueError:
                        pass

                writer_el = root.find("Writer")
                if writer_el is not None and writer_el.text:
                    authors.extend([w.strip() for w in writer_el.text.split(",") if w.strip()])

                penciller_el = root.find("Penciller")
                if penciller_el is not None and penciller_el.text:
                    artists = [a.strip() for a in penciller_el.text.split(",") if a.strip()]
                    for artist in artists:
                        if artist not in authors:
                            authors.append(artist)

                summary_el = root.find("Summary")
                if summary_el is not None and summary_el.text:
                    description = summary_el.text.strip()

                year_el = root.find("Year")
                if year_el is not None and year_el.text:
                    try:
                        pub_year = int(year_el.text.strip())
                    except ValueError:
                        pass

                publisher_el = root.find("Publisher")
                if publisher_el is not None and publisher_el.text:
                    publisher = publisher_el.text.strip()

                genre_el = root.find("Genre")
                if genre_el is not None and genre_el.text:
                    tags.extend([g.strip() for g in re.split(r"[,/]", genre_el.text) if g.strip()])
            except Exception:
                pass

        if not authors:
            authors = ["Unknown Comic Creator"]

        # 2. Extract First Image as Cover
        image_extensions = (".jpg", ".jpeg", ".png", ".webp")
        image_names = sorted(
            [
                n
                for n in namelist
                if n.lower().endswith(image_extensions) and not n.startswith("__MACOSX")
            ],
            key=str.lower,
        )

        cover_bytes: Optional[bytes] = None
        cover_mime = "image/jpeg"
        if image_names:
            try:
                first_img_data = archive.read(image_names[0])
                img = Image.open(io.BytesIO(first_img_data))
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=85)
                cover_bytes = buf.getvalue()
            except Exception:
                pass

        return ParsedBookPayload(
            title=title,
            authors=authors,
            series_name=series_name,
            series_index=series_index,
            publication_year=pub_year,
            publisher=publisher,
            description=description,
            tags=tags,
            cover_bytes=cover_bytes,
            cover_mime_type=cover_mime,
            raw_format=raw_format,
        )
