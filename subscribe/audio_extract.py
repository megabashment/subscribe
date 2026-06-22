from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_audio(input_path: Path, output_path: Path) -> Path:
    """Extract audio from a media file to a 16kHz mono WAV.

    Raises FileNotFoundError if ffmpeg is not on PATH.
    Raises RuntimeError if ffmpeg exits with an error.
    """
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError(
            "ffmpeg not found on PATH. Install it from https://ffmpeg.org/download.html"
        )

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_path),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "wav",
        str(output_path),
    ]

    logger.debug("Running: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    logger.info("Audio extracted: %s", output_path)
    return output_path
