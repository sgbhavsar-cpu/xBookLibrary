# Feature Specification: Audiobook Hub & Whisper Transcription (Feature 014)

## 1. Executive Summary & Value Proposition
Audiobooks represent the fastest-growing sector of personal and digital libraries. While traditional digital book managers treat audio as unstructured binary files, **xBookLibrary** elevates audiobooks to first-class citizens. Feature 014 equips xBookLibrary with an end-to-end Audiobook Hub: parsing M4B/MP3 formats, extracting embedded chapter markers and narrator metadata, providing HTTP 206 Partial Content range-streaming, syncing listening progress across devices, and leveraging speech-to-text models (Whisper / Gemini) to generate time-aligned transcripts. Transcripts are indexed directly into the library's LanceDB vector store, enabling users to ask conversational RAG questions citing exact spoken timestamps.

---

## 2. User Scenarios & Personas

### Persona: Maya (The Commuter & Deep Reader)
Maya listens to an M4B audiobook on her daily commute. When she gets home, she switches to the web interface. Her listening position is accurately synchronized down to the exact second and chapter.

### Persona: Dr. Julian (The Research Scholar)
Julian is studying an interview and oral history series provided in MP3 format. He uses xBookLibrary's "Transcribe with Whisper" capability. The system generates chapter transcripts with second-by-second timestamps and immediately vector-indexes them. Later, while researching in the RAG chat drawer, xBookLibrary answers his questions citing the exact chapter and audio timestamp (*"At 00:18:45 in Chapter 4"*), complete with a direct jump-to-play button.

---

## 3. Functional Requirements

### 3.1 Format Parsing & Ingestion (`.m4b`, `.mp3`)
- **FR-001**: Ingestion parser MUST recognize `.m4b` and `.mp3` audio files.
- **FR-002**: Parser MUST extract core metadata: Title, Author/Artist, Narrator (`\xa9wrt`, `composer`, or `TPE2`), Release Year, Publisher, and Description.
- **FR-003**: Parser MUST extract audio duration, bitrate, sample rate, and channels.
- **FR-004**: Parser MUST extract embedded artwork (`covr` in MP4 / `APIC` in ID3) and persist as book cover art.
- **FR-005**: Parser MUST extract embedded chapter markers (QuickTime/Nero chapter atoms in M4B, ID3 `CHAP`/`CTOC` frames in MP3) with start times, end times, and titles. If absent, it MUST fall back to generating logical equal intervals or single-chapter cues.

### 3.2 High-Performance Audio Streaming
- **FR-006**: Backend MUST support HTTP 206 Partial Content requests utilizing standard `Range: bytes=start-end` headers.
- **FR-007**: Audio stream MUST respond with `Accept-Ranges: bytes`, `Content-Range`, `Content-Length`, and valid MIME types (`audio/mp4` for M4B, `audio/mpeg` for MP3).
- **FR-008**: Streaming MUST seek instantaneously to any timestamp without buffering the entire file into server RAM.

### 3.3 Listening Progress & Calibre Sync
- **FR-009**: Backend MUST track and persist current playback position (timestamp in seconds, active chapter index, playback speed, progress percentage).
- **FR-010**: System MUST automatically sync Calibre custom column `#read_status` to `"Reading"` on playback initiation, and `"Completed"` when progress exceeds 98%.

### 3.4 Whisper Speech-to-Text Transcription & RAG Vector Indexing
- **FR-011**: System MUST provide an asynchronous transcription service supporting chapter-by-chapter and full-book transcription using LiteLLM (OpenAI Whisper, Groq Whisper, or Gemini Audio) with pluggable test mocking.
- **FR-012**: Transcripts MUST store timestamped word/sentence segments (`start`, `end`, `text`).
- **FR-013**: Transcripts MUST be exportable in WebVTT (`.vtt`), SubRip (`.srt`), and formatted Markdown (`.md`).
- **FR-014**: Generated transcripts MUST be indexed into the library's LanceDB vector store (`.vectors/`), with breadcrumb headers containing chapter names and timestamp ranges.

### 3.5 In-Browser Audio Player & UI Experience
- **FR-015**: A dedicated full-screen Audiobook Player view in `ReaderView` MUST provide playback controls: Play/Pause, Rewind 15s, Fast-Forward 30s, Previous/Next Chapter, Playback Speed selector (0.75x, 1.0x, 1.25x, 1.5x, 1.75x, 2.0x), and Sleep Timer (15m, 30m, 45m, 60m, end of chapter).
- **FR-016**: The player MUST render an interactive chapter drawer allowing instant jumping between chapters.
- **FR-017**: The player MUST render a live Synchronized Transcript panel that automatically highlights and scrolls to the spoken sentence in real time.
- **FR-018**: A persistent bottom mini-player bar MUST remain active in the main library view when an audiobook is playing, allowing uninterrupted listening while browsing.

---

## 4. Success Criteria
1. **Streaming Latency**: Audio seeking with Range requests responds in < 30ms locally.
2. **Progress Persistence**: Reopening an audiobook resumes within 1 second of the last saved timestamp.
3. **Transcript Accuracy & Grounding**: Search or RAG queries against audio transcripts correctly pinpoint the relevant chapter and timestamp.
4. **Zero Regressions**: All 140+ existing unit and contract tests continue to pass with 100% green status.
