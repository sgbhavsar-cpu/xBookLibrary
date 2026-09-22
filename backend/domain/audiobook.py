"""Domain models and request/response schemas for audiobooks and transcription."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptExportFormat(str, Enum):
    VTT = "vtt"
    SRT = "srt"
    MD = "md"


class AudioChapter(BaseModel):
    """Represents a chapter or track in an audiobook with precise start and end times."""

    index: int
    title: str
    start_time: float = Field(..., description="Start offset in seconds from audio beginning")
    end_time: float = Field(..., description="End offset in seconds")
    duration: float = Field(..., description="Duration in seconds")


class AudiobookMetadata(BaseModel):
    """Normalized technical and bibliographic metadata for an audiobook."""

    book_id: int
    format: str = Field(..., description="File format e.g. M4B, MP3")
    duration_seconds: float = Field(default=0.0, description="Total audio length in seconds")
    bitrate: Optional[int] = Field(default=None, description="Audio bitrate in kbps or bps")
    sample_rate: Optional[int] = Field(default=None, description="Sampling rate in Hz")
    channels: Optional[int] = Field(default=None, description="Channel count e.g. 1=mono, 2=stereo")
    narrator: Optional[str] = Field(default=None, description="Spoken voice artist / narrator")
    chapters: List[AudioChapter] = Field(default_factory=list)


class AudioListeningProgress(BaseModel):
    """Current playback state and cross-session position for an audiobook."""

    book_id: int
    format: str
    current_time: float = Field(default=0.0, description="Current playback timestamp in seconds")
    current_chapter_index: int = Field(default=0, description="Active chapter index")
    progress_percent: float = Field(default=0.0, description="Percentage of total book listened (0-100)")
    playback_speed: float = Field(default=1.0, description="Playback speed multiplier")
    is_finished: bool = Field(default=False, description="True if listened to completion (>98%)")
    last_listened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AudioListeningProgressUpdateRequest(BaseModel):
    """Payload to update an audiobook's listening progress."""

    current_time: float
    current_chapter_index: Optional[int] = 0
    progress_percent: Optional[float] = None
    playback_speed: Optional[float] = 1.0


class AudioTranscriptSegment(BaseModel):
    """Fine-grained timestamped transcription segment."""

    start: float = Field(..., description="Start timestamp in seconds")
    end: float = Field(..., description="End timestamp in seconds")
    text: str = Field(..., description="Spoken text in this interval")


class AudioChapterTranscript(BaseModel):
    """Full transcript of a specific chapter with fine-grained segments."""

    id: str
    book_id: int
    chapter_index: int
    chapter_title: str
    start_time: float
    end_time: float
    transcript_text: str
    segments: List[AudioTranscriptSegment] = Field(default_factory=list)
    model_used: str = "whisper-1"
    status: str = "completed"  # pending, completed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TranscriptionRequest(BaseModel):
    """Payload to trigger speech-to-text transcription."""

    book_id: int
    chapter_index: Optional[int] = Field(
        default=None, description="If provided, transcribes only this chapter. Otherwise transcribes all."
    )
    model_name: Optional[str] = Field(default="whisper-1", description="Transcription model to invoke")
    language: Optional[str] = Field(default=None, description="Optional language ISO code hint e.g. 'en'")
