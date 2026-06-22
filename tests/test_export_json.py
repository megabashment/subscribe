import json
from pathlib import Path
import tempfile

from subscribe.models import Segment, Transcript, Word
from subscribe.export.json_export import export_json


FIXTURE = Transcript(
    language="de",
    duration=10.0,
    segments=[
        Segment(id=0, start=0.0, end=3.5, text="Hallo Welt."),
        Segment(id=1, start=4.1, end=7.8, text="Das ist ein Test."),
    ],
)

WORD_FIXTURE = Transcript(
    language="en",
    duration=5.0,
    segments=[
        Segment(
            id=0, start=0.0, end=2.0, text="Hello world.",
            words=[
                Word(text="Hello", start=0.0, end=0.6, confidence=0.99),
                Word(text="world.", start=0.7, end=1.2, confidence=0.95),
            ],
        ),
    ],
)


def test_json_valid():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.json"
        export_json(FIXTURE, out)
        data = json.loads(out.read_text(encoding="utf-8"))

    assert data["language"] == "de"
    assert data["duration"] == 10.0
    assert len(data["segments"]) == 2


def test_json_segment_fields():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.json"
        export_json(FIXTURE, out)
        data = json.loads(out.read_text(encoding="utf-8"))

    seg = data["segments"][0]
    assert seg["start"] == 0.0
    assert seg["end"] == 3.5
    assert seg["text"] == "Hallo Welt."
    assert seg["words"] == []


def test_json_words_included():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.json"
        export_json(WORD_FIXTURE, out)
        data = json.loads(out.read_text(encoding="utf-8"))

    words = data["segments"][0]["words"]
    assert len(words) == 2
    assert words[0]["text"] == "Hello"
    assert words[0]["confidence"] == 0.99


def test_json_umlauts():
    transcript = Transcript(
        language="de",
        segments=[Segment(id=0, start=0.0, end=1.0, text="Ä, ö, ü, ß 🎙️")],
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.json"
        export_json(transcript, out)
        raw = out.read_text(encoding="utf-8")

    assert "Ä" in raw
    assert "🎙️" in raw
    assert "\\u" not in raw  # ensure_ascii=False: no escaped unicode


def test_json_no_bom():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.json"
        export_json(FIXTURE, out)
        assert out.read_bytes()[:3] != b"\xef\xbb\xbf"
