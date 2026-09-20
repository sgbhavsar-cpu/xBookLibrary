import io
import zipfile
import pytest
from pathlib import Path
from PIL import Image

from backend.services.converters import CBZToPdfConverter, TxtToEpubConverter
from backend.services.conversion_service import ConversionService
from backend.services.storage_service import StorageService
from backend.domain.conversion import ConversionStatus, ConversionEngineUsed


def test_txt_to_epub_converter(tmp_path: Path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text(
        "Introduction to Quantum Systems\n\nQuantum superposition allows qubits to represent 0 and 1 simultaneously.\n\nEntanglement correlates states across space.",
        encoding="utf-8",
    )
    epub_file = tmp_path / "sample.epub"

    output_path = TxtToEpubConverter.convert(
        txt_path=txt_file,
        output_epub_path=epub_file,
        title="Quantum Systems",
        author="Richard Feynman",
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    # Validate EPUB structure
    with zipfile.ZipFile(output_path, "r") as z:
        namelist = z.namelist()
        assert "mimetype" in namelist
        assert "META-INF/container.xml" in namelist
        assert "OEBPS/content.opf" in namelist
        assert "OEBPS/chapter1.xhtml" in namelist

        mimetype_info = z.getinfo("mimetype")
        assert mimetype_info.compress_type == zipfile.ZIP_STORED
        assert z.read("mimetype") == b"application/epub+zip"

        chapter_html = z.read("OEBPS/chapter1.xhtml").decode("utf-8")
        assert "Quantum superposition" in chapter_html
        assert "Quantum Systems" in chapter_html


def test_cbz_to_pdf_converter(tmp_path: Path):
    # Create two dummy images
    img1 = Image.new("RGB", (100, 150), color=(255, 0, 0))
    img2 = Image.new("RGB", (100, 150), color=(0, 255, 0))

    cbz_file = tmp_path / "comic.cbz"
    with zipfile.ZipFile(cbz_file, "w") as z:
        b1 = io.BytesIO()
        img1.save(b1, format="JPEG")
        z.writestr("page_001.jpg", b1.getvalue())

        b2 = io.BytesIO()
        img2.save(b2, format="JPEG")
        z.writestr("page_002.jpg", b2.getvalue())

    pdf_file = tmp_path / "comic.pdf"
    output_pdf = CBZToPdfConverter.convert(cbz_file, pdf_file)

    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 100
    # PDF magic bytes
    with open(output_pdf, "rb") as f:
        header = f.read(4)
        assert header == b"%PDF"


from tests.fixtures.generators import create_mock_calibre_library
import sqlite3


@pytest.mark.asyncio
async def test_conversion_service_workflow(tmp_path: Path):
    library_path = tmp_path / "CalibreLib"
    create_mock_calibre_library(library_path)

    # Ensure auxiliary tables exist
    conn = sqlite3.connect(library_path / "metadata.db")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS publishers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, sort TEXT);
    CREATE TABLE IF NOT EXISTS books_publishers_link (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL, publisher INTEGER NOT NULL, UNIQUE(book, publisher));
    CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, book INTEGER NOT NULL UNIQUE, text TEXT);
    CREATE TABLE IF NOT EXISTS x_toc_nodes (id INTEGER PRIMARY KEY AUTOINCREMENT, book_id INTEGER NOT NULL, parent_id INTEGER, title TEXT NOT NULL, level INTEGER DEFAULT 0, page_number INTEGER, anchor_href TEXT, order_index INTEGER DEFAULT 0);
    """)

    # Add a TXT format to Book 1
    book1_dir = library_path / "Isaac Asimov" / "Foundation (1951)"
    txt_file = book1_dir / "Foundation - Isaac Asimov.txt"
    txt_file.write_text("Chapter 1: The Psychohistorians\n\nHari Seldon foresaw the fall.", encoding="utf-8")

    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (1, 'TXT', ?, 'Foundation - Isaac Asimov')",
        (txt_file.stat().st_size,)
    )
    conn.commit()
    conn.close()

    conv_service = ConversionService(library_path)
    job = await conv_service.create_conversion_job(book_id=1, target_format="EPUB", source_format="TXT")
    assert job.status == ConversionStatus.PENDING
    assert job.source_format == "TXT"
    assert job.target_format == "EPUB"

    # Execute conversion
    completed_job = await conv_service.execute_conversion_async(job.id)
    assert completed_job.status == ConversionStatus.COMPLETED
    assert completed_job.engine_used == ConversionEngineUsed.PYTHON_NATIVE
    assert completed_job.percent_complete == 100
    assert completed_job.output_file_path is not None
    assert Path(completed_job.output_file_path).exists()

    # Verify format registered in SQLite
    updated_book = await conv_service.get_book(1)
    assert updated_book is not None
    formats = [f.format for f in updated_book.formats]
    assert "TXT" in formats
    assert "EPUB" in formats

