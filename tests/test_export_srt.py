from pathlib import Path
import tempfile

from subscribe.models import Segment, Transcript
from subscribe.export.srt import export_srt, _fmt_time


FIXTURE = Transcript(
    language="de",
    duration=10.0,
    segments=[
        Segment(id=0, start=0.0, end=3.5, text="Hallo Welt."),
        Segment(id=1, start=4.1, end=7.8, text="Das ist ein Test."),
    ],
)


def test_fmt_time():
    assert _fmt_time(0.0) == "00:00:00,000"
    assert _fmt_time(3.5) == "00:00:03,500"
    assert _fmt_time(3661.123) == "01:01:01,123"


def test_export_srt_content():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(FIXTURE, out)
        content = out.read_text(encoding="utf-8")

    assert "1\n" in content
    assert "00:00:00,000 --> 00:00:03,500" in content
    assert "Hallo Welt." in content
    assert "2\n" in content
    assert "00:00:04,100 --> 00:00:07,800" in content
    assert "Das ist ein Test." in content


def test_export_srt_skips_empty_segments():
    transcript = Transcript(
        language="de",
        segments=[
            Segment(id=0, start=0.0, end=1.0, text=""),
            Segment(id=1, start=1.0, end=2.0, text="Satz zwei."),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.srt"
        export_srt(transcript, out)
        content = out.read_text(encoding="utf-8")

    assert "Satz zwei." in content
    # empty segment must not produce a block
    assert "00:00:00,000 --> 00:00:01,000" not in content
