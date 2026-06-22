# SubScribe

Lokale Medien-Transkription. Datei rein, `.srt` raus — kein Cloud-Dienst, kein Account.

**Input:** mp4, mkv, mov, avi, mp3, wav, m4a, flac  
**Output:** `.srt` (vtt + json folgen in Sprint 2)  
**Sprachen:** Auto-Detect oder explizit (`--lang de`)  
**GPU:** CUDA (Windows/Nvidia) und Apple MPS auto-detected, Fallback CPU

---

## Voraussetzungen

- Python 3.11+
- ffmpeg im PATH: `winget install Gyan.FFmpeg` (danach Shell neu starten)
- Node.js + npm (für das Frontend)

---

## Installation

```bash
git clone https://github.com/megabashment/subscribe.git
cd subscribe

# Python-Paket + API-Dependencies
pip install -e .

# Frontend-Dependencies
cd frontend && npm install && cd ..
```

---

## Starten

```bat
start.bat         # API (:8511) + UI (:5173) parallel — empfohlen
start_api.bat     # nur FastAPI
start_ui.bat      # nur React Dev-Server
```

Browser öffnet sich automatisch auf `http://localhost:5173`.  
Datei per Drag & Drop, Sprache/Modell wählen, Download.

---

## CLI (alternativ)

```bash
subscribe run input.mp4 --lang de
subscribe run input.mp4 --lang de --format srt --model large-v3
subscribe --help
```

---

## API

```
GET  /health       → {"status":"ok","device":"cpu","version":"0.0.1"}
POST /transcribe   → multipart: file, lang, model, format, device
                     → FileResponse (.srt)
```

Die API ist Premiere-Plugin-ready — `POST /transcribe` ist direkt aus einem CEP-Panel via `fetch()` ansprechbar.

---

## Entwicklung

```bash
pip install -e .
pytest
pytest tests/test_export_srt.py::test_fmt_time
```

Roadmap: [BACKLOG.md](BACKLOG.md) · Architekturentscheidungen: [DESIGN.md](DESIGN.md)
