# BACKLOG.md — SubScribe

Format: `[Prio] Titel — Beschreibung`
Prio: 🔴 hoch · 🟡 mittel · ⚪ niedrig/später

---

## Sprints

### ✅ Sprint 0 — Setup
- Projektstruktur, venv, ffmpeg (`winget install Gyan.FFmpeg`), Device-Detection
- DoD: `subscribe --help` läuft, ffmpeg im PATH, Device geloggt

### ✅ Sprint 1 — MVP Transkription + UI
- Audio-Extraktion (ffmpeg), faster-whisper, SRT-Export
- FastAPI (`POST /transcribe`, `GET /health`) auf Port 8511
- React + Vite Frontend mit Drag & Drop auf Port 5173
- DoD: Datei in UI droppen → .srt Download, CLI läuft parallel

### Sprint 2 — Weitere Formate
- VTT-Export (`export/vtt.py`)
- JSON-Export mit Wort-Timestamps + Konfidenz (`export/json_export.py`)
- Frontend: Format-Fallback entfernen sobald vtt/json implementiert
- DoD: alle drei Formate via UI und CLI wählbar

### Sprint 3 — Word-Level-Precision (whisperX)
- Forced Alignment optional (`--word-level` Flag, `word_timestamps=True` in transcribe.py)
- DoD: Wort-Timestamps nachweislich präziser als Segment-Approximation

### Sprint 4 — Batch & Komfort
- Batch-Verarbeitung ganzer Ordner (CLI + API)
- Fortschrittsanzeige im Frontend (SSE oder Polling)
- Konfigurierbare Defaults via `config.yaml`
- DoD: Ordner mit 5 Dateien → 5 .srt ohne manuelles Eingreifen

---

## Versionierung

- **SemVer** `MAJOR.MINOR.PATCH` — `0.x.x` bis Sprint 3, `1.0.0` = stabil getestet
- Tags pro Sprint: `v0.1.0-sprint1` etc.
- `CHANGELOG.md` ab `v0.1.0`

## Git-Konventionen

- **Branching:** `master` (stabil) + `feature/<kurzbeschreibung>` pro Sprint-Item
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)

---

## Offen

- 🟡 VTT-Export — Sprint 2
- 🟡 JSON-Export mit Word-Timestamps — Sprint 2
- 🟡 SSE/Polling für Fortschrittsanzeige im Frontend — Sprint 4
- 🟡 Batch-Modus (Ordner) — Sprint 4
- ⚪ whisperX Forced Alignment — Sprint 3, erst evaluieren ob Mehrwert für den Use-Case
- ⚪ Speaker-Diarization (pyannote) — eigene Abhängigkeit, separat bewerten
- ⚪ Übersetzungsmodus (Whisper „translate") — kein MVP-Feature
- ⚪ Premiere CEP-Plugin — REST-API auf :8511 ist bereits kompatibel, Plugin ist dünner Client
- ⚪ `.ass`-Format

## Verworfen

- Cloud-basierte ASR — widerspricht "lokal, kein Cloud-Zwang"
- Streamlit-UI — durch FastAPI + React abgelöst
