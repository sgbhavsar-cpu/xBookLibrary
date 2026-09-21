"""Script to initialize a live sample Calibre library for development and verification."""

import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from backend.config import ConfigManager
from backend.services.library_manager import LibraryManager
from tests.fixtures.generators import (
    create_mock_calibre_library,
    create_sample_epub,
    create_sample_pdf,
    create_sample_cbz,
    create_sample_cover_bytes,
)


async def main():
    repo_root = Path(__file__).resolve().parent.parent
    sample_dir = repo_root / "sample_library"
    import shutil
    shutil.rmtree(sample_dir, ignore_errors=True)
    print(f"Creating sample library at {sample_dir}...")

    # 1. Create base Calibre library structure
    create_mock_calibre_library(sample_dir)

    # 2. Overwrite dummy files with valid readable archives
    book1_dir = sample_dir / "Isaac Asimov" / "Foundation (1951)"
    create_sample_epub(book1_dir / "Foundation - Isaac Asimov.epub", title="Foundation", author="Isaac Asimov")
    create_sample_pdf(book1_dir / "Foundation - Isaac Asimov.pdf", title="Foundation", author="Isaac Asimov")

    book2_dir = sample_dir / "William Gibson" / "Neuromancer (1984)"
    create_sample_epub(book2_dir / "Neuromancer - William Gibson.epub", title="Neuromancer", author="William Gibson")

    # 3. Add a comic book with CBZ
    comic_dir = sample_dir / "Stan Lee" / "Cyberpunk Chronicles (2024)"
    comic_dir.mkdir(parents=True, exist_ok=True)
    create_sample_cbz(comic_dir / "Cyberpunk Chronicles - Stan Lee.cbz", title="Cyberpunk Chronicles #1", series="Cyberpunk Chronicles")

    # Update metadata.db with the comic book
    import sqlite3
    conn = sqlite3.connect(sample_dir / "metadata.db")
    conn.execute("INSERT OR IGNORE INTO authors (name, sort) VALUES ('Stan Lee', 'Lee, Stan')")
    author_id = conn.execute("SELECT id FROM authors WHERE name = 'Stan Lee'").fetchone()[0]
    
    cur = conn.execute(
        "INSERT INTO books (title, sort, author_sort, path, has_cover) VALUES (?, ?, ?, ?, 1)",
        ("Cyberpunk Chronicles #1", "Cyberpunk Chronicles #1", "Lee, Stan", "Stan Lee/Cyberpunk Chronicles (2024)")
    )
    comic_book_id = cur.lastrowid
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (?, ?)", (comic_book_id, author_id))
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'CBZ', 150000, ?)",
        (comic_book_id, "Cyberpunk Chronicles - Stan Lee")
    )
    conn.commit()
    conn.close()

    # 4. Adopt with LibraryManager (augments x_ tables, registers as active)
    mgr = LibraryManager()
    lib = await mgr.adopt_calibre_library(sample_dir, name="Sample Calibre Library", set_active=True)
    print(f"Successfully adopted library: {lib.id} - {lib.name} ({lib.book_count} books)")

    # 5. Clean up stale/non-existent library entries from config
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    existing_libs = [l for l in cfg.libraries if Path(l.path).exists()]
    cfg.libraries = existing_libs
    cfg.active_library_id = lib.id
    cfg_mgr.save(cfg)
    print(f"Config updated: {len(cfg.libraries)} valid libraries, active is {cfg.active_library_id}")


if __name__ == "__main__":
    asyncio.run(main())
