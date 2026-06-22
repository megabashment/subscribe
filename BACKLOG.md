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

### ✅ Sprint 2 — Weitere Formate
- VTT-Export (`export/vtt.py`) — UTF-8 ohne BOM, Dot-Separator
- JSON-Export (`export/json_export.py`) — Segments + Words mit Konfidenz
- SRT-BOM-Fix (utf-8-sig für VLC/Windows-Kompatibilität)
- CLI + API: alle drei Formate vollständig aktiviert, Fallbacks entfernt
- DoD: alle drei Formate via UI und CLI wählbar, 27 Tests grün

### ✅ Sprint 2.5 — Review/Edit-UI
- `POST /export` (`api/routes/export.py`) — nimmt editierte Cues, serverseitige Validierung (Overlap, start<end, Encoding)
- `POST /transcribe/cues` — gibt JSON-Cues zurück statt direktem Download
- `Player.jsx` — Video/Audio-Player mit `timeupdate`-Sync
- `CueEditor.jsx` — inline editierbare Cue-Liste, Zeitfelder, Löschen/Splitten/Mergen, Zeichenzähler
- App-Flow: Upload → Transkription → Editor → Export
- DoD: 37 Tests grün, Overlap/Validierungsfehler blocken Export

### ✅ Sprint 3 — Word-Level-Timestamps
- `word_timestamps=True` als Default in `transcribe.py`
- `--word-level/--no-word-level` Flag in CLI
- `word_level: bool = Form(True)` in API-Routen
- `word_timestamps` als Settings-Feld in `config.py`
- DoD: Words werden in Transcript-Modell befüllt, JSON-Export enthält Words mit Konfidenz

### ✅ Sprint 4 — Batch & Komfort
- `subscribe batch <folder>` CLI-Befehl (mit `--glob`, `--output`, `--format`, `--word-level`)
- `POST /batch` API-Endpunkt mit SSE-Fortschrittsevents (`start`, `progress`, `done`)
- `config.yaml.example` als Vorlage für Defaults
- `config.py`: `word_timestamps` und `format` als konfigurierbare Felder
- DoD: 5 Dateien im Ordner → 5 Exports ohne manuelles Eingreifen

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

- ⚪ Speaker-Diarization (pyannote) — eigene Abhängigkeit, separat bewerten
- ⚪ Übersetzungsmodus (Whisper „translate") — kein MVP-Feature
- ⚪ Premiere CEP-Plugin — REST-API auf :8511 ist bereits kompatibel, Plugin ist dünner Client
- ⚪ `.ass`-Format
- ⚪ whisperX Forced Alignment — evaluieren ob Mehrwert über `word_timestamps=True` hinaus

## Verworfen

- Cloud-basierte ASR — widerspricht "lokal, kein Cloud-Zwang"
- Streamlit-UI — durch FastAPI + React abgelöst
