from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from subscribe.audio_extract import extract_audio
from subscribe.export.srt import export_srt
from subscribe.export.vtt import export_vtt
from subscribe.export.json_export import export_json
from subscribe.transcribe import transcribe
from subscribe.utils.device import detect_device

logger = logging.getLogger(__name__)
router = APIRouter()

SUPPORTED_FORMATS = {"srt", "vtt", "json"}
SUPPORTED_MODELS = {"tiny", "base", "small", "medium", "large-v3"}

MIME = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}


@router.post("/transcribe")
async def transcribe_file(
    file: UploadFile,
    lang: str = Form("auto"),
    model: str = Form("medium"),
    format: str = Form("srt"),
    device: str = Form("auto"),
) -> FileResponse:
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format '{format}'. Choose: {sorted(SUPPORTED_FORMATS)}")
    if model not in SUPPORTED_MODELS:
        raise HTTPException(400, f"Unsupported model '{model}'. Choose: {sorted(SUPPORTED_MODELS)}")

    effective_device = detect_device(None if device == "auto" else device)

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
        elif format == "vtt":
            export_vtt(transcript, out_path)
        elif format == "json":
            export_json(transcript, out_path)

        return FileResponse(
            path=str(out_path),
            filename=out_path.name,
            media_type=MIME[format],
            headers={
                "X-Language": transcript.language,
                "X-Segments": str(len(transcript.segments)),
            },
        )

    except Exception as exc:
        logger.exception("Transcription failed")
        raise HTTPException(500, str(exc)) from exc
