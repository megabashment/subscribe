from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator, model_validator

from subscribe.export.srt import export_srt
from subscribe.export.vtt import export_vtt
from subscribe.export.json_export import export_json
from subscribe.models import Segment, Transcript, Word

logger = logging.getLogger(__name__)
router = APIRouter()

MIME = {"srt": "text/plain", "vtt": "text/vtt", "json": "application/json"}


class CueIn(BaseModel):
    id: int
    start: float
    end: float
    text: str
    words: list[dict] = []

    @field_validator("end")
    @classmethod
    def end_after_start(cls, v: float, info) -> float:
        start = info.data.get("start", 0.0)
        if v <= start:
            raise ValueError(f"end ({v}) must be greater than start ({start})")
        return v


class ExportRequest(BaseModel):
    cues: list[CueIn]
    format: Literal["srt", "vtt", "json"] = "srt"
    filename: str = "subtitles"

    @model_validator(mode="after")
    def no_overlaps(self) -> "ExportRequest":
        sorted_cues = sorted(self.cues, key=lambda c: c.start)
        for i in range(len(sorted_cues) - 1):
            curr = sorted_cues[i]
            nxt = sorted_cues[i + 1]
            if curr.end > nxt.start:
                raise ValueError(
                    f"Overlap: cue {curr.id} ends at {curr.end:.3f}s but cue {nxt.id} starts at {nxt.start:.3f}s"
                )
        return self


def _build_transcript(cues: list[CueIn]) -> Transcript:
    segments = [
        Segment(
            id=c.id,
            start=c.start,
            end=c.end,
            text=c.text,
            words=[Word(**w) for w in c.words] if c.words else [],
        )
        for c in sorted(cues, key=lambda c: c.start)
    ]
    duration = max((s.end for s in segments), default=0.0) if segments else 0.0
    return Transcript(language="und", duration=duration, segments=segments)


@router.post("/export")
async def export_cues(body: ExportRequest = Body(...)) -> FileResponse:
    transcript = _build_transcript(body.cues)
    stem = Path(body.filename).stem or "subtitles"

    tmp = tempfile.mkdtemp()
    out_path = Path(tmp) / f"{stem}.{body.format}"

    try:
        if body.format == "srt":
            export_srt(transcript, out_path)
        elif body.format == "vtt":
            export_vtt(transcript, out_path)
        elif body.format == "json":
            export_json(transcript, out_path)
    except Exception as exc:
        logger.exception("Export failed")
        raise HTTPException(500, str(exc)) from exc

    return FileResponse(
        path=str(out_path),
        filename=out_path.name,
        media_type=MIME[body.format],
    )
