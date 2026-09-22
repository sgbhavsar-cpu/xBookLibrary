"""Unit tests for AudiobookParser (M4B and MP3 containers)."""

import tempfile
from pathlib import Path
import pytest
from mutagen.id3 import APIC, ID3, CHAP, COMM, TDRC, TIT2, TPE1, TPE2
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover

from backend.domain.parsers import CorruptedBookError
from backend.parsers import ParserRegistry
from backend.parsers.audio_parser import AudiobookParser


def create_minimal_mp3(file_path: Path, title: str = "Test Title", author: str = "Test Author", narrator: str = "Test Narrator"):
    # Minimal valid MPEG-1 Layer 3 frame
    frame_header = b"\xff\xfb\x90\x64"
    frame_data = frame_header + b"\x00" * (417 - len(frame_header))
    audio_data = frame_data * 15
    file_path.write_bytes(audio_data)

    tags = ID3()
    tags.add(TIT2(encoding=3, text=[title]))
    tags.add(TPE1(encoding=3, text=[author]))
    tags.add(TPE2(encoding=3, text=[narrator]))
    tags.add(TDRC(encoding=3, text=["2023"]))
    tags.add(COMM(encoding=3, lang="eng", desc="", text=["Audiobook description"]))

    # Add APIC (cover)
    tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=b"\xff\xd8\xff\xe0" + b"\x00" * 20))

    # Add chapters
    sub = ID3()
    sub.add(TIT2(encoding=3, text=["Prologue"]))
    chap1 = CHAP(element_id="ch1", start_time=0, end_time=150000, start_offset=0, end_offset=0, sub_frames=sub)
    tags.add(chap1)

    sub2 = ID3()
    sub2.add(TIT2(encoding=3, text=["Chapter 1"]))
    chap2 = CHAP(element_id="ch2", start_time=150000, end_time=300000, start_offset=0, end_offset=0, sub_frames=sub2)
    tags.add(chap2)

    tags.save(file_path)


def create_minimal_m4b(file_path: Path, title: str = "M4B Title", author: str = "M4B Author", narrator: str = "M4B Narrator"):
    def make_box(box_type: bytes, payload: bytes) -> bytes:
        return (len(payload) + 8).to_bytes(4, "big") + box_type + payload

    ftyp = make_box(b"ftyp", b"M4B " + (0).to_bytes(4, "big") + b"M4B mp42isom")
    timescale = 1000
    duration = 5000  # 5 seconds
    mvhd_payload = (
        b"\x00" * 4 + b"\x00" * 4 + b"\x00" * 4 +
        timescale.to_bytes(4, "big") + duration.to_bytes(4, "big") +
        b"\x00\x01\x00\x00\x01\x00" + b"\x00" * 10 +
        b"\x00\x01\x00\x00" + b"\x00" * 12 + b"\x00\x01\x00\x00" + b"\x00" * 12 + b"@\x00\x00\x00" +
        b"\x00" * 24 + (1).to_bytes(4, "big")
    )
    moov = make_box(b"moov", make_box(b"mvhd", mvhd_payload))
    file_path.write_bytes(ftyp + moov)

    audio = MP4(file_path)
    audio.add_tags()
    audio.tags["\xa9nam"] = [title]
    audio.tags["\xa9ART"] = [author]
    audio.tags["\xa9wrt"] = [narrator]
    audio.tags["\xa9day"] = ["2024"]
    audio.tags["desc"] = ["An exciting M4B audiobook adventure."]
    audio.tags["covr"] = [MP4Cover(b"\xff\xd8\xff\xe0" + b"\x00" * 20, imageformat=MP4Cover.FORMAT_JPEG)]
    audio.save()


def test_parser_registry_supports_audiobooks():
    exts = ParserRegistry.get_supported_extensions()
    assert ".m4b" in exts
    assert ".mp3" in exts

    p_m4b = ParserRegistry.get_parser(Path("sample.m4b"))
    assert isinstance(p_m4b, AudiobookParser)

    p_mp3 = ParserRegistry.get_parser(Path("sample.mp3"))
    assert isinstance(p_mp3, AudiobookParser)


def test_parse_mp3_metadata(tmp_path: Path):
    mp3_file = tmp_path / "audiobook.mp3"
    create_minimal_mp3(mp3_file, title="The Hound of the Baskervilles", author="Arthur Conan Doyle", narrator="Stephen Fry")

    parser = AudiobookParser()
    payload = parser.parse(mp3_file)

    assert payload.title == "The Hound of the Baskervilles"
    assert "Arthur Conan Doyle" in payload.authors
    assert payload.publication_year == 2023
    assert payload.description == "Audiobook description"
    assert payload.cover_bytes is not None
    assert payload.cover_mime_type == "image/jpeg"
    assert payload.raw_format == "MP3"
    assert any("Narrator: Stephen Fry" in t for t in payload.tags)
    assert len(payload.table_of_contents) == 2
    assert payload.table_of_contents[0].title == "Prologue"
    assert payload.table_of_contents[1].title == "Chapter 1"


def test_parse_m4b_metadata(tmp_path: Path):
    m4b_file = tmp_path / "detective.m4b"
    create_minimal_m4b(m4b_file, title="A Study in Scarlet", author="Sir Arthur Conan Doyle", narrator="Derek Jacobi")

    parser = AudiobookParser()
    payload = parser.parse(m4b_file)

    assert payload.title == "A Study in Scarlet"
    assert "Sir Arthur Conan Doyle" in payload.authors
    assert payload.publication_year == 2024
    assert payload.description == "An exciting M4B audiobook adventure."
    assert payload.cover_bytes is not None
    assert payload.cover_mime_type == "image/jpeg"
    assert payload.raw_format == "M4B"
    assert any("Narrator: Derek Jacobi" in t for t in payload.tags)
    assert len(payload.table_of_contents) >= 1


def test_parse_non_existent_file_raises():
    parser = AudiobookParser()
    with pytest.raises(CorruptedBookError, match="not found"):
        parser.parse(Path("does_not_exist.m4b"))


def test_parse_invalid_extension_raises(tmp_path: Path):
    wav_file = tmp_path / "test.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 30)
    parser = AudiobookParser()
    with pytest.raises(CorruptedBookError, match="Unsupported audio format"):
        parser.parse(wav_file)
