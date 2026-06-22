"""Tests for POST /export endpoint (Sprint 2.5)."""
import json
import pytest
from fastapi.testclient import TestClient

from api.server import app

client = TestClient(app)

VALID_CUES = [
    {"id": 0, "start": 0.0, "end": 3.5, "text": "Hallo Welt.", "words": []},
    {"id": 1, "start": 4.1, "end": 7.8, "text": "Das ist ein Test.", "words": []},
]


def test_export_srt():
    res = client.post("/export", json={"cues": VALID_CUES, "format": "srt", "filename": "test"})
    assert res.status_code == 200
    assert "Content-Type" in res.headers
    content = res.content.decode("utf-8-sig")
    assert "Hallo Welt." in content
    assert "Das ist ein Test." in content
    assert "1\r\n" in content or "1\n" in content


def test_export_vtt():
    res = client.post("/export", json={"cues": VALID_CUES, "format": "vtt", "filename": "test"})
    assert res.status_code == 200
    content = res.content.decode("utf-8")
    assert content.startswith("WEBVTT")
    assert "Hallo Welt." in content


def test_export_json():
    res = client.post("/export", json={"cues": VALID_CUES, "format": "json", "filename": "test"})
    assert res.status_code == 200
    data = json.loads(res.content.decode("utf-8"))
    assert len(data["segments"]) == 2


def test_export_rejects_overlap():
    overlapping = [
        {"id": 0, "start": 0.0, "end": 5.0, "text": "A", "words": []},
        {"id": 1, "start": 4.0, "end": 8.0, "text": "B", "words": []},
    ]
    res = client.post("/export", json={"cues": overlapping, "format": "srt"})
    assert res.status_code == 422


def test_export_rejects_end_before_start():
    bad = [{"id": 0, "start": 5.0, "end": 2.0, "text": "X", "words": []}]
    res = client.post("/export", json={"cues": bad, "format": "srt"})
    assert res.status_code == 422


def test_export_umlauts_srt():
    cues = [{"id": 0, "start": 0.0, "end": 2.0, "text": "Ä ö ü ß", "words": []}]
    res = client.post("/export", json={"cues": cues, "format": "srt"})
    assert res.status_code == 200
    content = res.content.decode("utf-8-sig")
    assert "Ä" in content


def test_export_srt_bom():
    res = client.post("/export", json={"cues": VALID_CUES, "format": "srt"})
    assert res.status_code == 200
    assert res.content[:3] == b"\xef\xbb\xbf"


def test_export_vtt_no_bom():
    res = client.post("/export", json={"cues": VALID_CUES, "format": "vtt"})
    assert res.status_code == 200
    assert res.content[:3] != b"\xef\xbb\xbf"


def test_export_single_cue():
    cues = [{"id": 0, "start": 1.0, "end": 3.0, "text": "Nur ein Cue.", "words": []}]
    res = client.post("/export", json={"cues": cues, "format": "srt"})
    assert res.status_code == 200
    assert "Nur ein Cue." in res.content.decode("utf-8-sig")


def test_export_empty_text_cue():
    cues = [{"id": 0, "start": 0.0, "end": 2.0, "text": "", "words": []}]
    res = client.post("/export", json={"cues": cues, "format": "srt"})
    # Empty text cue gets skipped by export_srt — still 200
    assert res.status_code == 200
