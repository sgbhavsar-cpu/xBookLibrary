# Technical Research: Audiobook Hub & Whisper Transcription (Feature 014)

## 1. Audio Container & Metadata Parsing (Mutagen)

### M4B (MPEG-4 Audio Book)
- Container: ISO Base Media File Format (MP4 container with `.m4b` extension).
- Audio Codec: AAC (Advanced Audio Coding) or ALAC.
- Metadata Atom Structure:
  - `\xa9nam`: Title
  - `\xa9ART` / `\xa9wrt`: Author / Narrator
  - `\xa9alb`: Album / Book Title
  - `\xa9day`: Year
  - `desc` / `\xa9des` / `ldes`: Synopsis
  - `covr`: Cover art bytes (JPEG / PNG)
  - `chpl` (Nero chapter atom) or text chapter track: Lists chapter title, start time, and duration.
- Library: `mutagen.mp4.MP4` provides full atom inspection and modification.

### MP3 (MPEG-1/2 Audio Layer III)
- Container: Raw bitstream with ID3v2 metadata frames.
- Tags:
  - `TIT2`: Title
  - `TPE1`: Author / Artist
  - `TPE2`: Narrator / Album Artist
  - `TALB`: Album / Series
  - `TDRC` / `TYER`: Year
  - `APIC`: Attached picture (cover art bytes)
  - `CHAP`: Chapter frames (start time, end time, chapter title)
  - `CTOC`: Table of contents frame
- Library: `mutagen.mp3.MP3` and `mutagen.id3.ID3`.

---

## 2. HTTP 206 Partial Content Streaming Protocol
- Modern browsers require HTTP Range requests to support seeking, scrubbing, and duration discovery for `<audio>` tags.
- Client sends: `Range: bytes=start-end` or `Range: bytes=start-`.
- Server behavior:
  - Validates byte range: `0 <= start <= end < file_size`.
  - Content-Length: `end - start + 1`.
  - HTTP Status: `206 Partial Content`.
  - Headers:
    - `Content-Range: bytes {start}-{end}/{total_size}`
    - `Accept-Ranges: bytes`
    - `Content-Length: {length}`
    - `Content-Type: audio/mp4` (M4B) or `audio/mpeg` (MP3)
- Async streaming: Async generator reading chunks (64KB - 256KB) directly from disk file pointer to prevent memory bloat.

---

## 3. Whisper Speech-to-Text Architecture & Segment Alignment
- Multi-provider adapter:
  - `LiteLLMTranscriptionProvider`: Uses `litellm.atranscription` (supports OpenAI Whisper, Groq Whisper, Faster-Whisper, Gemini Audio multimodal).
  - `MockTranscriptionProvider`: Returns predictable timed segments for testing without network or GPU.
- Time-coded segments:
  ```json
  [
    {"start": 0.0, "end": 4.5, "text": "It was a dark and stormy night."},
    {"start": 4.5, "end": 9.2, "text": "The rain fell in torrents, except at occasional intervals."}
  ]
  ```
- Vector Store Synchronization:
  - When a chapter transcript completes, it is passed to `RAGIndexer.chunk_book` with the chapter title and start/end time markers.
  - Chunks include metadata fields: `book_id`, `chapter_index`, `chapter_title`, `timestamp_start`, `timestamp_end`.
  - Citations in RAG answers format as `[Chapter 1: 00:04:15]`.
