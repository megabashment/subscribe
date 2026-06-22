"""Phase 4: optional phoneme-accurate forced alignment via whisperX (local).

whisperX uses a wav2vec2 alignment model (one per language, downloaded locally)
to refine Whisper's token-based word timestamps into true forced-alignment word
boundaries — noticeably sharper cue edges for subtitles.

This module is fully optional: if `whisperx` is not installed it raises
AlignmentUnavailable, and callers fall back to Whisper's own word timestamps.
The function takes and returns the project's own Transcript/Segment/Word models,
so export and the editor UI stay unchanged (same data contract).
"""
from __future__ import annotations

import logging
from pathlib import Path

from subscribe.models import Segment, Transcript, Word

logger = logging.getLogger(__name__)


class AlignmentUnavailable(RuntimeError):
    """Raised when whisperX (or its deps) is not importable."""


def is_available() -> bool:
    try:
        import whisperx  # noqa: F401
        return True
    except Exception:
        return False


def align_transcript(
    transcript: Transcript,
    audio_path: Path,
    device: str = "cpu",
    language: str | None = None,
) -> Transcript:
    """Return a new Transcript with forced-aligned word/segment timestamps.

    Args:
        transcript: result of the Whisper pass (must contain segments; word-level
            timestamps from Whisper are not required, but text is).
        audio_path: the same 16kHz wav used for transcription.
        device: "cuda" | "cpu" (the wav2vec2 model runs in addition to Whisper;
            on tight VRAM, use "cpu" here).
        language: language code; defaults to transcript.language.

    Raises:
        AlignmentUnavailable: if whisperx cannot be imported.
    """
    try:
        import whisperx
    except Exception as exc:  # pragma: no cover - exercised via fallback path
        raise AlignmentUnavailable(
            "whisperx is not installed. Install with: pip install -r requirements-align.txt"
        ) from exc

    lang = language or transcript.language
    if not transcript.segments:
        return transcript

    # whisperX expects plain dicts with start/end/text
    seg_dicts = [
        {"start": s.start, "end": s.end, "text": s.text}
        for s in transcript.segments
    ]

    logger.info("Loading alignment model for language=%s on %s", lang, device)
    align_model, metadata = whisperx.load_align_model(language_code=lang, device=device)

    audio = whisperx.load_audio(str(audio_path))
    result = whisperx.align(
        seg_dicts,
        align_model,
        metadata,
        audio,
        device,
        return_char_alignments=False,
    )

    aligned = _from_whisperx(result, fallback=transcript)
    logger.info("Alignment done: %d segments", len(aligned.segments))
    return aligned


def _from_whisperx(result: dict, fallback: Transcript) -> Transcript:
    """Convert a whisperX align() result back into our Transcript model.

    Falls back to the original segment timing/text where whisperX omits a field
    (e.g. words it could not align keep no/None timestamps — we skip those).
    """
    raw_segments = result.get("segments", [])
    segments: list[Segment] = []

    for i, seg in enumerate(raw_segments):
        words: list[Word] = []
        for w in seg.get("words", []):
            # whisperX may leave start/end unset for unalignable tokens
            if w.get("start") is None or w.get("end") is None:
                continue
            words.append(
                Word(
                    text=w.get("word", "").strip() or w.get("word", ""),
                    start=float(w["start"]),
                    end=float(w["end"]),
                    confidence=float(w.get("score", 1.0)),
                )
            )

        # Prefer aligned segment bounds; fall back to first/last word or original
        start = seg.get("start")
        end = seg.get("end")
        if (start is None or end is None) and words:
            start = words[0].start
            end = words[-1].end
        if start is None or end is None:
            # last resort: keep original timing for this index if present
            orig = fallback.segments[i] if i < len(fallback.segments) else None
            start = orig.start if orig else 0.0
            end = orig.end if orig else 0.0

        segments.append(
            Segment(
                id=i,
                start=float(start),
                end=float(end),
                text=seg.get("text", "").strip(),
                words=words,
            )
        )

    if not segments:
        return fallback

    return Transcript(
        language=fallback.language,
        duration=fallback.duration,
        segments=segments,
    )
