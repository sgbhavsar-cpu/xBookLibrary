"""PDF format parser implementation."""

import io
import re
from pathlib import Path
from typing import List, Optional

import pypdf
import pypdfium2

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    DrmProtectedError,
    ParsedBookPayload,
    TocItem,
)


class PdfParser(BookParserStrategy):
    """Extracts metadata, cover image, and outline TOC from PDF files."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        try:
            reader = pypdf.PdfReader(str(file_path))
        except Exception as e:
            raise CorruptedBookError(f"Unable to read PDF file: {e}") from e

        if reader.is_encrypted:
            try:
                # Try decrypting with blank password (many PDFs have empty user password)
                decrypt_res = reader.decrypt("")
                if decrypt_res == 0:
                    raise DrmProtectedError("PDF is password-encrypted or DRM-protected")
            except Exception as e:
                raise DrmProtectedError(f"PDF is encrypted: {e}") from e

        # 1. Extract Info / Metadata
        info = reader.metadata or {}
        title = info.title if info.title and info.title.strip() else file_path.stem
        authors = (
            [info.author.strip()] if info.author and info.author.strip() else ["Unknown Author"]
        )

        pub_year: Optional[int] = None
        if info.creation_date:
            match = re.search(r"\b(1\d{3}|20\d{2})\b", str(info.creation_date))
            if match:
                pub_year = int(match.group(1))

        tags = []
        if info.subject:
            tags.append(info.subject.strip())
        if "/Keywords" in info and info["/Keywords"]:
            keywords = [k.strip() for k in str(info["/Keywords"]).split(",") if k.strip()]
            tags.extend(keywords)

        # 2. Extract Table of Contents / Outline Bookmarks
        table_of_contents: List[TocItem] = []
        try:

            def process_outline(outline_items, level=0):
                for item in outline_items:
                    if isinstance(item, list):
                        process_outline(item, level=level + 1)
                    elif hasattr(item, "title"):
                        page_num = None
                        try:
                            if hasattr(item, "page"):
                                page_num = reader.get_destination_page_number(item) + 1
                        except Exception:
                            pass
                        table_of_contents.append(
                            TocItem(title=item.title, level=level, page_number=page_num)
                        )

            if reader.outline:
                process_outline(reader.outline)
        except Exception:
            pass

        # 3. Extract Sample Text (First 3 pages)
        sample_text = ""
        try:
            extracted_pages = []
            for i in range(min(3, len(reader.pages))):
                text = reader.pages[i].extract_text() or ""
                if text.strip():
                    extracted_pages.append(text.strip())
            sample_text = "\n\n".join(extracted_pages)[:3000]
        except Exception:
            pass

        # 4. Render Page 1 as Cover Image via pypdfium2
        cover_bytes: Optional[bytes] = None
        cover_mime = "image/jpeg"
        try:
            pdf_doc = pypdfium2.PdfDocument(str(file_path))
            if len(pdf_doc) > 0:
                first_page = pdf_doc[0]
                image = first_page.render(scale=2.0).to_pil()
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=85)
                cover_bytes = buf.getvalue()
        except Exception:
            pass

        return ParsedBookPayload(
            title=title,
            authors=authors,
            publication_year=pub_year,
            publisher=info.get("/Producer"),
            description=info.subject,
            tags=tags,
            cover_bytes=cover_bytes,
            cover_mime_type=cover_mime,
            table_of_contents=table_of_contents,
            sample_text=sample_text,
            raw_format="PDF",
        )
