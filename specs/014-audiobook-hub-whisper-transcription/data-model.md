# Data Model: Audiobook Hub & Whisper Transcription (Feature 014)

## 1. Relational Schema Extensions (`metadata.db`)

### `x_audiobook_metadata`
```sql
CREATE TABLE IF NOT EXISTS x_audiobook_metadata (
    book_id INTEGER PRIMARY KEY,
    format TEXT NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0.0,
    bitrate INTEGER,
    sample_rate INTEGER,
    channels INTEGER,
    narrator TEXT,
    chapters_json TEXT NOT NULL DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_x_audiobook_metadata_format ON x_audiobook_metadata (format);
```

### `x_audio_transcripts`
```sql
CREATE TABLE IF NOT EXISTS x_audio_transcripts (
    id TEXT PRIMARY KEY,
    book_id INTEGER NOT NULL,
    chapter_index INTEGER NOT NULL,
    chapter_title TEXT NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    transcript_text TEXT NOT NULL,
    segments_json TEXT NOT NULL DEFAULT '[]',
    model_used TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_x_audio_transcripts_book_ch ON x_audio_transcripts (book_id, chapter_index);
```

---

## 2. Python Domain Entities (`backend/domain/audiobook.py`)

```python
class AudioChapter(BaseModel):
    index: int
    title: str
    start_time: float
    end_time: float
    duration: float

class AudiobookMetadata(BaseModel):
    book_id: int
    format: str
    duration_seconds: float
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    narrator: Optional[str] = None
    chapters: List[AudioChapter] = []

class AudioListeningProgress(BaseModel):
    book_id: int
    format: str
    current_time: float
    current_chapter_index: int
    progress_percent: float
    playback_speed: float
    is_finished: bool
    last_listened_at: datetime

class AudioTranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class AudioChapterTranscript(BaseModel):
    id: str
    book_id: int
    chapter_index: int
    chapter_title: str
    start_time: float
    end_time: float
    transcript_text: str
    segments: List[AudioTranscriptSegment] = []
    model_used: str
    status: str
    created_at: datetime
```
