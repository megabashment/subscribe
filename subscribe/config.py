from __future__ import annotations

import yaml
from pathlib import Path
from pydantic import BaseModel


class Settings(BaseModel):
    model_size: str = "medium"
    language: str = "auto"
    output_dir: str = "."
    device: str = "auto"
    word_timestamps: bool = True
    format: str = "srt"

    # Decoding-Qualität (Phase 1)
    beam_size: int = 5
    initial_prompt: str | None = None
    condition_on_previous_text: bool = True
    no_speech_threshold: float = 0.6
    compression_ratio_threshold: float = 2.4
    log_prob_threshold: float = -1.0
    hallucination_silence_threshold: float | None = 2.0

    # Audio-Preprocessing (Phase 2)
    normalize_audio: bool = True
    denoise_audio: bool = False

    # VAD-Feintuning (Phase 3)
    vad_threshold: float = 0.5
    vad_min_silence_ms: int = 500
    vad_speech_pad_ms: int = 300

    # Forced Alignment (Phase 4, optional — benötigt requirements-align.txt)
    align: bool = False
    align_device: str | None = None  # None = gleiches Device wie Whisper; "cpu" spart VRAM

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        config_path = path or Path("config.yaml")
        if config_path.exists():
            with config_path.open() as f:
                data = yaml.safe_load(f) or {}
            return cls(**data)
        return cls()
