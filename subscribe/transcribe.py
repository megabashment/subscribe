from __future__ import annotations

import logging
from pathlib import Path

from subscribe.models import Segment, Transcript, Word
from subscribe.utils.device import detect_device

logger = logging.getLogger(__name__)


def transcribe(
    audio_path: Path,
    language: str = "auto",
    model_size: str = "medium",
    device: str = "auto",
) -> Transcript:
    """Transcribe audio using faster-whisper. Returns a Transcript with Segments."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        )

    effective_device = detect_device(None if device == "auto" else device)
    compute_type = "float16" if effective_device == "cuda" else "int8"

    logger.info("Loading model '%s' on %s (%s)", model_size, effective_device, compute_type)
    model = WhisperModel(model_size, device=effective_device, compute_type=compute_type)

    lang_arg = None if language == "auto" else language
    logger.info("Transcribing %s (lang=%s)", audio_path.name, lang_arg or "auto-detect")

    raw_segments, info = model.transcribe(
        str(audio_path),
        language=lang_arg,
        word_timestamps=False,
    )

    segments: list[Segment] = []
    for i, seg in enumerate(raw_segments):
        segments.append(
            Segment(
                id=i,
                start=seg.start,
                end=seg.end,
                text=seg.text.strip(),
            )
        )
        logger.debug("[%.2f → %.2f] %s", seg.start, seg.end, seg.text.strip())

    logger.info("Transcription done: %d segments, language=%s", len(segments), info.language)

    return Transcript(
        language=info.language,
        duration=info.duration,
        segments=segments,
    )
