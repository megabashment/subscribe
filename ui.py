from __future__ import annotations

import logging
import queue
import tempfile
import threading
from pathlib import Path

import os
import warnings
import streamlit as st

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SubScribe",
    page_icon="🎙️",
    layout="centered",
)

st.title("🎙️ SubScribe")
st.caption("Lokale Transkription · kein Cloud-Zwang")

# ── Sidebar: Settings ────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Einstellungen")

    model_size = st.selectbox(
        "Modell",
        ["tiny", "base", "small", "medium", "large-v3"],
        index=3,
        help="Größer = genauer, aber langsamer. 'medium' ist ein guter Kompromiss.",
    )

    language = st.selectbox(
        "Sprache",
        ["auto", "de", "en", "fr", "es", "it", "pl", "nl", "pt", "ru", "zh", "ja"],
        index=0,
        help="'auto' erkennt die Sprache automatisch.",
    )

    output_format = st.selectbox(
        "Ausgabeformat",
        ["srt", "vtt", "json"],
        index=0,
    )

    device_override = st.selectbox(
        "Gerät",
        ["auto", "cuda", "cpu"],
        index=0,
    )

    st.divider()
    st.markdown("**venv:** `C:\\Users\\chris\\projects\\venv`")

# ── File upload ──────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Mediendatei hochladen",
    type=["mp4", "mkv", "mov", "avi", "mp3", "wav", "m4a", "flac"],
    help="Video oder Audio — wird lokal verarbeitet, nichts wird hochgeladen.",
)

if not uploaded:
    st.info("Datei hochladen um zu starten.")
    st.stop()

st.success(f"Datei geladen: **{uploaded.name}** ({uploaded.size / 1_048_576:.1f} MB)")

# ── Run button ───────────────────────────────────────────────────────────────
if st.button("▶ Transkription starten", type="primary", use_container_width=True):

    log_queue: queue.Queue[str] = queue.Queue()
    result_holder: dict = {}

    # Patch logging so messages appear in the UI
    class QueueHandler(logging.Handler):
        _SKIP_PREFIXES = ("httpx", "huggingface_hub", "filelock", "urllib3")

        def emit(self, record: logging.LogRecord) -> None:
            if record.name.startswith(self._SKIP_PREFIXES):
                return
            log_queue.put(self.format(record))

    root_logger = logging.getLogger()
    q_handler = QueueHandler()
    q_handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    root_logger.addHandler(q_handler)
    root_logger.setLevel(logging.INFO)

    def run_transcription() -> None:
        try:
            from subscribe.utils.logging import setup_logging
            from subscribe.utils.device import detect_device
            from subscribe.audio_extract import extract_audio
            from subscribe.transcribe import transcribe
            from subscribe.export.srt import export_srt

            setup_logging("INFO")
            device = detect_device(None if device_override == "auto" else device_override)

            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)

                # Save upload to disk
                input_path = tmp_path / uploaded.name
                input_path.write_bytes(uploaded.getvalue())

                # Extract audio
                audio_path = extract_audio(input_path, tmp_path / "audio.wav")

                # Transcribe
                transcript = transcribe(
                    audio_path,
                    language=language,
                    model_size=model_size,
                    device=device,
                )

                # Export
                out_path = tmp_path / Path(uploaded.name).with_suffix(f".{output_format}").name
                if output_format == "srt":
                    export_srt(transcript, out_path)
                else:
                    log_queue.put(f"WARNING ui: Format '{output_format}' noch nicht implementiert (Sprint 2) — exportiere als SRT.")
                    out_path = out_path.with_suffix(".srt")
                    export_srt(transcript, out_path)

                result_holder["bytes"] = out_path.read_bytes()
                result_holder["filename"] = out_path.name
                result_holder["language"] = transcript.language
                result_holder["segments"] = len(transcript.segments)

        except Exception as exc:
            result_holder["error"] = str(exc)
        finally:
            log_queue.put("__DONE__")

    thread = threading.Thread(target=run_transcription, daemon=True)
    thread.start()

    log_box = st.empty()
    progress = st.progress(0, text="Wird gestartet…")
    log_lines: list[str] = []

    step_map = {
        "Audio extracted": (33, "Audio extrahiert…"),
        "Loading model": (50, "Modell wird geladen…"),
        "Transcribing": (60, "Transkription läuft…"),
        "Transcription done": (90, "Fertigstellen…"),
    }

    while True:
        try:
            msg = log_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        if msg == "__DONE__":
            break

        log_lines.append(msg)
        log_box.code("\n".join(log_lines[-20:]), language=None)

        for key, (pct, label) in step_map.items():
            if key in msg:
                progress.progress(pct, text=label)

    thread.join()
    root_logger.removeHandler(q_handler)

    if "error" in result_holder:
        st.error(f"Fehler: {result_holder['error']}")
    else:
        progress.progress(100, text="Fertig!")
        st.balloons()

        col1, col2, col3 = st.columns(3)
        col1.metric("Sprache", result_holder["language"].upper())
        col2.metric("Segmente", result_holder["segments"])
        col3.metric("Format", output_format.upper())

        st.download_button(
            label=f"⬇ {result_holder['filename']} herunterladen",
            data=result_holder["bytes"],
            file_name=result_holder["filename"],
            mime="text/plain",
            type="primary",
            use_container_width=True,
        )
