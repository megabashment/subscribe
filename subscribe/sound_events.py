"""
Non-speech sound event detection — two optional layers.

Layer 1 (always active, zero deps):
    Whisper sometimes emits non-speech tokens like [laughter], [music].
    normalise_whisper_tokens() translates them to German bracket labels
    and discards blank/irrelevant tokens.

Layer 2 (optional, requires panns-inference + librosa):
    PANNs CNN14 audio tagger runs a sliding window over the extracted audio
    and inserts detected events ([Stöhnen], [Seufzen], …) into transcript gaps.
    Install: pip install panns-inference librosa
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Callable

from subscribe.models import Segment, Transcript

logger = logging.getLogger(__name__)

ProgressFn = Callable[[str, dict], None]

# ── Layer 1: Whisper token normalisation ────────────────────────────────────

_WHISPER_TOKEN_MAP: dict[str, str | None] = {
    'laughter':   '[Lachen]',
    'laughing':   '[Lachen]',
    'music':      '[Musik]',
    'singing':    '[Gesang]',
    'applause':   '[Applaus]',
    'clapping':   '[Applaus]',
    'sigh':       '[Seufzen]',
    'sighs':      '[Seufzen]',
    'sighing':    '[Seufzen]',
    'crying':     '[Weinen]',
    'sobbing':    '[Weinen]',
    'screaming':  '[Schreien]',
    'shouting':   '[Schreien]',
    'groaning':   '[Stöhnen]',
    'moaning':    '[Stöhnen]',
    'coughing':   '[Husten]',
    'cough':      '[Husten]',
    'sneezing':   '[Niesen]',
    'sneeze':     '[Niesen]',
    'breathing':  '[Atmen]',
    'blank_audio': None,
    '_bos_':      None,
    '_eos_':      None,
    '_eot_':      None,
}

_TOKEN_RE = re.compile(r'^\[([^\]]+)\]$')


def _classify_whisper_text(text: str) -> tuple[str | None, bool]:
    """Return (normalised_text, is_event). None means discard the segment."""
    m = _TOKEN_RE.match(text.strip())
    if not m:
        return text, False
    inner = m.group(1).lower().strip()
    if inner in _WHISPER_TOKEN_MAP:
        mapped = _WHISPER_TOKEN_MAP[inner]
        return mapped, mapped is not None
    return text, True  # unknown bracket token — keep as event


def normalise_whisper_tokens(transcript: Transcript) -> Transcript:
    """Translate Whisper non-speech tokens to German labels; discard blanks."""
    cleaned: list[Segment] = []
    new_id = 0
    for seg in transcript.segments:
        result, is_event = _classify_whisper_text(seg.text)
        if result is None:
            continue
        cleaned.append(Segment(
            id=new_id,
            start=seg.start,
            end=seg.end,
            text=result,
            words=[] if is_event else seg.words,
            is_event=is_event,
        ))
        new_id += 1
    return Transcript(language=transcript.language, duration=transcript.duration, segments=cleaned)


# ── Layer 2: PANNs audio event detection ────────────────────────────────────

# AudioSet class → (German bracket label, confidence threshold)
_PANNS_MAP: dict[str, tuple[str, float]] = {
    'Laughter':             ('[Lachen]',   0.50),
    'Crying, sobbing':      ('[Weinen]',   0.45),
    'Screaming':            ('[Schreien]', 0.50),
    'Groan':                ('[Stöhnen]',  0.45),
    'Sigh':                 ('[Seufzen]',  0.45),
    'Cough':                ('[Husten]',   0.55),
    'Sneeze':               ('[Niesen]',   0.60),
    'Applause':             ('[Applaus]',  0.55),
    'Music':                ('[Musik]',    0.65),
    'Whistling':            ('[Pfeifen]',  0.60),
    'Whimper':              ('[Wimmern]',  0.50),
    'Baby cry, infant cry': ('[Weinen]',   0.50),
}

_MIN_EVENT_DURATION = 0.4   # seconds — shorter events are noise
_MERGE_GAP          = 0.6   # seconds — gaps smaller than this merge same-label events


def detect_events_panns(
    audio_path: Path,
    device: str = 'cpu',
    on_progress: ProgressFn | None = None,
) -> list[tuple[float, float, str]]:
    """
    Run PANNs CNN14 audio tagger on audio_path.

    Returns list of (start_sec, end_sec, label) for detected sound events,
    sorted by start time. Events shorter than _MIN_EVENT_DURATION are dropped.

    Raises ImportError if panns-inference or librosa are not installed.
    """
    try:
        import numpy as np
        import librosa
        from panns_inference import AudioTagging
        import panns_inference.config as panns_config
    except ImportError as exc:
        raise ImportError(
            f"panns-inference not installed ({exc}).\n"
            "Run: pip install panns-inference librosa"
        ) from exc

    def emit(pct: int | None = None) -> None:
        if on_progress:
            data: dict = {'phase': 'sound_events', 'msg': ''}
            if pct is not None:
                data['pct'] = pct
            on_progress('status', data)

    emit()
    logger.info("PANNs: loading audio %s", audio_path)

    # PANNs CNN14 was trained at 32 kHz
    audio, sr = librosa.load(str(audio_path), sr=32000, mono=True)

    panns_device = 'cuda' if device == 'cuda' else 'cpu'
    at = AudioTagging(checkpoint_path=None, device=panns_device)

    classes: list[str] = panns_config.labels
    class_indices = {cls: classes.index(cls) for cls in _PANNS_MAP if cls in classes}
    if not class_indices:
        logger.warning("PANNs: no target classes found in label list — event detection will produce no results")

    window    = sr          # 1-second windows
    hop       = sr // 2     # 0.5-second hop
    n_hops    = max(1, (len(audio) - window) // hop)

    raw: list[tuple[float, float, str, float]] = []

    for step, i in enumerate(range(0, len(audio) - window, hop)):
        chunk = audio[i: i + window][None, :]
        _, clip_out = at.inference(chunk)
        probs = clip_out[0]

        t_start = i / sr
        t_end   = (i + window) / sr

        for cls, (label, thresh) in _PANNS_MAP.items():
            idx = class_indices.get(cls, -1)
            if idx >= 0 and probs[idx] > thresh:
                raw.append((t_start, t_end, label, float(probs[idx])))

        if step % 20 == 0:
            pct = round(step / n_hops * 100)
            emit(pct)

    # Merge consecutive windows of the same label (within _MERGE_GAP)
    merged: list[list] = []  # [start, end, label]
    for start, end, label, _ in sorted(raw, key=lambda x: x[0]):
        if merged and merged[-1][2] == label and start <= merged[-1][1] + _MERGE_GAP:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end, label])

    result = [
        (s, e, lbl)
        for s, e, lbl in merged
        if e - s >= _MIN_EVENT_DURATION
    ]

    logger.info("PANNs: detected %d events", len(result))
    return result


def merge_events_into_transcript(
    transcript: Transcript,
    events: list[tuple[float, float, str]],
) -> Transcript:
    """Insert PANNs events into gaps between speech segments; skip overlaps."""
    if not events:
        return transcript

    speech_ranges = [(s.start, s.end) for s in transcript.segments]

    def _overlaps(start: float, end: float) -> bool:
        return any(start < se and end > ss for ss, se in speech_ranges)

    extras: list[Segment] = [
        Segment(id=-1, start=s, end=e, text=lbl, is_event=True)
        for s, e, lbl in events
        if not _overlaps(s, e)
    ]

    if not extras:
        return transcript

    all_segs = sorted(transcript.segments + extras, key=lambda seg: seg.start)
    for i, seg in enumerate(all_segs):
        seg.id = i

    return Transcript(
        language=transcript.language,
        duration=transcript.duration,
        segments=all_segs,
    )
