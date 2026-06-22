"""Phase 2: verify the ffmpeg audio-preprocessing filter chain is assembled
correctly. We test the pure command/filter builders without running ffmpeg.
"""
from __future__ import annotations

from pathlib import Path

from subscribe.audio_extract import _build_filter_chain, _build_cmd


def test_no_filters_when_all_disabled():
    assert _build_filter_chain(normalize=False, denoise=False) is None


def test_normalize_adds_speechband_and_loudnorm():
    af = _build_filter_chain(normalize=True, denoise=False)
    assert af is not None
    assert "highpass=f=80" in af
    assert "lowpass=f=8000" in af
    assert "loudnorm" in af
    assert "afftdn" not in af


def test_denoise_adds_afftdn():
    af = _build_filter_chain(normalize=False, denoise=True)
    assert "afftdn" in af
    assert "loudnorm" not in af


def test_both_filters_combined():
    af = _build_filter_chain(normalize=True, denoise=True)
    assert "afftdn" in af and "loudnorm" in af
    # denoise should run before loudnorm
    assert af.index("afftdn") < af.index("loudnorm")


def test_cmd_without_filters_has_no_af_flag():
    cmd = _build_cmd(Path("in.mp4"), Path("out.wav"), None)
    assert "-af" not in cmd
    assert cmd[:3] == ["ffmpeg", "-y", "-i"]
    # core output options present, mono 16kHz wav
    assert "-ac" in cmd and "1" in cmd
    assert "16000" in cmd and "wav" in cmd


def test_cmd_with_filters_includes_af_flag():
    cmd = _build_cmd(Path("in.mp4"), Path("out.wav"), "loudnorm")
    assert "-af" in cmd
    assert cmd[cmd.index("-af") + 1] == "loudnorm"
    # core output options still present
    assert "16000" in cmd and "wav" in cmd
