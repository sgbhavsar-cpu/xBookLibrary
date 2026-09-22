"""Audiobook parser strategy supporting M4B and MP3 audio containers."""

import re
from pathlib import Path
from typing import List, Optional

import mutagen
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
    TocItem,
)


class AudiobookParser(BookParserStrategy):
    """Extracts bibliographic metadata, artwork, duration, and chapters from M4B and MP3 files."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"Audiobook file not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext == ".m4b" or ext == ".mp4":
            return self._parse_m4b(file_path)
        elif ext == ".mp3":
            return self._parse_mp3(file_path)
        else:
            raise CorruptedBookError(f"Unsupported audio format: {ext}")

    def _parse_m4b(self, file_path: Path) -> ParsedBookPayload:
        try:
            audio = MP4(file_path)
        except Exception as e:
            raise CorruptedBookError(f"Failed to parse M4B file: {e}") from e

        tags = audio.tags or {}

        # 1. Title
        title_list = tags.get("\xa9nam") or []
        title = str(title_list[0]).strip() if title_list else file_path.stem

        # 2. Authors & Narrator
        artist_list = tags.get("\xa9ART") or []
        writer_list = tags.get("\xa9wrt") or []
        authors = [str(a).strip() for a in artist_list if str(a).strip()]
        if not authors and writer_list:
            authors = [str(w).strip() for w in writer_list if str(w).strip()]
        if not authors:
            authors = ["Unknown"]

        narrator = str(writer_list[0]).strip() if writer_list else None

        # 3. Year
        year_list = tags.get("\xa9day") or []
        year: Optional[int] = None
        if year_list:
            match = re.search(r"\b(19\d\d|20\d\d)\b", str(year_list[0]))
            if match:
                year = int(match.group(1))

        # 4. Description
        desc_list = tags.get("desc") or tags.get("\xa9des") or tags.get("ldes") or []
        description = str(desc_list[0]).strip() if desc_list else None

        # 5. Cover art
        cover_bytes: Optional[bytes] = None
        cover_mime_type: Optional[str] = None
        covr_list = tags.get("covr") or []
        if covr_list:
            raw_cover = covr_list[0]
            cover_bytes = bytes(raw_cover)
            if hasattr(raw_cover, "imageformat") and raw_cover.imageformat == MP4Cover.FORMAT_PNG:
                cover_mime_type = "image/png"
            elif cover_bytes.startswith(b"\x89PNG"):
                cover_mime_type = "image/png"
            else:
                cover_mime_type = "image/jpeg"

        # 6. Duration & Chapters
        duration = float(getattr(audio.info, "length", 0.0))
        toc: List[TocItem] = []

        # Check for embedded chapters in mutagen MP4
        if hasattr(audio, "chapters") and audio.chapters:
            for idx, ch in enumerate(audio.chapters):
                ch_title = getattr(ch, "title", f"Chapter {idx + 1}")
                start_sec = getattr(ch, "start", 0) / 1000.0 if getattr(ch, "start", 0) > 1000 else getattr(ch, "start", 0)
                toc.append(
                    TocItem(
                        title=str(ch_title),
                        level=0,
                        anchor_href=f"t={int(start_sec)}",
                    )
                )

        if not toc:
            # Fallback: create single chapter or logical 15-minute chapters if long
            if duration > 1800:  # > 30 minutes
                interval = 900.0  # 15 minutes
                num_parts = max(1, int(duration // interval) + (1 if duration % interval > 0 else 0))
                for i in range(num_parts):
                    start_s = i * interval
                    toc.append(
                        TocItem(
                            title=f"Part {i + 1}",
                            level=0,
                            anchor_href=f"t={int(start_s)}",
                        )
                    )
            else:
                toc.append(TocItem(title="Audiobook", level=0, anchor_href="t=0"))

        tags_out = ["Audiobook"]
        if narrator:
            tags_out.append(f"Narrator: {narrator}")

        sample_text = (
            f"Audiobook: {title} by {', '.join(authors)}. "
            f"Duration: {int(duration // 60)} minutes {int(duration % 60)} seconds. "
            f"{('Narrated by ' + narrator + '.') if narrator else ''} "
            f"{description or ''}"
        )

        return ParsedBookPayload(
            title=title,
            authors=authors,
            publication_year=year,
            description=description,
            cover_bytes=cover_bytes,
            cover_mime_type=cover_mime_type,
            table_of_contents=toc,
            tags=tags_out,
            sample_text=sample_text,
            raw_format="M4B",
        )

    def _parse_mp3(self, file_path: Path) -> ParsedBookPayload:
        try:
            audio = MP3(file_path)
        except Exception as e:
            raise CorruptedBookError(f"Failed to parse MP3 file: {e}") from e

        tags = audio.tags or ID3()

        # 1. Title
        title_frame = tags.get("TIT2")
        title = str(title_frame.text[0]).strip() if (title_frame and title_frame.text) else file_path.stem

        # 2. Authors & Narrator
        author_frame = tags.get("TPE1")
        authors = [str(a).strip() for a in author_frame.text if str(a).strip()] if (author_frame and author_frame.text) else ["Unknown"]

        narrator_frame = tags.get("TPE2")
        narrator = str(narrator_frame.text[0]).strip() if (narrator_frame and narrator_frame.text) else None

        # 3. Year
        year: Optional[int] = None
        for year_tag in ["TDRC", "TYER"]:
            y_frame = tags.get(year_tag)
            if y_frame and y_frame.text:
                match = re.search(r"\b(19\d\d|20\d\d)\b", str(y_frame.text[0]))
                if match:
                    year = int(match.group(1))
                    break

        # 4. Description
        description: Optional[str] = None
        for key in tags.keys():
            if key.startswith("COMM"):
                comm_frame = tags[key]
                if comm_frame and getattr(comm_frame, "text", None):
                    description = str(comm_frame.text[0]).strip()
                    break

        # 5. Cover art (APIC)
        cover_bytes: Optional[bytes] = None
        cover_mime_type: Optional[str] = None
        for key in tags.keys():
            if key.startswith("APIC"):
                apic = tags[key]
                cover_bytes = apic.data
                cover_mime_type = getattr(apic, "mime", "image/jpeg")
                break

        # 6. Duration & Chapters (CHAP frames)
        duration = float(getattr(audio.info, "length", 0.0))
        toc: List[TocItem] = []

        for key in sorted(tags.keys()):
            if key.startswith("CHAP"):
                chap = tags[key]
                start_ms = getattr(chap, "start_time", 0)
                start_sec = start_ms / 1000.0
                chap_title = f"Chapter {len(toc) + 1}"
                if hasattr(chap, "sub_frames"):
                    tit2 = chap.sub_frames.get("TIT2")
                    if tit2 and tit2.text:
                        chap_title = str(tit2.text[0]).strip()
                toc.append(
                    TocItem(
                        title=chap_title,
                        level=0,
                        anchor_href=f"t={int(start_sec)}",
                    )
                )

        if not toc:
            if duration > 1800:
                interval = 900.0
                num_parts = max(1, int(duration // interval) + (1 if duration % interval > 0 else 0))
                for i in range(num_parts):
                    start_s = i * interval
                    toc.append(TocItem(title=f"Part {i + 1}", level=0, anchor_href=f"t={int(start_s)}"))
            else:
                toc.append(TocItem(title="Audiobook", level=0, anchor_href="t=0"))

        tags_out = ["Audiobook"]
        if narrator:
            tags_out.append(f"Narrator: {narrator}")

        sample_text = (
            f"Audiobook: {title} by {', '.join(authors)}. "
            f"Duration: {int(duration // 60)} minutes {int(duration % 60)} seconds. "
            f"{('Narrated by ' + narrator + '.') if narrator else ''} "
            f"{description or ''}"
        )

        return ParsedBookPayload(
            title=title,
            authors=authors,
            publication_year=year,
            description=description,
            cover_bytes=cover_bytes,
            cover_mime_type=cover_mime_type,
            table_of_contents=toc,
            tags=tags_out,
            sample_text=sample_text,
            raw_format="MP3",
        )
