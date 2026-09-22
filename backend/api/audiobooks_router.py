"""FastAPI endpoints for audiobook streaming, chapter metadata, listening progress, and Whisper transcription."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from backend.domain.audiobook import (
    AudiobookMetadata,
    AudioChapterTranscript,
    AudioListeningProgress,
    AudioListeningProgressUpdateRequest,
    TranscriptExportFormat,
    TranscriptionRequest,
)
from backend.services.audiobook_service import AudiobookService
from backend.services.library_manager import LibraryManager
from backend.services.transcription_service import TranscriptionService

router = APIRouter(tags=["Audiobook Hub & Transcription"])


def get_library_manager() -> LibraryManager:
    return LibraryManager()


def get_audiobook_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
) -> AudiobookService:
    return AudiobookService(library_manager=lib_mgr)


def get_transcription_service(
    lib_mgr: LibraryManager = Depends(get_library_manager),
    audio_service: AudiobookService = Depends(get_audiobook_service),
) -> TranscriptionService:
    return TranscriptionService(
        library_manager=lib_mgr,
        audiobook_service=audio_service,
    )


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/metadata",
    response_model=AudiobookMetadata,
    summary="Get audiobook metadata, narrator, duration, and chapters",
)
async def get_audiobook_metadata(
    library_id: str,
    book_id: int,
    audio_service: AudiobookService = Depends(get_audiobook_service),
):
    meta = await audio_service.get_audiobook_metadata(library_id, book_id)
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audiobook not found or book {book_id} has no M4B/MP3 format",
        )
    return meta


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/stream",
    summary="Stream audiobook with HTTP 206 Partial Content Range support",
)
async def stream_audiobook(
    library_id: str,
    book_id: int,
    format: Optional[str] = Query(None, description="Audio format filter e.g. M4B, MP3"),
    range_header: Optional[str] = Header(None, alias="Range"),
    audio_service: AudiobookService = Depends(get_audiobook_service),
):
    try:
        file_path, mime_type, file_size = await audio_service.get_audio_file(
            library_id, book_id, format_name=format
        )
    except FileNotFoundError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    start, end, content_length = audio_service.parse_range_header(range_header, file_size)

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
        "Content-Type": mime_type,
    }

    status_code = status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK

    return StreamingResponse(
        audio_service.file_chunk_generator(file_path, start, content_length),
        status_code=status_code,
        headers=headers,
        media_type=mime_type,
    )


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/progress",
    response_model=Optional[AudioListeningProgress],
    summary="Get saved listening progress for an audiobook",
)
async def get_audio_progress(
    library_id: str,
    book_id: int,
    audio_service: AudiobookService = Depends(get_audiobook_service),
):
    return await audio_service.get_listening_progress(library_id, book_id)


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/audio/progress",
    response_model=AudioListeningProgress,
    summary="Save listening progress and synchronize Calibre #read_status",
)
async def save_audio_progress(
    library_id: str,
    book_id: int,
    req: AudioListeningProgressUpdateRequest,
    audio_service: AudiobookService = Depends(get_audiobook_service),
):
    return await audio_service.save_listening_progress(library_id, book_id, req)


@router.post(
    "/api/libraries/{library_id}/books/{book_id}/audio/transcribe",
    response_model=List[AudioChapterTranscript],
    summary="Trigger Whisper speech-to-text transcription for chapter(s)",
)
async def transcribe_audiobook(
    library_id: str,
    book_id: int,
    req: TranscriptionRequest,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    try:
        if req.chapter_index is not None:
            t = await transcription_service.transcribe_chapter(
                library_id,
                book_id,
                req.chapter_index,
                model_name=req.model_name or "whisper-1",
                language=req.language,
            )
            return [t]
        else:
            return await transcription_service.transcribe_all_chapters(
                library_id,
                book_id,
                model_name=req.model_name or "whisper-1",
                language=req.language,
            )
    except IndexError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/transcripts",
    response_model=List[AudioChapterTranscript],
    summary="List all generated chapter transcripts for an audiobook",
)
async def list_transcripts(
    library_id: str,
    book_id: int,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    return await transcription_service.get_transcripts(library_id, book_id)


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/transcripts/export",
    summary="Export audiobook transcripts to WebVTT, SubRip, or Markdown",
)
async def export_transcripts(
    library_id: str,
    book_id: int,
    format: str = Query("vtt", description="Export format: vtt, srt, md"),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    try:
        export_fmt = TranscriptExportFormat(format.lower())
    except ValueError:
        export_fmt = TranscriptExportFormat.VTT

    transcripts = await transcription_service.get_transcripts(library_id, book_id)
    if not transcripts:
        # Try generating if none exist
        try:
            transcripts = await transcription_service.transcribe_all_chapters(library_id, book_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No transcripts exist for this audiobook.",
            )

    content = transcription_service.export_transcripts(transcripts, export_fmt)

    media_map = {
        TranscriptExportFormat.VTT: "text/vtt",
        TranscriptExportFormat.SRT: "text/plain",
        TranscriptExportFormat.MD: "text/markdown",
    }
    ext_map = {
        TranscriptExportFormat.VTT: "vtt",
        TranscriptExportFormat.SRT: "srt",
        TranscriptExportFormat.MD: "md",
    }

    return Response(
        content=content,
        media_type=media_map[export_fmt],
        headers={
            "Content-Disposition": f'attachment; filename="transcript_book_{book_id}.{ext_map[export_fmt]}"'
        },
    )


@router.get(
    "/api/libraries/{library_id}/books/{book_id}/audio/transcripts/{chapter_index}",
    response_model=AudioChapterTranscript,
    summary="Get transcript for a single chapter",
)
async def get_chapter_transcript(
    library_id: str,
    book_id: int,
    chapter_index: int,
    transcription_service: TranscriptionService = Depends(get_transcription_service),
):
    tr = await transcription_service.get_chapter_transcript(library_id, book_id, chapter_index)
    if not tr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transcript not found for chapter {chapter_index}",
        )
    return tr
