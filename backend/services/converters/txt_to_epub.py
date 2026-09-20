import html
import uuid
import zipfile
from pathlib import Path
from typing import Optional


class TxtToEpubConverter:
    """
    Converts plain text or markdown files into standard, reflowable EPUB format.
    """

    @classmethod
    def convert(
        cls,
        txt_path: Path,
        output_epub_path: Path,
        title: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Path:
        if not txt_path.exists():
            raise FileNotFoundError(f"Source text file not found: {txt_path}")

        raw_text = txt_path.read_text(encoding="utf-8", errors="replace")
        book_title = title or txt_path.stem
        book_author = author or "Unknown Author"
        book_uuid = str(uuid.uuid4())

        # Format paragraphs into XHTML
        paragraphs = raw_text.split("\n\n")
        body_html_parts = []
        for p in paragraphs:
            stripped = p.strip()
            if stripped:
                escaped = html.escape(stripped).replace("\n", "<br />")
                body_html_parts.append(f"      <p>{escaped}</p>")
        body_html = "\n".join(body_html_parts)

        chapter_xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
  <head>
    <title>{html.escape(book_title)}</title>
    <style type="text/css">
      body {{ font-family: sans-serif; line-height: 1.6; margin: 5%; }}
      p {{ margin-bottom: 1em; text-indent: 1.5em; }}
      h1 {{ text-align: center; margin-bottom: 2em; }}
    </style>
  </head>
  <body>
    <h1>{html.escape(book_title)}</h1>
{body_html}
  </body>
</html>"""

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{html.escape(book_title)}</dc:title>
    <dc:creator>{html.escape(book_author)}</dc:creator>
    <dc:identifier id="BookID">urn:uuid:{book_uuid}</dc:identifier>
    <dc:language>en</dc:language>
    <meta property="dcterms:modified">2026-09-20T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>"""

        output_epub_path.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(output_epub_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            # 1. mimetype must be stored uncompressed as first file
            z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            # 2. META-INF/container.xml
            z.writestr("META-INF/container.xml", container_xml)
            # 3. OEBPS files
            z.writestr("OEBPS/content.opf", content_opf)
            z.writestr("OEBPS/chapter1.xhtml", chapter_xhtml)

        return output_epub_path
