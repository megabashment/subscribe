# SubScribe

Local media transcription with word-level timestamps. No cloud, no accounts — runs entirely on your machine.

## What it does

Feed it a video or audio file, get back a `.srt` subtitle file (and optionally `.vtt` or a word-level `.json`) that plays correctly in VLC without any manual cleanup.

**Supported input:** mp4, mkv, mp3, wav, m4a, flac  
**Output formats:** `.srt`, `.vtt`, `.json`  
**Languages:** auto-detect or explicit (`--lang de`, `--lang en`, …)  
**GPU:** CUDA (Windows/Nvidia) and Apple Silicon MPS auto-detected, falls back to CPU

## Installation

Requires Python 3.11+ and [ffmpeg](https://ffmpeg.org/download.html) on your PATH.

```bash
# Clone
git clone https://github.com/megabashment/subscribe.git
cd subscribe

# Install (uv recommended)
uv pip install -e .
# or
pip install -e .
```

## Usage

```bash
# Check everything works
subscribe --help
subscribe --version

# Transcribe (Sprint 1+)
subscribe run input.mp4 --lang de
subscribe run input.mp4 --lang de --format json --model large-v3
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Status

Currently Sprint 0 — scaffold and device detection only. `subscribe run` outputs "Sprint 1 not yet implemented."  
See [BACKLOG.md](BACKLOG.md) for the roadmap.
