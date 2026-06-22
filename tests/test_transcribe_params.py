"""Phase 1: verify decoding parameters are forwarded to faster-whisper.

We mock faster_whisper.WhisperModel so no real model is loaded; we only
assert that transcribe() passes the right kwargs to model.transcribe().
"""
from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from subscribe.transcribe import transcribe


class _FakeInfo:
    language = "de"
    duration = 1.0


def _install_fake_faster_whisper(monkeypatch, capture: dict):
    """Inject a fake faster_whisper module whose WhisperModel records calls."""
    fake_model = MagicMock()
    # transcribe() returns (segments_iterable, info)
    fake_model.transcribe.return_value = ([], _FakeInfo())

    def _model_ctor(model_size, device, compute_type):
        capture["ctor"] = {"model_size": model_size, "device": device, "compute_type": compute_type}
        return fake_model

    fake_module = types.ModuleType("faster_whisper")
    fake_module.WhisperModel = _model_ctor
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)

    # Force device detection to cpu for determinism
    monkeypatch.setattr("subscribe.transcribe.detect_device", lambda *_a, **_k: "cpu")
    return fake_model


def test_defaults_forwarded(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(Path("dummy.wav"))

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["beam_size"] == 5
    assert kwargs["initial_prompt"] is None
    assert kwargs["condition_on_previous_text"] is True
    assert kwargs["no_speech_threshold"] == 0.6
    assert kwargs["compression_ratio_threshold"] == 2.4
    assert kwargs["log_prob_threshold"] == -1.0
    # word_timestamps default True → hallucination threshold active
    assert kwargs["hallucination_silence_threshold"] == 2.0


def test_custom_params_forwarded(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(
        Path("dummy.wav"),
        beam_size=10,
        initial_prompt="Kubernetes, Grafana",
        condition_on_previous_text=False,
        no_speech_threshold=0.75,
    )

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["beam_size"] == 10
    assert kwargs["initial_prompt"] == "Kubernetes, Grafana"
    assert kwargs["condition_on_previous_text"] is False
    assert kwargs["no_speech_threshold"] == 0.75


def test_hallucination_threshold_disabled_without_word_timestamps(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(Path("dummy.wav"), word_timestamps=False)

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["hallucination_silence_threshold"] is None


def test_vad_parameters_present_when_enabled(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(Path("dummy.wav"), vad=True)

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["vad_filter"] is True
    assert kwargs["vad_parameters"]["threshold"] == 0.5
    assert kwargs["vad_parameters"]["min_silence_duration_ms"] == 500
    # Phase 3: speech padding on by default to avoid clipped word onsets
    assert kwargs["vad_parameters"]["speech_pad_ms"] == 300


def test_vad_parameters_customisable(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(
        Path("dummy.wav"),
        vad=True,
        vad_threshold=0.3,
        vad_min_silence_ms=700,
        vad_speech_pad_ms=400,
    )

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["vad_parameters"] == {
        "threshold": 0.3,
        "min_silence_duration_ms": 700,
        "speech_pad_ms": 400,
    }


def test_vad_parameters_none_when_disabled(monkeypatch):
    capture: dict = {}
    fake_model = _install_fake_faster_whisper(monkeypatch, capture)

    transcribe(Path("dummy.wav"), vad=False)

    _, kwargs = fake_model.transcribe.call_args
    assert kwargs["vad_filter"] is False
    assert kwargs["vad_parameters"] is None
