# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Lokales CLI-Tool zur automatischen Transkription von Mediendateien mit Word-Level-Timestamps und Export in gängige Untertitelformate.

**Status:** Sprint 1 abgeschlossen — MVP-Transkription + Streamlit-UI lauffähig

---

## Zweck & Scope

Mediendateien (Video/Audio) lokal transkribieren — Spracherkennung, Wort-für-Wort-Timestamps, Export als `.srt`/`.vtt`/`.json`, ohne Cloud-Dienste.

**Out of Scope (Phase 1):** Kein Webservice, keine Live-Transkription, keine Übersetzung.

**MVP-Kriterium:** `mp4/mkv/mp3/wav` rein → valide `.srt` raus, die in VLC ohne Nachbearbeitung korrekt läuft.

---

## System-Abhängigkeiten

Diese müssen **vor** dem ersten `subscribe run` auf dem System installiert sein:

| Tool | Wann nötig | Installation |
|---|---|---|
| `ffmpeg` | Sprint 0 (Setup) | `winget install Gyan.FFmpeg` |
| CUDA Toolkit | optional, für GPU-Beschleunigung | nvidia.com |

**ffmpeg muss im PATH sein.** Nach `winget`-Installation einmalig Shell neu starten.

---

## Tech Stack

| Bereich | Wahl |
|---|---|
| ASR-Engine | `faster-whisper` (CTranslate2) |
| Alignment (Word-Level) | `whisperX` — optional, Phase 2 |
| Audio-Extraktion | `ffmpeg` via subprocess |
| CLI | `typer` |
| UI | `streamlit` (Port 8510, `start_ui.bat`) |
| Datenmodell | `pydantic` (Word, Segment, Transcript) |
| GPU | CUDA (Windows/Nvidia) · Metal/CPU (macOS) · Auto-Detect, Fallback CPU |
| Tests | `pytest` |
| Paketverwaltung | `venv` + `pip` (`C:\Users\chris\projects\venv\`) |

---

## Architektur

```
subscribe/
├── cli.py              # Typer-Entry-Point: subscribe run <file> [--lang] [--format] [--model]
├── audio_extract.py    # ffmpeg-Wrapper: Video → wav (16kHz mono)
├── transcribe.py       # faster-whisper Aufruf, Device-Detection
├── align.py            # Optional: whisperX Forced Alignment (Phase 2)
├── models.py           # Pydantic: Word, Segment, Transcript
├── config.py           # Settings laden (Modellgröße, Default-Sprache, Pfade)
├── export/
│   ├── srt.py
│   ├── vtt.py          # Sprint 2
│   └── json_export.py  # Sprint 2
└── utils/
    ├── device.py       # CUDA → MPS → CPU, mit --device Override
    └── logging.py
ui.py                   # Streamlit-UI
start_ui.bat            # UI starten (Doppelklick)
tests/
```

**Datenfluss:**
`Mediendatei → ffmpeg (audio_extract.py) → faster-whisper (transcribe.py) → Transcript (models.py) → Export`

---

## Befehle

```bash
# Einmalig installieren
pip install -e .   # venv: C:\Users\chris\projects\venv\Scripts\pip

# UI starten (empfohlen)
start_ui.bat       # öffnet http://localhost:8510

# CLI
subscribe run input.mp4 --lang de --format srt
subscribe run input.mp4 --lang de --format srt --model large-v3

# Tests
pytest
pytest tests/test_export_srt.py
pytest tests/test_export_srt.py::test_fmt_time
```

---

## Coding-Richtlinien

- **Type Hints überall**, pydantic-Modelle statt loser Dicts
- **Device-Detection** zentral in `utils/device.py` — nicht inline in anderen Modulen
- **Keine globalen Konstanten für Pfade** — alles über `config.py` / CLI-Parameter
- **Keine hardcodierte Modellgröße** — Default `medium`, Override per `--model tiny|base|small|medium|large-v3`
- **Logging statt print** (`logging`-Modul, Level konfigurierbar)
- Jede neue Exportfunktion bekommt einen Unit-Test mit einer festen Beispiel-Transcript-Fixture

---

## Dokumentation

- `BACKLOG.md` — Sprint-Plan, offene Ideen, Versionierung, Git-Konventionen
- `DESIGN.md` — Architekturentscheidungen mit Begründung
- `CHANGELOG.md` — ab `v0.1.0` (Keep-a-Changelog-Format)
