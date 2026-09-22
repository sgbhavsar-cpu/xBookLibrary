"""Script to initialize a rich sample Calibre library for development and end-to-end verification."""

import asyncio
import json
import shutil
import sqlite3
import sys
import uuid
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from mutagen.id3 import APIC, ID3, CHAP, COMM, TDRC, TIT2, TPE1, TPE2

from backend.config import ConfigManager
from backend.database.schema import CALIBRE_SCHEMA_DDL
from backend.services.library_manager import LibraryManager
from backend.services.custom_columns_service import CustomColumnsService
from tests.fixtures.generators import (
    create_mock_calibre_library,
    create_sample_cbz,
    create_sample_cover_bytes,
    create_sample_epub,
    create_sample_pdf,
)


def create_sample_audiobook(file_path: Path, title: str, author: str, narrator: str):
    """Creates a valid, seekable MP3 file with ID3 tags, embedded cover, and chapter markers."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    frame_header = b"\xff\xfb\x90\x64"
    frame_data = frame_header + b"\x00" * (417 - len(frame_header))
    # 300 seconds worth of audio frames
    audio_data = frame_data * 100
    file_path.write_bytes(audio_data)

    tags = ID3()
    tags.add(TIT2(encoding=3, text=[title]))
    tags.add(TPE1(encoding=3, text=[author]))
    tags.add(TPE2(encoding=3, text=[narrator]))
    tags.add(TDRC(encoding=3, text=["2024"]))
    tags.add(COMM(encoding=3, lang="eng", desc="", text=["Masterpiece epic sci-fi audiobook."]))
    tags.add(
        APIC(
            encoding=3,
            mime="image/jpeg",
            type=3,
            desc="Cover",
            data=create_sample_cover_bytes(width=400, height=400, color="darkorange"),
        )
    )

    # Add chapter markers
    sub1 = ID3()
    sub1.add(TIT2(encoding=3, text=["Prologue: Arrakis"]))
    tags.add(CHAP(element_id="ch1", start_time=0, end_time=60000, start_offset=0, end_offset=0, sub_frames=sub1))

    sub2 = ID3()
    sub2.add(TIT2(encoding=3, text=["Chapter 1: The Gom Jabbar"]))
    tags.add(CHAP(element_id="ch2", start_time=60000, end_time=180000, start_offset=0, end_offset=0, sub_frames=sub2))

    sub3 = ID3()
    sub3.add(TIT2(encoding=3, text=["Chapter 2: Departure for Dune"]))
    tags.add(CHAP(element_id="ch3", start_time=180000, end_time=300000, start_offset=0, end_offset=0, sub_frames=sub3))

    tags.save(file_path)


async def main():
    sample_dir = repo_root / "sample_library"
    shutil.rmtree(sample_dir, ignore_errors=True)
    print(f"Creating rich demo library at {sample_dir}...")

    # 1. Base Calibre structure
    create_mock_calibre_library(sample_dir)

    # 2. Book 1: Foundation (Asimov) - EPUB + PDF
    book1_dir = sample_dir / "Isaac Asimov" / "Foundation (1951)"
    create_sample_epub(book1_dir / "Foundation - Isaac Asimov.epub", title="Foundation", author="Isaac Asimov")
    create_sample_pdf(book1_dir / "Foundation - Isaac Asimov.pdf", title="Foundation", author="Isaac Asimov")
    (book1_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="darkblue"))

    # 3. Book 2: Neuromancer (Gibson) - EPUB
    book2_dir = sample_dir / "William Gibson" / "Neuromancer (1984)"
    create_sample_epub(book2_dir / "Neuromancer - William Gibson.epub", title="Neuromancer", author="William Gibson")
    (book2_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="darkcyan"))

    # 4. Book 3: Cyberpunk Chronicles #1 (Lee) - CBZ Comic
    comic_dir = sample_dir / "Stan Lee" / "Cyberpunk Chronicles (2024)"
    comic_dir.mkdir(parents=True, exist_ok=True)
    create_sample_cbz(comic_dir / "Cyberpunk Chronicles - Stan Lee.cbz", title="Cyberpunk Chronicles #1", series="Cyberpunk Chronicles")
    (comic_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="purple"))

    # 5. Book 4: Dune (Herbert) - MP3 Audiobook
    dune_dir = sample_dir / "Frank Herbert" / "Dune (1965)"
    dune_dir.mkdir(parents=True, exist_ok=True)
    dune_mp3 = dune_dir / "Dune - Frank Herbert.mp3"
    create_sample_audiobook(dune_mp3, title="Dune", author="Frank Herbert", narrator="Scott Brick & Orlagh Cassidy")
    (dune_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="darkgoldenrod"))

    # 6. Book 5: Snow Crash (Stephenson) - EPUB
    snow_dir = sample_dir / "Neal Stephenson" / "Snow Crash (1992)"
    snow_dir.mkdir(parents=True, exist_ok=True)
    create_sample_epub(snow_dir / "Snow Crash - Neal Stephenson.epub", title="Snow Crash", author="Neal Stephenson")
    (snow_dir / "cover.jpg").write_bytes(create_sample_cover_bytes(color="crimson"))

    # Populate metadata.db
    conn = sqlite3.connect(sample_dir / "metadata.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(CALIBRE_SCHEMA_DDL)

    # Add authors
    authors_data = [
        ("Isaac Asimov", "Asimov, Isaac"),
        ("William Gibson", "Gibson, William"),
        ("Stan Lee", "Lee, Stan"),
        ("Frank Herbert", "Herbert, Frank"),
        ("Neal Stephenson", "Stephenson, Neal"),
    ]
    for name, sort in authors_data:
        conn.execute("INSERT OR IGNORE INTO authors (name, sort) VALUES (?, ?)", (name, sort))

    def get_author_id(name: str) -> int:
        return conn.execute("SELECT id FROM authors WHERE name = ?", (name,)).fetchone()[0]

    # Add tags
    all_tags = ["Science Fiction", "Cyberpunk", "Classics", "Audiobook", "Comics", "AI", "Metaverse"]
    for t in all_tags:
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (t,))

    def get_tag_id(tag: str) -> int:
        return conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()[0]

    # Add series
    series_data = ["Foundation", "Sprawl Trilogy", "Cyberpunk Chronicles", "Dune Saga"]
    for s in series_data:
        conn.execute("INSERT OR IGNORE INTO series (name, sort) VALUES (?, ?)", (s, s))

    def get_series_id(name: str) -> int:
        return conn.execute("SELECT id FROM series WHERE name = ?", (name,)).fetchone()[0]

    # Insert Comic (Cyberpunk Chronicles)
    cur = conn.execute(
        "INSERT INTO books (title, sort, author_sort, path, has_cover, series_index) VALUES (?, ?, ?, ?, 1, 1.0)",
        ("Cyberpunk Chronicles #1", "Cyberpunk Chronicles #1", "Lee, Stan", "Stan Lee/Cyberpunk Chronicles (2024)"),
    )
    comic_id = cur.lastrowid
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (?, ?)", (comic_id, get_author_id("Stan Lee")))
    conn.execute("INSERT INTO books_series_link (book, series) VALUES (?, ?)", (comic_id, get_series_id("Cyberpunk Chronicles")))
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", (comic_id, get_tag_id("Comics")))
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'CBZ', 150000, ?)",
        (comic_id, "Cyberpunk Chronicles - Stan Lee"),
    )

    # Insert Audiobook (Dune)
    cur = conn.execute(
        "INSERT INTO books (title, sort, author_sort, path, has_cover, series_index) VALUES (?, ?, ?, ?, 1, 1.0)",
        ("Dune", "Dune", "Herbert, Frank", "Frank Herbert/Dune (1965)"),
    )
    dune_id = cur.lastrowid
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (?, ?)", (dune_id, get_author_id("Frank Herbert")))
    conn.execute("INSERT INTO books_series_link (book, series) VALUES (?, ?)", (dune_id, get_series_id("Dune Saga")))
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", (dune_id, get_tag_id("Audiobook")))
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", (dune_id, get_tag_id("Science Fiction")))
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'MP3', 4500000, ?)",
        (dune_id, "Dune - Frank Herbert"),
    )
    conn.execute(
        "INSERT INTO comments (book, text) VALUES (?, ?)",
        (dune_id, "<p>Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, heir to a noble family tasked with ruling an inhospitable world where the only thing of value is the 'spice' melange.</p>"),
    )

    # Insert Snow Crash
    cur = conn.execute(
        "INSERT INTO books (title, sort, author_sort, path, has_cover, series_index) VALUES (?, ?, ?, ?, 1, 1.0)",
        ("Snow Crash", "Snow Crash", "Stephenson, Neal", "Neal Stephenson/Snow Crash (1992)"),
    )
    snow_id = cur.lastrowid
    conn.execute("INSERT INTO books_authors_link (book, author) VALUES (?, ?)", (snow_id, get_author_id("Neal Stephenson")))
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", (snow_id, get_tag_id("Cyberpunk")))
    conn.execute("INSERT INTO books_tags_link (book, tag) VALUES (?, ?)", (snow_id, get_tag_id("Metaverse")))
    conn.execute(
        "INSERT INTO data (book, format, uncompressed_size, name) VALUES (?, 'EPUB', 320000, ?)",
        (snow_id, "Snow Crash - Neal Stephenson"),
    )
    conn.execute(
        "INSERT INTO comments (book, text) VALUES (?, ?)",
        (snow_id, "<p>In reality, Hiro Protagonist delivers pizza for Uncle Enzo's Coso Nostra Pizza Inc. But in the Metaverse he's a warrior prince.</p>"),
    )

    # Link tags and series to Foundation (ID 1) and Neuromancer (ID 2)
    conn.execute("INSERT OR IGNORE INTO books_series_link (book, series) VALUES (1, ?)", (get_series_id("Foundation"),))
    conn.execute("UPDATE books SET series_index = 1.0 WHERE id = 1")
    conn.execute("INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (1, ?)", (get_tag_id("Science Fiction"),))
    conn.execute("INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (1, ?)", (get_tag_id("Classics"),))

    conn.execute("INSERT OR IGNORE INTO books_series_link (book, series) VALUES (2, ?)", (get_series_id("Sprawl Trilogy"),))
    conn.execute("UPDATE books SET series_index = 1.0 WHERE id = 2")
    conn.execute("INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (2, ?)", (get_tag_id("Cyberpunk"),))
    conn.execute("INSERT OR IGNORE INTO books_tags_link (book, tag) VALUES (2, ?)", (get_tag_id("AI"),))

    conn.commit()
    conn.close()

    # 7. Adopt library with LibraryManager
    mgr = LibraryManager()
    lib = await mgr.adopt_calibre_library(sample_dir, name="Demo Master Library", set_active=True)
    print(f"Successfully adopted library: {lib.id} - {lib.name} ({lib.book_count} books)")

    # 8. Install Custom Columns Presets (#read_status, #difficulty, #rating, #pages)
    cc_service = CustomColumnsService()
    await cc_service.install_default_presets(sample_dir)
    print("Installed standard custom columns presets (#read_status, #difficulty, #rating, #pages).")

    # Set custom values for the demo books
    await cc_service.set_book_custom_values(sample_dir, 1, {
        "read_status": "Reading",
        "rating": 5,
        "pages": 255,
        "difficulty": "Introductory",
    })
    await cc_service.set_book_custom_values(sample_dir, 2, {
        "read_status": "Completed",
        "rating": 5,
        "pages": 271,
        "difficulty": "Intermediate",
    })
    await cc_service.set_book_custom_values(sample_dir, dune_id, {
        "read_status": "Reading",
        "rating": 5,
        "pages": 896,
        "difficulty": "Advanced",
    })
    await cc_service.set_book_custom_values(sample_dir, snow_id, {
        "read_status": "Unread",
        "rating": 4,
        "pages": 480,
    })
    print("Populated rich custom column values for demo books.")

    # 9. Seed Audiobook Technical Metadata, Progress, and Live Whisper Transcript
    conn = sqlite3.connect(sample_dir / "metadata.db")
    chapters_json = json.dumps([
        {"index": 0, "title": "Prologue: Arrakis", "start_time": 0.0, "end_time": 60.0, "duration": 60.0},
        {"index": 1, "title": "Chapter 1: The Gom Jabbar", "start_time": 60.0, "end_time": 180.0, "duration": 120.0},
        {"index": 2, "title": "Chapter 2: Departure for Dune", "start_time": 180.0, "end_time": 300.0, "duration": 120.0},
    ])
    conn.execute(
        """INSERT OR REPLACE INTO x_audiobook_metadata 
           (book_id, format, duration_seconds, bitrate, sample_rate, channels, narrator, chapters_json)
           VALUES (?, 'MP3', 300.0, 128000, 44100, 2, 'Scott Brick & Orlagh Cassidy', ?)""",
        (dune_id, chapters_json),
    )

    # Seed listening progress (at 75 seconds in Chapter 1)
    conn.execute(
        """INSERT OR REPLACE INTO x_reading_progress
           (book_id, format, location, progress_percent, total_seconds, last_read_at)
           VALUES (?, 'MP3', ?, 25.0, 75, CURRENT_TIMESTAMP)""",
        (dune_id, json.dumps({"current_time": 75.0, "current_chapter_index": 1, "playback_speed": 1.0})),
    )

    # Seed Live Whisper transcript for Chapter 1
    segments_json = json.dumps([
        {"start": 60.0, "end": 75.0, "text": "A beginning is the time for taking the most delicate care that the balances are correct."},
        {"start": 75.0, "end": 90.0, "text": "This every sister of the Bene Gesserit knows."},
        {"start": 90.0, "end": 110.0, "text": "To begin your study of the life of Muad'Dib, then, take care that you first place him in his time..."},
        {"start": 110.0, "end": 130.0, "text": "Born in the fifty-seventh year of the Padishah Emperor, Shaddam IV."},
        {"start": 130.0, "end": 180.0, "text": "And take the most special care that you locate him in his place: the planet Arrakis, the world known as Dune."},
    ])
    conn.execute(
        """INSERT OR REPLACE INTO x_audio_transcripts
           (id, book_id, chapter_index, chapter_title, start_time, end_time, transcript_text, segments_json, model_used, status)
           VALUES (?, ?, 1, 'Chapter 1: The Gom Jabbar', 60.0, 180.0, ?, ?, 'whisper-1', 'completed')""",
        (
            str(uuid.uuid4()),
            dune_id,
            "A beginning is the time for taking the most delicate care that the balances are correct. This every sister of the Bene Gesserit knows. To begin your study of the life of Muad'Dib, then, take care that you first place him in his time. Born in the fifty-seventh year of the Padishah Emperor, Shaddam IV. And take the most special care that you locate him in his place: the planet Arrakis, the world known as Dune.",
            segments_json,
        ),
    )

    # Seed annotations for Foundation (ID 1)
    conn.execute(
        """INSERT OR REPLACE INTO x_annotations
           (id, book_id, format, location, selected_text, color, note_text, chapter_title)
           VALUES (?, 1, 'EPUB', 'chapter1.xhtml#chap1', 'To Sherlock Holmes she is always THE woman.', 'yellow', 'Fascinating character opening.', 'Chapter 1')""",
        (str(uuid.uuid4()),),
    )

    # 10. Seed Virtual Libraries in Calibre preferences
    virtual_libs = {
        "Science Fiction": 'tags:"=Science Fiction" or tags:"=Cyberpunk"',
        "Currently Reading": '#read_status:"=Reading"',
        "Audiobooks": 'format:"=MP3" or format:"=M4B"',
    }
    conn.execute(
        "INSERT OR REPLACE INTO preferences (key, val) VALUES ('virtual_libraries', ?)",
        (json.dumps(virtual_libs),),
    )

    # 11. Seed sample e-reader device
    conn.execute(
        """INSERT OR REPLACE INTO x_devices
           (id, name, device_type, target_address, created_at)
           VALUES (?, 'Kindle Oasis', 'kindle', 'demo.reader@kindle.com', CURRENT_TIMESTAMP)""",
        (str(uuid.uuid4()),),
    )

    conn.commit()
    conn.close()
    print("Configured virtual libraries, annotations, and sample devices.")

    # 12. Update app config
    cfg_mgr = ConfigManager()
    cfg = cfg_mgr.load()
    existing_libs = [l for l in cfg.libraries if Path(l.path).exists()]
    cfg.libraries = existing_libs
    cfg.active_library_id = lib.id
    cfg_mgr.save(cfg)
    print(f"\nAll set! Active Library: {lib.name} ({lib.id}) at {sample_dir}")
    print(f"Total Books: {lib.book_count}")


if __name__ == "__main__":
    asyncio.run(main())
