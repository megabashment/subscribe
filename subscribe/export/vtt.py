from __future__ import annotations

from pathlib import Path

from subscribe.models import Transcript


def _fmt_time(seconds: float) -> str:
    """Format seconds as WebVTT timestamp: HH:MM:SS.mmm (dot, not comma)"""
    ms = round(seconds * 1000)
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def export_vtt(transcript: Transcript, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["WEBVTT", ""]

    seq = 1
    for seg in transcript.segments:
        if not seg.text:
            continue
        lines.append(str(seq))
        lines.append(f"{_fmt_time(seg.start)} --> {_fmt_time(seg.end)}")
        lines.append(seg.text)
        lines.append("")
        seq += 1

    # VTT spec: UTF-8 without BOM
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
