from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def probe_duration(path: Path) -> float | None:
    """Return duration in seconds from a WAV file header, or via ffprobe for other formats."""
    try:
        if path.suffix.lower() == ".wav":
            import wave
            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate   = wf.getframerate()
                return frames / rate if rate else None
    except Exception:
        pass

    if not shutil.which("ffprobe"):
        return None
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_entries", "format=duration", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            dur = data.get("format", {}).get("duration")
            return float(dur) if dur else None
    except Exception:
        pass
    return None


def _build_filter_chain(normalize: bool, denoise: bool) -> str | None:
    """Assemble the ffmpeg -af filter chain. Returns None if no filters active.

    Filters (all local, no external models needed):
    - highpass/lowpass: keep the speech band, drop rumble & high-freq hiss
    - afftdn: ffmpeg's built-in FFT denoiser
    - loudnorm: EBU R128 loudness normalisation (even level helps Whisper)
    """
    filters: list[str] = []
    if normalize or denoise:
        # Restrict to the speech band first — cheap and helps both stages
        filters.append("highpass=f=80")
        filters.append("lowpass=f=8000")
    if denoise:
        filters.append("afftdn")
    if normalize:
        filters.append("loudnorm")
    return ",".join(filters) if filters else None


def _build_cmd(input_path: Path, output_path: Path, af: str | None) -> list[str]:
    cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn"]
    if af:
        cmd += ["-af", af]
    cmd += ["-ac", "1", "-ar", "16000", "-f", "wav", str(output_path)]
    return cmd


def extract_audio(
    input_path: Path,
    output_path: Path,
    normalize: bool = True,
    denoise: bool = False,
) -> Path:
    """Extract audio from a media file to a 16kHz mono WAV.

    Optionally applies a local audio-cleanup filter chain (normalize / denoise)
    that improves recognition on quiet or noisy material. If the filtered
    extraction fails (e.g. a filter is missing in the installed ffmpeg build),
    it falls back to an unfiltered extraction.

    Raises FileNotFoundError if ffmpeg is not on PATH.
    Raises RuntimeError if ffmpeg exits with an error (even unfiltered).
    """
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError(
            "ffmpeg not found on PATH. Install it from https://ffmpeg.org/download.html"
        )

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    af = _build_filter_chain(normalize, denoise)
    cmd = _build_cmd(input_path, output_path, af)
    logger.debug("Running: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        if af:
            # Filter chain may be unsupported in this ffmpeg build → retry clean
            logger.warning(
                "ffmpeg filtered extraction failed, retrying without filters:\n%s",
                result.stderr,
            )
            cmd = _build_cmd(input_path, output_path, None)
            result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    logger.info("Audio extracted: %s", output_path)
    return output_path
