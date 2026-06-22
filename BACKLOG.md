# BACKLOG.md — SubScribe

Format: `[Prio] Titel — Beschreibung (Sprint-Zuordnung falls bekannt)`
Prio: 🔴 hoch · 🟡 mittel · ⚪ niedrig/später

---

## Sprints

### Sprint 0 — Setup (aktuell)
- Projektstruktur, venv/uv, ffmpeg-Check, CLAUDE.md/BACKLOG.md/DESIGN.md
- Device-Detection-Modul (cuda/mps/cpu)
- DoD: `subscribe --help` läuft, Device wird korrekt erkannt und geloggt

### Sprint 1 — MVP Transkription
- Audio-Extraktion aus Video (ffmpeg)
- faster-whisper Integration, Segment-Timestamps
- SRT-Export
- CLI: `subscribe run input.mp4 --lang de --format srt`
- DoD: Test-Video → valide .srt, in VLC korrekt synchron

### Sprint 2 — Wortliste & weitere Formate
- pydantic-Datenmodell (Word/Segment/Transcript) vollständig
- JSON-Export der Wortliste mit Timestamps + Konfidenz
- VTT-Export
- DoD: JSON enthält jedes erkannte Wort mit Start/Ende/Konfidenz

### Sprint 3 — Word-Level-Precision (whisperX)
- Forced Alignment optional zuschaltbar (`--word-level`)
- Vergleich Genauigkeit vs. Sprint-1-Segmentierung
- DoD: Wort-Timestamps nachweislich präziser als Segment-Approximation

### Sprint 4 — Batch & Komfort
- Batch-Verarbeitung ganzer Ordner
- Fortschrittsanzeige (rich/tqdm)
- Konfigurierbare Defaults via `config.yaml`
- DoD: Ordner mit 5 Dateien → 5 saubere .srt ohne manuelles Eingreifen

---

## Versionierung

- **SemVer** `MAJOR.MINOR.PATCH` — `0.x.x` während Sprint 0–3, `1.0.0` = MVP stabil getestet
- Tags pro Sprint: `v0.1.0-sprint1` etc.
- `CHANGELOG.md` ab `0.1.0` (Keep-a-Changelog-Format)

## Git-Konventionen

- **Branching:** `main` (stabil) + `feature/<kurzbeschreibung>` pro Sprint-Item
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- `.gitignore`: venv, `__pycache__`, Modell-Caches (`~/.cache/whisper`), Testmediendateien > 5 MB

---

## Offen

- 🔴 Device-Detection robust testen auf beiden Geräten (Windows CUDA + MacBook Metal/CPU) — Sprint 0
- 🔴 ffmpeg-Verfügbarkeit prüfen & klare Fehlermeldung wenn nicht installiert — Sprint 0
- 🔴 Modellgröße konfigurierbar, Default festlegen (medium vs. large-v3) — Sprint 1
- 🟡 whisperX Forced Alignment evaluieren — lohnt sich der Mehraufwand für Word-Level-Precision? — Sprint 3
- 🟡 Konfidenzwerte pro Wort sauber durchreichen ins JSON — Sprint 2
- 🟡 Batch-Modus für ganze Ordner — Sprint 4
- 🟡 Fortschrittsanzeige bei langen Dateien (rich/tqdm) — Sprint 4
- ⚪ Speaker-Diarization (wer spricht wann) — eigenes Modul, eigene Abhängigkeit (pyannote), separat evaluieren
- ⚪ Übersetzungsmodus (Whisper „translate" statt „transcribe") — kein MVP-Feature
- ⚪ Einfaches lokales Web-UI statt CLI, falls CLI im Alltag nervt
- ⚪ Untertitel-Stil/Formatierung (Zeilenlänge, max. Zeichen/Zeile für SRT nach Lesbarkeits-Konventionen)
- ⚪ Automatisches Trimmen von Stille/Pausen vor Transkription
- ⚪ Unterstützung für .ass-Format
- ⚪ Re-Evaluierung „kein Produktplan" — falls sich das Tool im Alltag bewährt, separate Entscheidung zu GUI/Distribution

## Erledigt

*(wird gepflegt, sobald Sprint-Items abgeschlossen sind)*

## Verworfen

- Cloud-basierte ASR-Dienste (Google/Azure Speech) — widerspricht "lokal, kein Cloud-Zwang"
