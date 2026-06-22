# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> Lokales CLI-Tool zur automatischen Transkription von Mediendateien mit Word-Level-Timestamps und Export in gängige Untertitelformate.

**Status:** Konzept / Sprint 0 — noch kein Code, nur Planung

---

## Zweck & Scope

Mediendateien (Video/Audio) lokal transkribieren — Spracherkennung, Wort-für-Wort-Timestamps, Export als `.srt`/`.vtt`/`.json`, ohne Cloud-Dienste.

**Out of Scope (Phase 1):** Kein Webservice, keine GUI, keine Live-Transkription, keine Übersetzung.

**MVP-Kriterium:** `mp4/mkv/mp3/wav` rein → valide `.srt` raus, die in VLC ohne Nachbearbeitung korrekt läuft. Plus strukturierte Wortliste (JSON) als Nebenprodukt.

---

## Tech Stack

| Bereich | Wahl |
|---|---|
| ASR-Engine | `faster-whisper` (CTranslate2) |
| Alignment (Word-Level) | `whisperX` — optional, Phase 2 |
| Audio-Extraktion | `ffmpeg` via subprocess |
| CLI | `typer` |
| Datenmodell | `pydantic` (Word, Segment, Transcript) |
| GPU | CUDA (Windows/Nvidia) · Metal/CPU (macOS) · Auto-Detect, Fallback CPU |
| Tests | `pytest` |
| Paketverwaltung | `uv` bevorzugt, sonst `venv` + `pip` |

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
│   ├── vtt.py
│   └── json_export.py
└── utils/
    ├── device.py       # CUDA → MPS → CPU, mit --device Override
    └── logging.py
tests/
```

**Datenfluss:**
`Mediendatei → ffmpeg → faster-whisper → [whisperX] → Transcript (pydantic) → Export`

---

## Befehle

```bash
# Installieren (uv bevorzugt)
uv pip install -r requirements.txt
# oder
pip install -r requirements.txt

# CLI starten
python -m subscribe run input.mp4 --lang de --format srt
python -m subscribe run input.mp4 --lang de --format json --model large-v3

# Tests
pytest
pytest tests/test_export.py          # einzelne Datei
pytest tests/test_export.py::test_srt_basic  # einzelne Funktion
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
