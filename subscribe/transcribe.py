from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path

from subscribe.audio_extract import probe_duration
from subscribe.models import Segment, Transcript, Word
from subscribe.utils.device import detect_device

logger = logging.getLogger(__name__)

# Type for progress callbacks: emit(event, data)
ProgressFn = Callable[[str, dict], None]


def _patch_hf_download(emit: ProgressFn) -> None:
    """Monkey-patch huggingface_hub tqdm so we get download progress events."""
    try:
        import huggingface_hub.file_download as fd

        _orig = fd.tqdm

        class _ProgressTqdm:
            def __init__(self, *args, **kwargs):
                self._total = kwargs.get("total") or (args[1] if len(args) > 1 else None)
                self._desc = kwargs.get("desc", "")
                self._n = 0
                self._last_emit = 0.0

            def __enter__(self): return self
            def __exit__(self, *a): pass

            def update(self, n=1):
                self._n += n
                now = time.monotonic()
                if now - self._last_emit >= 0.5:
                    self._last_emit = now
                    emit("download", {
                        "desc": self._desc,
                        "downloaded_mb": round(self._n / 1_048_576, 1),
                        "total_mb": round(self._total / 1_048_576, 1) if self._total else None,
                    })

            def close(self): pass
            def set_postfix(self, *a, **kw): pass

        fd.tqdm = _ProgressTqdm
        return fd, _orig
    except Exception:
        return None, None


def transcribe(
    audio_path: Path,
    language: str = "auto",
    model_size: str = "medium",
    device: str = "auto",
    word_timestamps: bool = True,
    vad: bool = True,
    vad_threshold: float = 0.5,
    vad_min_silence_ms: int = 500,
    vad_speech_pad_ms: int = 300,
    beam_size: int = 5,
    initial_prompt: str | None = None,
    condition_on_previous_text: bool = True,
    no_speech_threshold: float = 0.6,
    compression_ratio_threshold: float = 2.4,
    log_prob_threshold: float = -1.0,
    hallucination_silence_threshold: float | None = 2.0,
    align: bool = False,
    align_device: str | None = None,
    on_progress: ProgressFn | None = None,
) -> Transcript:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError("faster-whisper is not installed. Run: pip install faster-whisper")

    def emit(event: str, data: dict) -> None:
        if on_progress:
            on_progress(event, data)

    effective_device = detect_device(None if device == "auto" else device)
    compute_type = "float16" if effective_device == "cuda" else "int8"

    # Patch HF download progress before model load
    fd_mod, orig_tqdm = _patch_hf_download(emit)

    emit("status", {"phase": "model", "msg": f"Lade Modell {model_size}…"})
    logger.info("Loading model '%s' on %s (%s)", model_size, effective_device, compute_type)
    model = WhisperModel(model_size, device=effective_device, compute_type=compute_type)

    # Restore original tqdm
    if fd_mod and orig_tqdm:
        fd_mod.tqdm = orig_tqdm

    lang_arg = None if language == "auto" else language

    # Probe duration so the frontend can show a real progress bar
    duration_hint = probe_duration(audio_path)
    emit("status", {"phase": "audio", "msg": "Extrahiere Audio…", "duration": duration_hint})
    logger.info("Transcribing %s (lang=%s, duration=%.1fs)", audio_path.name, lang_arg or "auto-detect", duration_hint or 0)

    emit("status", {"phase": "transcribe", "msg": "Transkribiere…", "duration": duration_hint})
    vad_params = {
        "threshold": vad_threshold,
        "min_silence_duration_ms": vad_min_silence_ms,
        "speech_pad_ms": vad_speech_pad_ms,
    } if vad else None

    # hallucination_silence_threshold only takes effect with word timestamps
    halluc = hallucination_silence_threshold if word_timestamps else None

    raw_segments, info = model.transcribe(
        str(audio_path),
        language=lang_arg,
        word_timestamps=word_timestamps,
        vad_filter=vad,
        vad_parameters=vad_params,
        beam_size=beam_size,
        initial_prompt=initial_prompt,
        condition_on_previous_text=condition_on_previous_text,
        no_speech_threshold=no_speech_threshold,
        compression_ratio_threshold=compression_ratio_threshold,
        log_prob_threshold=log_prob_threshold,
        hallucination_silence_threshold=halluc,
    )

    segments: list[Segment] = []
    for i, seg in enumerate(raw_segments):
        words: list[Word] = []
        if word_timestamps and seg.words:
            for w in seg.words:
                words.append(Word(text=w.word, start=w.start, end=w.end, confidence=w.probability))
        segments.append(Segment(id=i, start=seg.start, end=seg.end, text=seg.text.strip(), words=words))
        emit("segment", {"index": i, "start": seg.start, "end": seg.end, "text": seg.text.strip()})
        logger.debug("[%.2f → %.2f] %s", seg.start, seg.end, seg.text.strip())

    logger.info("Done: %d segments, language=%s", len(segments), info.language)
    transcript = Transcript(language=info.language, duration=info.duration, segments=segments)

    if align:
        transcript = _maybe_align(
            transcript, audio_path,
            align_device=align_device or effective_device,
            emit=emit,
        )

    return transcript


def _maybe_align(
    transcript: Transcript,
    audio_path: Path,
    align_device: str,
    emit: ProgressFn,
) -> Transcript:
    """Run whisperX forced alignment; fall back to Whisper word timestamps on
    any failure (missing dependency, unsupported language, OOM)."""
    from subscribe.align import align_transcript, AlignmentUnavailable

    emit("status", {"phase": "align", "msg": "Präzises Alignment (whisperX)…"})
    try:
        return align_transcript(
            transcript, audio_path,
            device=align_device, language=transcript.language,
        )
    except AlignmentUnavailable as exc:
        logger.warning("Alignment skipped (whisperx not installed): %s", exc)
    except Exception as exc:
        logger.warning("Alignment failed, using Whisper word timestamps: %s", exc)
    return transcript
