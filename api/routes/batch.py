from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

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


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/batch")
async def batch_transcribe(
    files: list[UploadFile],
    lang: str = Form("auto"),
    model: str = Form("medium"),
    format: str = Form("srt"),
    device: str = Form("auto"),
    word_level: bool = Form(True),
) -> StreamingResponse:
    """
    Transcribe multiple files with SSE progress events.

    SSE event types:
      start   — {total: N}
      progress — {index: i, total: N, filename: str, status: "ok"|"error", message?: str}
      done    — {ok: N, failed: N}
    """
    if format not in SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format '{format}'.")
    if model not in SUPPORTED_MODELS:
        raise HTTPException(400, f"Unsupported model '{model}'.")

    effective_device = detect_device(None if device == "auto" else device)

    async def generate():
        total = len(files)
        yield _sse("start", {"total": total})

        ok = failed = 0
        tmp_root = tempfile.mkdtemp()

        for i, upload in enumerate(files):
            fname = upload.filename or f"file_{i}"
            stem = Path(fname).stem
            try:
                # Write upload to temp
                file_bytes = await upload.read()
                suffix = Path(fname).suffix or ".mp4"
                input_path = Path(tmp_root) / f"input_{i}{suffix}"
                input_path.write_bytes(file_bytes)

                # Run transcription in thread so we don't block the event loop
                audio_path = await asyncio.to_thread(
                    extract_audio, input_path, Path(tmp_root) / f"audio_{i}.wav"
                )
                transcript = await asyncio.to_thread(
                    transcribe, audio_path,
                    lang, model, effective_device, word_level,
                )

                out_path = Path(tmp_root) / f"{stem}.{format}"
                if format == "srt":
                    export_srt(transcript, out_path)
                elif format == "vtt":
                    export_vtt(transcript, out_path)
                elif format == "json":
                    export_json(transcript, out_path)

                yield _sse("progress", {
                    "index": i + 1, "total": total,
                    "filename": fname,
                    "status": "ok",
                    "out": str(out_path),
                    "language": transcript.language,
                    "segments": len(transcript.segments),
                })
                ok += 1

            except Exception as exc:
                logger.exception("Batch item failed: %s", fname)
                yield _sse("progress", {
                    "index": i + 1, "total": total,
                    "filename": fname,
                    "status": "error",
                    "message": str(exc),
                })
                failed += 1

        yield _sse("done", {"ok": ok, "failed": failed})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
