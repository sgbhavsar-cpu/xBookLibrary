"""MOBI and AZW3 format parser implementation."""

import struct
from pathlib import Path
from typing import Dict, List, Optional

from backend.domain.parsers import (
    BookParserStrategy,
    CorruptedBookError,
    ParsedBookPayload,
)


class MobiParser(BookParserStrategy):
    """Parses PalmDOC / MOBI / AZW3 headers and EXTH records."""

    def parse(self, file_path: Path) -> ParsedBookPayload:
        if not file_path.exists():
            raise CorruptedBookError(f"File not found: {file_path}")

        try:
            data = file_path.read_bytes()
        except Exception as e:
            raise CorruptedBookError(f"Cannot read MOBI file: {e}") from e

        if len(data) < 78:
            raise CorruptedBookError("File too small to be a valid MOBI file")

        # Palm Database Header
        db_name = data[:32].split(b"\x00")[0].decode("latin-1", errors="ignore")
        num_records = struct.unpack(">H", data[76:78])[0]

        if num_records < 1 or len(data) < 78 + num_records * 8:
            raise CorruptedBookError("Invalid Palm record table")

        # Read record offsets
        record_offsets = []
        for i in range(num_records):
            offset = struct.unpack(">I", data[78 + i * 8 : 78 + i * 8 + 4])[0]
            record_offsets.append(offset)

        record_0_offset = record_offsets[0]
        record_0_end = record_offsets[1] if num_records > 1 else len(data)
        record_0 = data[record_0_offset:record_0_end]

        title = db_name if db_name else file_path.stem
        authors: List[str] = []
        pub_year: Optional[int] = None
        identifiers: Dict[str, str] = {}
        cover_bytes: Optional[bytes] = None
        cover_offset_idx: Optional[int] = None

        # Check for MOBI header in Record 0
        if len(record_0) >= 24 and record_0[16:24] == b"BOOKMOBI":
            # Read full title offset
            try:
                full_name_offset = struct.unpack(">I", record_0[84:88])[0]
                full_name_len = struct.unpack(">I", record_0[88:92])[0]
                if full_name_offset + full_name_len <= len(record_0):
                    full_title = record_0[
                        full_name_offset : full_name_offset + full_name_len
                    ].decode("utf-8", errors="ignore")
                    if full_title.strip():
                        title = full_title.strip()
            except Exception:
                pass

            # Parse EXTH Header if present
            try:
                exth_flag = struct.unpack(">I", record_0[128:132])[0]
                if (exth_flag & 0x40) and b"EXTH" in record_0:
                    exth_pos = record_0.index(b"EXTH")
                    record_count = struct.unpack(">I", record_0[exth_pos + 8 : exth_pos + 12])[0]
                    curr_pos = exth_pos + 12

                    for _ in range(record_count):
                        if curr_pos + 8 > len(record_0):
                            break
                        rec_type = struct.unpack(">I", record_0[curr_pos : curr_pos + 4])[0]
                        rec_len = struct.unpack(">I", record_0[curr_pos + 4 : curr_pos + 8])[0]
                        rec_val = record_0[curr_pos + 8 : curr_pos + rec_len]

                        # EXTH 100: Author
                        if rec_type == 100:
                            authors.append(rec_val.decode("utf-8", errors="ignore").strip())
                        # EXTH 503: Updated Title
                        elif rec_type == 503 and rec_val.decode("utf-8", errors="ignore").strip():
                            title = rec_val.decode("utf-8", errors="ignore").strip()
                        # EXTH 104: ISBN
                        elif rec_type == 104:
                            identifiers["isbn"] = rec_val.decode("utf-8", errors="ignore").strip()
                        # EXTH 106: Publication Date
                        elif rec_type == 106:
                            date_str = rec_val.decode("utf-8", errors="ignore").strip()
                            if len(date_str) >= 4 and date_str[:4].isdigit():
                                pub_year = int(date_str[:4])
                        # EXTH 201: CoverOffset
                        elif rec_type == 201:
                            try:
                                cover_offset_idx = struct.unpack(">I", rec_val)[0]
                            except Exception:
                                pass

                        curr_pos += rec_len
            except Exception:
                pass

        # Extract Cover Image from Record if offset is found
        if cover_offset_idx is not None:
            # The cover image record is indexed from first_image_index + cover_offset_idx
            # Or directly as a Palm record index
            try:
                target_rec = cover_offset_idx
                if target_rec < len(record_offsets):
                    rec_start = record_offsets[target_rec]
                    rec_end = (
                        record_offsets[target_rec + 1]
                        if target_rec + 1 < len(record_offsets)
                        else len(data)
                    )
                    candidate = data[rec_start:rec_end]
                    # Check for JPEG or PNG magic bytes
                    if candidate.startswith(b"\xff\xd8\xff") or candidate.startswith(b"\x89PNG"):
                        cover_bytes = candidate
            except Exception:
                pass

        if not authors:
            authors = ["Unknown Author"]

        return ParsedBookPayload(
            title=title,
            authors=authors,
            publication_year=pub_year,
            identifiers=identifiers,
            cover_bytes=cover_bytes,
            cover_mime_type="image/jpeg",
            raw_format="MOBI",
        )
