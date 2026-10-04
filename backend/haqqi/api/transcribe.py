"""POST /v1/transcribe (task 6.1): a short voice recording → text for the story box.

The audio is held in memory for one request and never stored or logged; neither is the transcript.
"""

import logging
from functools import cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from haqqi.config import get_settings
from haqqi.models import Language
from haqqi.speech import SpeechError, Transcriber, get_transcriber

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1")
UNAVAILABLE = "Voice input is not available right now. Please type your story."

# About 3 minutes of browser speech (Opus or AAC at up to ~128 kbit/s); the UI stops at 2 minutes.
MAX_AUDIO_BYTES = 3 * 1024 * 1024
# What MediaRecorder produces on Chrome/Android (webm/ogg) and iPhone Safari (mp4/aac), plus files.
AUDIO_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/x-m4a",
    "audio/aac",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "video/webm",  # some browsers label audio-only WebM this way
}


class TranscribeResult(BaseModel):
    text: str
    detected_language: str | None


@cache
def get_transcriber_dep() -> Transcriber | None:
    return get_transcriber(get_settings())


@router.post("/transcribe")
async def transcribe(
    audio: Annotated[UploadFile, File()],
    transcriber: Annotated[Transcriber | None, Depends(get_transcriber_dep)],
    language: Annotated[Language | None, Form()] = None,
) -> TranscribeResult:
    if transcriber is None:
        raise HTTPException(503, UNAVAILABLE)
    media_type = (audio.content_type or "").split(";")[0].strip().lower()
    if media_type not in AUDIO_TYPES:
        raise HTTPException(415, "Unsupported audio format.")
    data = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(413, "The recording is too long. Please keep it under 2 minutes.")
    if not data:
        raise HTTPException(422, "The recording is empty.")
    try:
        result = transcriber.transcribe(data, language)
    except SpeechError as exc:
        log.warning("transcribe failed: %s", exc)  # no audio, no text
        raise HTTPException(503, UNAVAILABLE) from None
    log.info("transcribe ok: %d bytes, %s s", len(data), result.duration_s)
    return TranscribeResult(text=result.text, detected_language=result.detected_language)
