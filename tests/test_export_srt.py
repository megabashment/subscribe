from pathlib import Path
import tempfile

import pytest

from subscribe.models import Segment, Transcript
from subscribe.export.srt import export_srt, _fmt_time as srt_fmt_time
from subscribe.export.vtt import export_vtt, _fmt_time as vtt_fmt_time


# ── Shared fixture ────────────────────────────────────────────────────────────

FIXTURE = Transcript(
    language="de",
    duration=10.0,
    segments=[
        Segment(id=0, start=0.0, end=3.5, text="Hallo Welt."),
        Segment(id=1, start=4.1, end=7.8, text="Das ist ein Test."),
    ],
)

UMLAUT_FIXTURE = Transcript(
    language="de",
    duration=5.0,
    segments=[
        Segment(id=0, start=0.0, end=2.0, text="Ä, ö, ü, ß — Anführungszeichen 🎙️"),
    ],
)

EMPTY_SEG_FIXTURE = Transcript(
    language="de",
    segments=[
        Segment(id=0, start=0.0, end=1.0, text=""),
        Segment(id=1, start=1.0, end=2.0, text="Satz zwei."),
    ],
)


# ── SRT: timestamp format ─────────────────────────────────────────────────────

def test_srt_fmt_time_zero():
    assert srt_fmt_time(0.0) == "00:00:00,000"

def test_srt_fmt_time_millis():
    assert srt_fmt_time(3.5) == "00:00:03,500"

def test_srt_fmt_time_hours():
    assert srt_fmt_time(3661.123) == "01:01:01,123"

def test_srt_fmt_time_uses_comma():
    ts = srt_fmt_time(1.0)
    assert "," in ts
    assert "." not in ts.split(":")[2]  # seconds part uses comma, not dot


# ── SRT: content ──────────────────────────────────────────────────────────────

def test_srt_content():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(FIXTURE, out)
        content = out.read_text(encoding="utf-8-sig")

    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:03,500" in content
    assert "Hallo Welt." in content
    assert "2\n" in content
    assert "00:00:04,100 --> 00:00:07,800" in content
    assert "Das ist ein Test." in content

def test_srt_bom():
    """SRT must be UTF-8 with BOM for VLC/Windows compatibility."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(FIXTURE, out)
        raw = out.read_bytes()
    assert raw[:3] == b"\xef\xbb\xbf", "SRT file must start with UTF-8 BOM"

def test_srt_skips_empty_segments():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(EMPTY_SEG_FIXTURE, out)
        content = out.read_text(encoding="utf-8-sig")
    assert "Satz zwei." in content
    assert "00:00:00,000 --> 00:00:01,000" not in content

def test_srt_umlauts_and_emoji():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(UMLAUT_FIXTURE, out)
        content = out.read_text(encoding="utf-8-sig")
    assert "Ä, ö, ü, ß" in content
    assert "🎙️" in content
    assert "Anführungszeichen" in content

def test_srt_sequence_numbers_start_at_1():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(FIXTURE, out)
        lines = out.read_text(encoding="utf-8-sig").splitlines()
    # first non-empty line must be "1"
    assert lines[0] == "1"

def test_srt_start_before_end():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(FIXTURE, out)
        content = out.read_text(encoding="utf-8-sig")
    # Both cues: start < end
    assert "00:00:00,000 --> 00:00:03,500" in content
    assert "00:00:04,100 --> 00:00:07,800" in content


# ── VTT: timestamp format ─────────────────────────────────────────────────────

def test_vtt_fmt_time_zero():
    assert vtt_fmt_time(0.0) == "00:00:00.000"

def test_vtt_fmt_time_millis():
    assert vtt_fmt_time(3.5) == "00:00:03.500"

def test_vtt_fmt_time_uses_dot():
    ts = vtt_fmt_time(1.0)
    assert "." in ts
    assert "," not in ts


# ── VTT: content ──────────────────────────────────────────────────────────────

def test_vtt_header():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(FIXTURE, out)
        content = out.read_text(encoding="utf-8")
    assert content.startswith("WEBVTT")

def test_vtt_no_bom():
    """VTT must NOT have BOM (spec requirement)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(FIXTURE, out)
        raw = out.read_bytes()
    assert raw[:3] != b"\xef\xbb\xbf", "VTT must not have UTF-8 BOM"

def test_vtt_content():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(FIXTURE, out)
        content = out.read_text(encoding="utf-8")
    assert "00:00:00.000 --> 00:00:03.500" in content
    assert "Hallo Welt." in content
    assert "00:00:04.100 --> 00:00:07.800" in content

def test_vtt_skips_empty_segments():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(EMPTY_SEG_FIXTURE, out)
        content = out.read_text(encoding="utf-8")
    assert "Satz zwei." in content
    assert "00:00:00.000 --> 00:00:01.000" not in content

def test_vtt_umlauts_and_emoji():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(UMLAUT_FIXTURE, out)
        content = out.read_text(encoding="utf-8")
    assert "Ä, ö, ü, ß" in content
    assert "🎙️" in content

def test_vtt_sequence_numbers_start_at_1():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.vtt"
        export_vtt(FIXTURE, out)
        lines = out.read_text(encoding="utf-8").splitlines()
    # line 0: WEBVTT, line 1: empty, line 2: "1"
    assert lines[2] == "1"
