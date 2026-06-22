from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional

import typer

from subscribe import __version__
from subscribe.config import Settings
from subscribe.utils.logging import setup_logging
from subscribe.utils.device import detect_device

app = typer.Typer(help="SubScribe — local media transcription with word-level timestamps.")

_settings: Settings = Settings()
_device: str = "cpu"


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"SubScribe {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", callback=version_callback, is_eager=True),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level (DEBUG, INFO, WARNING)"),
    device: str = typer.Option("auto", "--device", help="Force device: auto | cuda | mps | cpu"),
) -> None:
    global _settings, _device
    setup_logging(log_level)
    _settings = Settings.load()
    _device = detect_device(device if device != "auto" else _settings.device)


@app.command()
def run(
    input_file: str = typer.Argument(..., help="Path to video or audio file"),
    lang: str = typer.Option("auto", "--lang", help="Language code (e.g. de, en) or 'auto'"),
    format: str = typer.Option("srt", "--format", help="Output format: srt | vtt | json"),
    model: str = typer.Option("medium", "--model", help="Whisper model size: tiny|base|small|medium|large-v3"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: next to input)"),
) -> None:
    """Transcribe a media file and export subtitles."""
    from subscribe.audio_extract import extract_audio
    from subscribe.transcribe import transcribe
    from subscribe.export.srt import export_srt
    from subscribe.export.vtt import export_vtt
    from subscribe.export.json_export import export_json

    input_path = Path(input_file)
    if not input_path.exists():
        typer.echo(f"Error: file not found: {input_path}", err=True)
        raise typer.Exit(code=1)

    if format not in ("srt", "vtt", "json"):
        typer.echo(f"Error: unsupported format '{format}'. Choose srt, vtt, or json.", err=True)
        raise typer.Exit(code=1)

    out_path = Path(output) if output else input_path.with_suffix(f".{format}")

    with tempfile.TemporaryDirectory() as tmp:
        audio_path = extract_audio(input_path, Path(tmp) / "audio.wav")
        transcript = transcribe(
            audio_path,
            language=lang,
            model_size=model,
            device=_device,
        )

    if format == "srt":
        result = export_srt(transcript, out_path)
    elif format == "vtt":
        result = export_vtt(transcript, out_path)
    elif format == "json":
        result = export_json(transcript, out_path)

    typer.echo(f"Saved: {result}")
