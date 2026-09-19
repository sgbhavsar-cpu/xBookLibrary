"""EPUB format parser implementation."""

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
    TocItem,
)


class EpubParser(BookParserStrategy):
    """Extracts metadata, cover image, and TOC from EPUB 2 and EPUB 3 archives."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # 1. Locate OPF content file via META-INF/container.xml
                try:
                    container_data = zf.read("META-INF/container.xml")
                    container_root = ET.fromstring(container_data)
                    # Find rootfile
                    rootfile = container_root.find(
                        ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
                    )
                    if rootfile is None or "full-path" not in rootfile.attrib:
                        raise CorruptedBookError(
                            "Invalid container.xml: missing rootfile full-path"
                        )
                    opf_path = rootfile.attrib["full-path"]
                except Exception as e:
                    raise CorruptedBookError(f"Unable to read EPUB container.xml: {e}") from e

                opf_dir = Path(opf_path).parent.as_posix()
                if opf_dir == ".":
                    opf_dir = ""

                # 2. Parse OPF file
                try:
                    opf_data = zf.read(opf_path)
                    opf_root = ET.fromstring(opf_data)
                except Exception as e:
                    raise CorruptedBookError(f"Unable to parse OPF manifest: {e}") from e

                # XML namespaces
                ns = {
                    "opf": "http://www.idpf.org/2007/opf",
                    "dc": "http://purl.org/dc/elements/1.1/",
                }

                # Extract Title
                title = "Unknown Title"
                title_elem = opf_root.find(".//dc:title", ns)
                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                else:
                    # Fallback to filename without extension
                    title = file_path.stem

                # Extract Authors
                authors = []
                for creator in opf_root.findall(".//dc:creator", ns):
                    if creator.text and creator.text.strip():
                        authors.append(creator.text.strip())
                if not authors:
                    authors = ["Unknown Author"]

                # Extract Publication Year
                pub_year: Optional[int] = None
                date_elem = opf_root.find(".//dc:date", ns)
                if date_elem is not None and date_elem.text:
                    match = re.search(r"\b(1\d{3}|20\d{2})\b", date_elem.text)
                    if match:
                        pub_year = int(match.group(1))

                # Publisher & Description
                publisher = None
                pub_elem = opf_root.find(".//dc:publisher", ns)
                if pub_elem is not None and pub_elem.text:
                    publisher = pub_elem.text.strip()

                description = None
                desc_elem = opf_root.find(".//dc:description", ns)
                if desc_elem is not None and desc_elem.text:
                    description = desc_elem.text.strip()

                language = None
                lang_elem = opf_root.find(".//dc:language", ns)
                if lang_elem is not None and lang_elem.text:
                    language = lang_elem.text.strip()

                # Identifiers (ISBN, etc.)
                identifiers: Dict[str, str] = {}
                for ident in opf_root.findall(".//dc:identifier", ns):
                    if ident.text:
                        val = ident.text.strip()
                        scheme = ident.attrib.get(f"{{{ns['opf']}}}scheme", "id").lower()
                        identifiers[scheme] = val

                # Tags / Subjects
                tags = []
                for subj in opf_root.findall(".//dc:subject", ns):
                    if subj.text and subj.text.strip():
                        tags.append(subj.text.strip())

                # Manifest items map
                manifest = {}
                for item in opf_root.findall(".//opf:item", ns):
                    item_id = item.attrib.get("id")
                    item_href = item.attrib.get("href")
                    item_media = item.attrib.get("media-type")
                    properties = item.attrib.get("properties", "")
                    if item_id and item_href:
                        manifest[item_id] = {
                            "href": item_href,
                            "media-type": item_media,
                            "properties": properties,
                        }

                # 3. Extract Cover Image
                cover_bytes: Optional[bytes] = None
                cover_mime = "image/jpeg"
                cover_href = None

                # Search meta name="cover"
                for meta in opf_root.findall(".//opf:meta", ns):
                    if meta.attrib.get("name") == "cover":
                        cover_id = meta.attrib.get("content")
                        if cover_id in manifest:
                            cover_href = manifest[cover_id]["href"]
                            cover_mime = manifest[cover_id].get("media-type", "image/jpeg")

                # EPUB 3 cover-image property
                if not cover_href:
                    for item_info in manifest.values():
                        if "cover-image" in item_info.get("properties", ""):
                            cover_href = item_info["href"]
                            cover_mime = item_info.get("media-type", "image/jpeg")
                            break

                # Fallback check for common cover file names in zip
                if not cover_href:
                    for name in zf.namelist():
                        if re.search(r"cover\.(jpe?g|png|webp)", name, re.IGNORECASE):
                            cover_href = name
                            cover_mime = "image/png" if name.endswith(".png") else "image/jpeg"
                            break

                if cover_href:
                    try:
                        resolved_cover = (
                            f"{opf_dir}/{cover_href}"
                            if opf_dir and not cover_href.startswith(opf_dir)
                            else cover_href
                        )
                        # Normalize path
                        resolved_cover = resolved_cover.replace("//", "/")
                        cover_bytes = zf.read(resolved_cover)
                    except Exception:
                        pass

                # 4. Extract Table of Contents (from NCX or Nav)
                table_of_contents: List[TocItem] = []
                ncx_href = None
                for item_info in manifest.values():
                    if item_info.get("media-type") == "application/x-dtbncx+xml":
                        ncx_href = item_info["href"]
                        break

                if ncx_href:
                    try:
                        resolved_ncx = f"{opf_dir}/{ncx_href}" if opf_dir else ncx_href
                        ncx_data = zf.read(resolved_ncx)
                        ncx_root = ET.fromstring(ncx_data)
                        ncx_ns = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
                        for nav_point in ncx_root.findall(".//ncx:navPoint", ncx_ns):
                            label = nav_point.find(".//ncx:text", ncx_ns)
                            content_el = nav_point.find(".//ncx:content", ncx_ns)
                            title_text = (
                                label.text.strip()
                                if label is not None and label.text
                                else "Section"
                            )
                            src = content_el.attrib.get("src") if content_el is not None else None
                            table_of_contents.append(TocItem(title=title_text, anchor_href=src))
                    except Exception:
                        pass

                # 5. Extract Sample Text (from first spine item)
                sample_text = ""
                spine_items = opf_root.findall(".//opf:itemref", ns)
                if spine_items:
                    first_id = spine_items[0].attrib.get("idref")
                    if first_id in manifest:
                        first_href = manifest[first_id]["href"]
                        resolved_first = f"{opf_dir}/{first_href}" if opf_dir else first_href
                        try:
                            html_bytes = zf.read(resolved_first)
                            raw_text = html_bytes.decode("utf-8", errors="ignore")
                            # Strip HTML tags
                            clean_text = re.sub(r"<[^>]+>", " ", raw_text)
                            clean_text = re.sub(r"\s+", " ", clean_text).strip()
                            sample_text = clean_text[:3000]
                        except Exception:
                            pass

                return ParsedBookPayload(
                    title=title,
                    authors=authors,
                    publication_year=pub_year,
                    publisher=publisher,
                    description=description,
                    language=language,
                    identifiers=identifiers,
                    tags=tags,
                    cover_bytes=cover_bytes,
                    cover_mime_type=cover_mime,
                    table_of_contents=table_of_contents,
                    sample_text=sample_text,
                    raw_format="EPUB",
                )

        except zipfile.BadZipFile as e:
            raise CorruptedBookError(f"File is not a valid EPUB zip archive: {e}") from e
