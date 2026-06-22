# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Lokales CLI-Tool + Web-App zur automatischen Transkription von Mediendateien mit Word-Level-Timestamps und Export in gängige Untertitelformate.

**Status:** Sprint 2 abgeschlossen — VTT/JSON-Export, SRT-BOM-Fix, 27 Tests grün

---

## Zweck & Scope

Mediendateien (Video/Audio) lokal transkribieren — Spracherkennung, Wort-für-Wort-Timestamps, Export als `.srt`/`.vtt`/`.json`, ohne Cloud-Dienste.

**Out of Scope (Phase 1):** Keine Live-Transkription, keine Übersetzung.

**MVP-Kriterium:** `mp4/mkv/mp3/wav` rein → valide `.srt` raus, die in VLC ohne Nachbearbeitung korrekt läuft.

---

## System-Abhängigkeiten

Diese müssen **vor** dem ersten `subscribe run` auf dem System installiert sein:

| Tool | Wann nötig | Installation |
|---|---|---|
| `ffmpeg` | Sprint 0 (Setup) | `winget install Gyan.FFmpeg` |
| `node` + `npm` | Frontend-Dev | bereits vorhanden (v25.8) |
| CUDA Toolkit | optional, für GPU-Beschleunigung | nvidia.com |

**ffmpeg muss im PATH sein.** Nach `winget`-Installation einmalig Shell neu starten.

---

## Tech Stack

| Bereich | Wahl |
|---|---|
| ASR-Engine | `faster-whisper` (CTranslate2) |
| Alignment (Word-Level) | `whisperX` — optional, Phase 2 |
| Audio-Extraktion | `ffmpeg` via subprocess |
| API | `FastAPI` + `uvicorn` (Port 8511) |
| Frontend | React + Vite (Port 5173) — kein Framework, plain CSS |
| CLI | `typer` |
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
├── models.py           # Pydantic: Word, Segment, Transcript
├── config.py           # Settings laden (Modellgröße, Default-Sprache, Pfade)
├── export/srt.py       # UTF-8 mit BOM (utf-8-sig)
├── export/vtt.py       # UTF-8 ohne BOM, Dot-Separator
├── export/json_export.py  # JSON mit Words + Konfidenz
└── utils/device.py     # CUDA → MPS → CPU, mit --device Override
api/
├── server.py           # FastAPI App + CORS
├── models.py           # Request/Response Schemas
└── routes/
    ├── health.py       # GET /health
    └── transcribe.py   # POST /transcribe (multipart)
frontend/src/
├── App.jsx
└── components/         # DropZone, Settings, ProgressLog, ResultPanel
start.bat               # API + UI parallel starten (empfohlen)
start_api.bat           # Nur API (Port 8511)
start_ui.bat            # Nur Frontend-Dev-Server (Port 5173)
```

**Datenfluss:**
`Mediendatei → POST /transcribe → ffmpeg → faster-whisper → Transcript → SRT → FileResponse`

**Premiere-Plugin:** REST-API auf Port 8511 ist direkt via `fetch()` aus einem CEP-Panel ansprechbar — kein Umbau nötig.

---

## Befehle

```bash
# Einmalig installieren
pip install -e .           # venv: C:\Users\chris\projects\venv\Scripts\pip
cd frontend && npm install

# Starten (empfohlen: beides zusammen)
start.bat                  # öffnet API auf :8511, UI auf http://localhost:5173

# Einzeln
start_api.bat              # nur FastAPI
start_ui.bat               # nur React Dev-Server

# CLI (alternativ zur UI)
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
- API-Routen: Fehler immer als `HTTPException` mit klarer `detail`-Message
- Jede neue Exportfunktion bekommt einen Unit-Test mit einer festen Beispiel-Transcript-Fixture

---

## Dokumentation

- `BACKLOG.md` — Sprint-Plan, offene Ideen, Versionierung, Git-Konventionen
- `DESIGN.md` — Architekturentscheidungen mit Begründung
- `CHANGELOG.md` — ab `v0.1.0` (Keep-a-Changelog-Format)
