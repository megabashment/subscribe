"""Phase 4: forced alignment — result conversion and graceful fallback.

We don't run real whisperX (heavy, downloads models). We test:
- _from_whisperx() maps a whisperX-style result back into our Transcript model
- align_transcript() raises AlignmentUnavailable when whisperx is absent
- transcribe()'s _maybe_align falls back to the original transcript on failure
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from subscribe.align import _from_whisperx, align_transcript, AlignmentUnavailable
from subscribe.models import Segment, Transcript, Word


FALLBACK = Transcript(
    language="de",
    duration=10.0,
    segments=[
        Segment(id=0, start=0.0, end=3.5, text="Hallo Welt.",
                words=[Word(text="Hallo", start=0.0, end=1.0, confidence=0.9)]),
    ],
)


def test_from_whisperx_maps_words_and_scores():
    result = {
        "segments": [
            {
                "start": 0.1, "end": 3.4, "text": "Hallo Welt.",
                "words": [
                    {"word": "Hallo", "start": 0.10, "end": 0.55, "score": 0.97},
                    {"word": "Welt.", "start": 0.60, "end": 1.10, "score": 0.93},
                ],
            }
        ]
    }
    out = _from_whisperx(result, fallback=FALLBACK)
    assert out.language == "de"
    assert out.duration == 10.0
    assert len(out.segments) == 1
    seg = out.segments[0]
    assert seg.start == 0.1 and seg.end == 3.4
    assert [w.text for w in seg.words] == ["Hallo", "Welt."]
    assert seg.words[0].confidence == 0.97


def test_from_whisperx_skips_unaligned_words():
    result = {
        "segments": [
            {
                "start": 0.0, "end": 2.0, "text": "Hallo Welt.",
                "words": [
                    {"word": "Hallo", "start": 0.0, "end": 0.5, "score": 0.9},
                    {"word": "Welt.", "start": None, "end": None},  # unalignable
                ],
            }
        ]
    }
    out = _from_whisperx(result, fallback=FALLBACK)
    assert [w.text for w in out.segments[0].words] == ["Hallo"]


def test_from_whisperx_derives_segment_bounds_from_words():
    result = {
        "segments": [
            {
                "text": "Hallo",  # no segment start/end
                "words": [{"word": "Hallo", "start": 1.2, "end": 1.9, "score": 0.8}],
            }
        ]
    }
    out = _from_whisperx(result, fallback=FALLBACK)
    assert out.segments[0].start == 1.2
    assert out.segments[0].end == 1.9


def test_from_whisperx_empty_returns_fallback():
    out = _from_whisperx({"segments": []}, fallback=FALLBACK)
    assert out is FALLBACK


def test_align_transcript_raises_when_whisperx_absent(monkeypatch):
    # Ensure import of whisperx fails
    monkeypatch.setitem(sys.modules, "whisperx", None)
    with pytest.raises(AlignmentUnavailable):
        align_transcript(FALLBACK, Path("dummy.wav"), device="cpu")


def test_transcribe_align_fallback(monkeypatch):
    """transcribe(align=True) must not crash when whisperx is unavailable —
    it should return the Whisper transcript unchanged."""
    import types
    from unittest.mock import MagicMock
    from subscribe import transcribe as transcribe_mod

    class _Info:
        language = "de"
        duration = 1.0

    fake_model = MagicMock()
    fake_model.transcribe.return_value = ([], _Info())
    fake_fw = types.ModuleType("faster_whisper")
    fake_fw.WhisperModel = lambda *a, **k: fake_model
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_fw)
    monkeypatch.setattr("subscribe.transcribe.detect_device", lambda *a, **k: "cpu")
    # whisperx import fails → AlignmentUnavailable → fallback
    monkeypatch.setitem(sys.modules, "whisperx", None)

    result = transcribe_mod.transcribe(Path("dummy.wav"), align=True)
    assert result.language == "de"  # returned cleanly, no crash
