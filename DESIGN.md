# DESIGN.md — SubScribe

Architekturentscheidungen mit Begründung. Format angelehnt an ADRs (Architecture Decision Records), aber schlank gehalten.

---

## ADR-001: faster-whisper statt openai-whisper

**Entscheidung:** `faster-whisper` (CTranslate2-Backend) als primäre ASR-Engine.

**Begründung:** Deutlich geringerer Speicherverbrauch und höhere Geschwindigkeit bei identischer Modellqualität (gleiche Whisper-Gewichte, anderes Inference-Backend). Läuft sowohl auf CUDA als auch auf CPU performant — relevant, da SubScribe auf zwei unterschiedlichen Geräten (Windows-GPU, MacBook) laufen soll.

**Alternativen geprüft:** `openai-whisper` (Referenzimplementierung, langsamer), `whisper.cpp` (sehr schlank, aber Python-Integration umständlicher für das geplante Datenmodell).

---

## ADR-002: Segment-Timestamps in Phase 1, Word-Alignment optional in Phase 3

**Entscheidung:** MVP nutzt die nativen Segment-Timestamps von faster-whisper. Wort-genaues Forced Alignment (whisperX) erst in Sprint 3, wenn der Bedarf sich am echten Use-Case bestätigt.

**Begründung:** Segment-Timestamps reichen für valide .srt-Dateien aus. Word-Level-Alignment bringt zusätzliche Abhängigkeiten (eigenes Alignment-Modell pro Sprache) und Komplexität. Erst MVP zum Laufen bringen, dann Genauigkeit gezielt verbessern, statt Komplexität vorzuziehen.

---

## ADR-003: CLI statt GUI in Phase 1

**Entscheidung:** Keine grafische Oberfläche im MVP.

**Begründung:** Der Use-Case (Mediendatei rein, .srt raus) ist scriptbar und braucht keine Klickoberfläche, um nützlich zu sein. Eine GUI lässt sich später aufsetzen, falls der Workflow das rechtfertigt — sie ist aber eine eigene Entscheidung mit eigenem Aufwand, kein impliziter Folgeschritt.

---

## ADR-004: pydantic als Datenmodell-Schicht

**Entscheidung:** `Word`, `Segment`, `Transcript` als pydantic-Modelle statt lose typisierter Dicts.

**Begründung:** Validierung „for free", saubere JSON-Serialisierung für den Export, und ein stabiler interner Vertrag zwischen Transkriptions-Modul und Export-Modulen — wichtig, weil mehrere Exportformate (.srt, .vtt, .json) auf demselben Datenmodell aufbauen sollen, ohne Code zu duplizieren.

---

## ADR-005: Gerätekompatibilität (CUDA / Metal / CPU) als First-Class-Anforderung

**Entscheidung:** Automatische Geräteerkennung mit Fallback-Kette CUDA → MPS (Apple Silicon) → CPU, keine Annahme eines bestimmten Geräts im Code.

**Begründung:** Du nutzt sowohl den Windows-PC (Nvidia-GPU) als auch das MacBook gleichwertig. Das Tool darf nicht an ein Gerät gekoppelt sein — Hardcoding von `device="cuda"` würde es auf dem Mac unbrauchbar machen und umgekehrt.

---

## Offene Architekturfragen (noch keine Entscheidung)
- Konfigurationsformat: `.env` vs. `config.yaml` — Tendenz YAML wegen Lesbarkeit bei mehreren Optionen (Modellgröße, Default-Sprache, Output-Verzeichnis), finale Entscheidung in Sprint 0
- Paketmanager: `uv` vs. klassisches `venv`+`pip` — keine harte Anforderung, wird beim Setup pragmatisch entschieden
