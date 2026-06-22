# DESIGN.md — SubScribe

Architekturentscheidungen mit Begründung (ADR-Format, schlank).

---

## ADR-001: faster-whisper statt openai-whisper

**Entscheidung:** `faster-whisper` (CTranslate2-Backend) als primäre ASR-Engine.

**Begründung:** Gleiche Modellgewichte wie openai-whisper, aber deutlich schneller und speichersparender. Läuft auf CUDA und CPU performant — relevant für den Einsatz auf Windows-GPU und MacBook.

---

## ADR-002: Segment-Timestamps im MVP, Word-Alignment optional später

**Entscheidung:** MVP nutzt native Segment-Timestamps. Wort-genaues Forced Alignment (whisperX) erst in Sprint 3, wenn der Bedarf am echten Use-Case bestätigt ist.

**Begründung:** Segment-Timestamps reichen für valide .srt-Dateien. Word-Level-Alignment bringt zusätzliche Abhängigkeiten pro Sprache — erst MVP stabilisieren.

---

## ADR-003: FastAPI statt Streamlit als UI-Backend

**Entscheidung:** FastAPI + React (Vite) statt Streamlit.

**Begründung:** Streamlit ist klobig, hat kein natives Drag & Drop und ist schwer erweiterbar. FastAPI gibt eine saubere REST-API (`POST /transcribe`), die direkt als Basis für ein zukünftiges Premiere CEP-Plugin dient — kein Umbau nötig. React-Frontend läuft separat, bleibt austauschbar.

**Ports:** API `:8511`, Frontend Dev-Server `:5173`.

---

## ADR-004: pydantic als Datenmodell-Schicht

**Entscheidung:** `Word`, `Segment`, `Transcript` als pydantic-Modelle.

**Begründung:** Validierung, JSON-Serialisierung und ein stabiler Vertrag zwischen Transkriptions- und Export-Modulen — alle Exportformate (.srt, .vtt, .json) bauen auf demselben Modell auf.

---

## ADR-005: Automatische Geräteerkennung (CUDA → MPS → CPU)

**Entscheidung:** Fallback-Kette in `utils/device.py`, kein Hardcoding.

**Begründung:** Das Tool läuft auf Windows (Nvidia-GPU) und MacBook gleichwertig. `torch` wird optional importiert — `subscribe --help` funktioniert auch ohne GPU-Libs.

---

## ADR-006: SRT mit UTF-8 BOM, VTT ohne BOM, JSON ohne BOM

**Entscheidung:** SRT wird als `utf-8-sig` geschrieben (BOM), VTT und JSON als `utf-8` (kein BOM).

**Begründung:** VLC auf Windows ignoriert SRT-Dateien ohne BOM oder zeigt Umlaute falsch an. Die WebVTT-Spec schreibt explizit vor, dass kein BOM verwendet werden darf. JSON hat keine Encoding-Vorgabe, BOM würde viele Parser brechen.

---

## ADR-007: Review/Edit-UI als Sprint 2.5 vor whisperX

**Entscheidung:** Review/Edit-UI (Player + editierbare Cue-Liste + serverseitiger Export-Endpunkt) kommt vor Word-Level-Alignment (Sprint 3).

**Begründung:** Whisper-Segment-Timestamps sind gut genug für den MVP, aber Fehler kommen vor (falsche Wortgrenzen, Stille-Artefakte). Eine Edit-UI erlaubt Korrekturen ohne Roundtrip — das ist für den täglichen Gebrauch wichtiger als präzisere Timestamps, die man danach nicht mehr korrigieren kann. Außerdem: der `POST /export`-Endpunkt der Edit-UI liefert die serverseitige Validierungs-Logik, die Sprint 3 sowieso braucht.

---

## Offene Fragen

- `config.yaml` für Defaults — Tendenz YAML, Entscheidung in Sprint 4
