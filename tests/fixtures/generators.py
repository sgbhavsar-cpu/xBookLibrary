"""Helpers for creating synthetic test book files for all supported formats."""

import io
import zipfile
from pathlib import Path

import docx
from PIL import Image
from pypdf import PdfWriter


def create_sample_cover_bytes(width: int = 400, height: int = 600, color: str = "blue") -> bytes:
    """Generate a sample JPEG cover image in memory."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_sample_epub(
    file_path: Path, title: str = "Test EPUB Book", author: str = "Arthur Conan Doyle"
) -> Path:
    """Creates a minimal valid EPUB 2/3 archive."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    cover_bytes = create_sample_cover_bytes(color="darkblue")

    container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

    content_opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>{title}</dc:title>
    <dc:creator opf:role="aut">{author}</dc:creator>
    <dc:identifier id="BookId">urn:isbn:9781234567890</dc:identifier>
    <dc:language>en</dc:language>
    <dc:date>1892</dc:date>
    <dc:publisher>George Newnes</dc:publisher>
    <dc:description>A classic mystery novel.</dc:description>
    <dc:subject>Mystery</dc:subject>
    <dc:subject>Detective</dc:subject>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""

    toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <docTitle><text>{title}</text></docTitle>
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>Chapter 1: A Scandal in Bohemia</text></navLabel>
      <content src="chapter1.xhtml#chap1"/>
    </navPoint>
    <navPoint id="navPoint-2" playOrder="2">
      <navLabel><text>Chapter 2: The Red-Headed League</text></navLabel>
      <content src="chapter1.xhtml#chap2"/>
    </navPoint>
  </navMap>
</ncx>"""

    chapter1_xhtml = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
  <h1 id="chap1">Chapter 1: A Scandal in Bohemia</h1>
  <p>To Sherlock Holmes she is always THE woman.
  I have seldom heard him mention her under any other name.</p>
  <h1 id="chap2">Chapter 2: The Red-Headed League</h1>
  <p>I had called upon my friend, Mr. Sherlock Holmes, one day in the autumn of last year.</p>
</body>
</html>"""

    with zipfile.ZipFile(file_path, "w") as zf:
        # Mimetype must be uncompressed first entry in EPUB standard
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/toc.ncx", toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr("OEBPS/cover.jpg", cover_bytes, compress_type=zipfile.ZIP_DEFLATED)

    return file_path


def create_sample_pdf(
    file_path: Path, title: str = "Test PDF Document", author: str = "Isaac Asimov"
) -> Path:
    """Creates a sample PDF with metadata, outline bookmarks, and text."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()

    # Add 2 pages with text
    writer.add_blank_page(width=595, height=842)
    writer.add_blank_page(width=595, height=842)

    # Add document outline / TOC
    parent_outline = writer.add_outline_item("Part I: The Psychohistorians", 0)
    writer.add_outline_item("Chapter 1: Gaal Dornick", 0, parent=parent_outline)
    writer.add_outline_item("Chapter 2: Hari Seldon", 1, parent=parent_outline)

    # Add metadata
    writer.add_metadata(
        {
            "/Title": title,
            "/Author": author,
            "/Subject": "Foundation Series Sci-Fi",
            "/Keywords": "Foundation, Seldon, Empire",
            "/CreationDate": "D:19510101000000",
        }
    )

    with open(file_path, "wb") as f:
        writer.write(f)

    return file_path


def create_sample_cbz(file_path: Path, title: str = "Saga Volume 1", series: str = "Saga") -> Path:
    """Creates a sample CBZ comic archive with ComicInfo.xml and pages."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    cover_bytes = create_sample_cover_bytes(color="crimson")
    page_bytes = create_sample_cover_bytes(color="black")

    comic_info = f"""<?xml version="1.0" encoding="utf-8"?>
<ComicInfo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <Title>{title}</Title>
  <Series>{series}</Series>
  <Number>1</Number>
  <Volume>1</Volume>
  <Summary>When two soldiers from opposite sides of a galactic war fall in love...</Summary>
  <Year>2012</Year>
  <Writer>Brian K. Vaughan</Writer>
  <Penciller>Fiona Staples</Penciller>
  <Inker>Fiona Staples</Inker>
  <Colorist>Fiona Staples</Colorist>
  <Letterer>Fonografiks</Letterer>
  <Publisher>Image Comics</Publisher>
  <Genre>Space Opera / Fantasy</Genre>
</ComicInfo>"""

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("ComicInfo.xml", comic_info)
        zf.writestr("000_cover.jpg", cover_bytes)
        zf.writestr("001_page1.jpg", page_bytes)

    return file_path


def create_sample_docx(
    file_path: Path, title: str = "Research Notes", author: str = "Marie Curie"
) -> Path:
    """Creates a sample DOCX document with heading hierarchy."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    doc = docx.Document()
    doc.core_properties.title = title
    doc.core_properties.author = author

    doc.add_heading(title, level=0)
    doc.add_heading("1. Introduction and Hypotheses", level=1)
    doc.add_paragraph("Investigation of the radioactive properties of pitchblende minerals.")
    doc.add_heading("2. Experimental Isolation", level=1)
    doc.add_paragraph(
        "Chemical fractional crystallization of barium chloride carrier precipitates."
    )

    doc.save(file_path)
    return file_path


def create_sample_txt(file_path: Path, title: str = "Cyberpunk Manifesto") -> Path:
    """Creates a sample plain text / markdown file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# {title}

By Christian As. Kirtchev (1997)

## 1. We are the electronic minds

We are the digital wanderers, exploring the vast interconnected networks of the modern era.
Information wants to be free.

## 2. The Net is our Canvas

Boundaries dissolve in cyberspace. Knowledge cannot be chained.
"""
    file_path.write_text(content, encoding="utf-8")
    return file_path


def create_sample_mobi(
    file_path: Path, title: str = "Test MOBI Book", author: str = "Philip K. Dick"
) -> Path:
    """Creates a minimal synthetic MOBI file with EXTH metadata and Palm headers."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    import struct

    # Palm DB header (78 bytes)
    db_name = title.encode("latin-1", errors="ignore")[:31].ljust(32, b"\x00")
    header = bytearray(db_name)
    header.extend(b"\x00" * 44)  # flags, dates, etc.
    header.extend(struct.pack(">H", 1))  # 1 record

    # Record 0 offset table (8 bytes)
    rec_0_offset = 78 + 8  # 86
    header.extend(struct.pack(">I", rec_0_offset))  # offset
    header.extend(b"\x00\x00\x00\x00")  # attributes & uniqueID

    # Record 0 payload
    # PalmDOC (16 bytes)
    rec_0 = bytearray(struct.pack(">HHIHHII", 1, 0, 50, 1, 4096, 0, 0)[:16])
    # MOBI magic (8 bytes)
    rec_0.extend(b"BOOKMOBI")
    # MOBI header length (4 bytes)
    rec_0.extend(struct.pack(">I", 232))
    # Pad to offset 84 for full name offset/length
    rec_0.extend(b"\x00" * (84 - len(rec_0)))

    # Title offset relative to Record 0 start
    title_bytes = title.encode("utf-8")
    title_offset = 300  # Put title at offset 300
    rec_0.extend(struct.pack(">II", title_offset, len(title_bytes)))

    # Pad to 128 for EXTH flag
    rec_0.extend(b"\x00" * (128 - len(rec_0)))
    rec_0.extend(struct.pack(">I", 0x40))  # EXTH exists flag

    # Pad to 248 for EXTH block
    rec_0.extend(b"\x00" * (248 - len(rec_0)))

    # EXTH header: EXTH (4), len (4), count (4)
    author_bytes = author.encode("utf-8")
    exth_records = bytearray()
    # Author (100)
    exth_records.extend(struct.pack(">II", 100, 8 + len(author_bytes)))
    exth_records.extend(author_bytes)
    # Title (503)
    exth_records.extend(struct.pack(">II", 503, 8 + len(title_bytes)))
    exth_records.extend(title_bytes)

    exth_block = bytearray(b"EXTH")
    exth_block.extend(struct.pack(">II", 12 + len(exth_records), 2))
    exth_block.extend(exth_records)
    rec_0.extend(exth_block)

    # Pad to title_offset
    if len(rec_0) < title_offset:
        rec_0.extend(b"\x00" * (title_offset - len(rec_0)))
    rec_0.extend(title_bytes)

    full_data = bytes(header) + bytes(rec_0)
    file_path.write_bytes(full_data)
    return file_path


def create_mock_calibre_library(library_dir: Path) -> Path:
    """Creates a simulated pre-existing Calibre library on disk with metadata.db."""
    import sqlite3

    library_dir.mkdir(parents=True, exist_ok=True)
    db_path = library_dir / "metadata.db"

    conn = sqlite3.connect(db_path)
    # Calibre standard tables only (no x_ extension tables)
    conn.executescript("""
    CREATE TABLE books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        sort TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        pubdate DATETIME,
        series_index REAL DEFAULT 1.0,
        author_sort TEXT,
        isbn TEXT,
        lccn TEXT,
        path TEXT NOT NULL,
        flags INTEGER DEFAULT 1,
        uuid TEXT UNIQUE,
        has_cover INTEGER DEFAULT 1,
        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        sort TEXT,
        link TEXT DEFAULT ''
    );
    CREATE TABLE books_authors_link (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book INTEGER NOT NULL,
        author INTEGER NOT NULL,
        UNIQUE(book, author)
    );
    CREATE TABLE data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book INTEGER NOT NULL,
        format TEXT NOT NULL,
        uncompressed_size INTEGER NOT NULL,
        name TEXT NOT NULL,
        UNIQUE(book, format)
    );
    CREATE TABLE identifiers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book INTEGER NOT NULL,
        type TEXT NOT NULL,
        val TEXT NOT NULL,
        UNIQUE(book, type)
    );
    CREATE TABLE tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    CREATE TABLE books_tags_link (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book INTEGER NOT NULL,
        tag INTEGER NOT NULL,
        UNIQUE(book, tag)
    );
    """)

    # Insert sample authors
    conn.execute("INSERT INTO authors (name, sort) VALUES ('Isaac Asimov', 'Asimov, Isaac')")
    conn.execute("INSERT INTO authors (name, sort) VALUES ('William Gibson', 'Gibson, William')")

    # Insert sample books
    conn.execute("""
    INSERT INTO books (id, title, sort, author_sort, isbn, path, has_cover)
    VALUES (1, 'Foundation', 'Foundation', 'Asimov, Isaac', '9780553293357',
            'Isaac Asimov/Foundation (1951)', 1)
    """)
    conn.execute("""
    INSERT INTO books (id, title, sort, author_sort, isbn, path, has_cover)
    VALUES (2, 'Neuromancer', 'Neuromancer', 'Gibson, William', '9780441569595',
            'William Gibson/Neuromancer (1984)', 1)
    """)

    # Link authors
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (1, 1)")
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (2, 2)")

    # Formats
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) "
        "VALUES (1, 'EPUB', 250000, 'Foundation - Isaac Asimov')"
    )
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) "
        "VALUES (1, 'PDF', 1200000, 'Foundation - Isaac Asimov')"
    )
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) "
        "VALUES (2, 'EPUB', 310000, 'Neuromancer - William Gibson')"
    )

    # Tags
    conn.execute("INSERT INTO tags (name) VALUES ('Sci-Fi')")
    conn.execute("INSERT INTO tags (name) VALUES ('Cyberpunk')")
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (1, 1)")
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (2, 1)")
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (2, 2)")

    conn.commit()
    conn.close()

    # Create directory files on disk
    book1_dir = library_dir / "Isaac Asimov" / "Foundation (1951)"
    book1_dir.mkdir(parents=True, exist_ok=True)
    (book1_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="blue"))
    (book1_dir / "Foundation - Isaac Asimov.epub").write_bytes(b"dummy-epub-bytes")
    (book1_dir / "Foundation - Isaac Asimov.pdf").write_bytes(b"dummy-pdf-bytes")

    book2_dir = library_dir / "William Gibson" / "Neuromancer (1984)"
    book2_dir.mkdir(parents=True, exist_ok=True)
    (book2_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="green"))
    (book2_dir / "Neuromancer - William Gibson.epub").write_bytes(b"dummy-epub-bytes")

    return library_dir
