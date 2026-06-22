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

### Sprint 2.5 — Review/Edit-UI (nach Sprint 2, vor Sprint 3)
Ziel: Transkriptions-Ergebnis prüfen und korrigieren bevor Export.

**Player-View**
- `<video>`/`<audio>`-Element, kein Wellenform-Player
- Aktueller Cue wird während Wiedergabe hervorgehoben (Timestamp-Sync via `timeupdate`)
- Klick auf Cue → Player springt zur Startzeit

**Cue-Liste (editierbar)**
- Start, Ende, Text inline editierbar, kein Modal
- Zeitfelder validiert: Start < Ende, kein Overlap mit Nachbar-Cue, Live-Fehleranzeige
- Text mehrzeilig, Zeichenzähler/Zeile (42 Richtwert, nicht hart blocken)
- Cue löschen / splitten / mergen

**Export**
- `POST /export` in `api/routes/export.py` — nimmt editierte Cues entgegen, läuft serverseitige SRT/VTT-Validierung (Sequenznummern, Start < Ende, kein Overlap, Encoding)
- Frontend blockiert "Speichern" bei Overlap-Fehler, warnt bei Abweichung vom Whisper-Original
- Kein Auto-Save — explizites "Speichern" persistiert

**Verifikation:** Export in VLC öffnen. Edge Cases: leerer Cue-Text, Overlap vor Speichern, Sonderzeichen.

**Neue API-Endpunkte:**
- `POST /export` → nimmt `{cues: [...], format: "srt"|"vtt"|"json"}` → FileResponse

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

- 🔴 Review/Edit-UI — Sprint 2.5 (nächster Sprint)
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
