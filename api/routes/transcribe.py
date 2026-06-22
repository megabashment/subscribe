from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import asyncio
import json
import queue
import threading

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

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
    word_level: bool = Form(True),
    vad: bool = Form(True),
    beam_size: int = Form(5),
    prompt: str | None = Form(None),
    normalize: bool = Form(True),
    denoise: bool = Form(False),
    align: bool = Form(False),
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

        audio_path = extract_audio(input_path, tmp_path / "audio.wav", normalize=normalize, denoise=denoise)
        transcript = transcribe(
            audio_path,
            language=lang,
            model_size=model,
            device=effective_device,
            word_timestamps=word_level,
            vad=vad,
            beam_size=beam_size,
            initial_prompt=prompt or None,
            align=align,
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


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/transcribe/cues")
async def transcribe_to_cues(
    file: UploadFile,
    lang: str = Form("auto"),
    model: str = Form("medium"),
    device: str = Form("auto"),
    word_level: bool = Form(True),
    vad: bool = Form(True),
    beam_size: int = Form(5),
    prompt: str | None = Form(None),
    normalize: bool = Form(True),
    denoise: bool = Form(False),
    align: bool = Form(False),
    sound_events: bool = Form(False),
) -> StreamingResponse:
    """Transcribe and stream progress via SSE. Final event 'done' contains all cues."""
    if model not in SUPPORTED_MODELS:
        raise HTTPException(400, f"Unsupported model '{model}'. Choose: {sorted(SUPPORTED_MODELS)}")

    effective_device = detect_device(None if device == "auto" else device)

    tmp_path = Path(tempfile.mkdtemp())
    suffix = Path(file.filename or "upload").suffix or ".mp4"
    input_path = tmp_path / f"input{suffix}"
    input_path.write_bytes(await file.read())
    filename_stem = Path(file.filename or "output").stem

    # Queue bridges the transcribe thread → async generator
    q: queue.Queue = queue.Queue()
    _DONE = object()

    def on_progress(event: str, data: dict) -> None:
        q.put((event, data))

    def run() -> None:
        try:
            audio_path = extract_audio(input_path, tmp_path / "audio.wav", normalize=normalize, denoise=denoise)
            transcript = transcribe(
                audio_path,
                language=lang,
                model_size=model,
                device=effective_device,
                word_timestamps=word_level,
                vad=vad,
                beam_size=beam_size,
                initial_prompt=prompt or None,
                align=align,
                sound_events=sound_events,
                on_progress=on_progress,
            )
            q.put(("done", {
                "language": transcript.language,
                "duration": transcript.duration,
                "filename": filename_stem,
                "segments": [
                    {
                        "id": seg.id,
                        "start": seg.start,
                        "end": seg.end,
                        "text": seg.text,
                        "is_event": seg.is_event,
                        "words": [w.model_dump() for w in seg.words],
                    }
                    for seg in transcript.segments
                ],
            }))
        except Exception as exc:
            logger.exception("Transcription failed")
            q.put(("error", {"message": str(exc)}))
        finally:
            q.put(_DONE)

    threading.Thread(target=run, daemon=True).start()

    async def generate():
        loop = asyncio.get_event_loop()
        while True:
            item = await loop.run_in_executor(None, q.get)
            if item is _DONE:
                break
            event, data = item
            yield _sse(event, data)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
