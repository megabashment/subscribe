from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from subscribe.audio_extract import extract_audio
from subscribe.export.srt import export_srt
from subscribe.transcribe import transcribe
from subscribe.utils.device import detect_device

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_FORMATS = {"srt", "vtt", "json"}
SUPPORTED_MODELS = {"tiny", "base", "small", "medium", "large-v3"}


@router.post("/transcribe")
async def transcribe_file(
    file: UploadFile,
    lang: str = Form("auto"),
    model: str = Form("medium"),
    format: str = Form("srt"),
    device: str = Form("auto"),
) -> FileResponse:
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format '{format}'. Choose: {SUPPORTED_FORMATS}")
    if model not in SUPPORTED_MODELS:
        raise HTTPException(400, f"Unsupported model '{model}'. Choose: {SUPPORTED_MODELS}")

    effective_device = detect_device(None if device == "auto" else device)

    # We need the tempdir to outlive this function so FileResponse can stream it.
    # FastAPI's BackgroundTask will clean up after the response is sent.
    tmp = tempfile.mkdtemp()
    tmp_path = Path(tmp)

    try:
        suffix = Path(file.filename or "upload").suffix or ".mp4"
        input_path = tmp_path / f"input{suffix}"
        input_path.write_bytes(await file.read())

        audio_path = extract_audio(input_path, tmp_path / "audio.wav")

        transcript = transcribe(
            audio_path,
            language=lang,
            model_size=model,
            device=effective_device,
        )

        stem = Path(file.filename or "output").stem
        out_path = tmp_path / f"{stem}.{format}"

        if format == "srt":
            export_srt(transcript, out_path)
        else:
            # vtt / json: Sprint 2 — fall back to srt for now
            out_path = tmp_path / f"{stem}.srt"
            export_srt(transcript, out_path)
            logger.warning("Format '%s' not yet implemented, returning SRT", format)

        return FileResponse(
            path=str(out_path),
            filename=out_path.name,
            media_type="text/plain",
            headers={"X-Language": transcript.language, "X-Segments": str(len(transcript.segments))},
        )

    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(500, str(exc)) from exc
