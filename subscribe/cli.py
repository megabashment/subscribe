from __future__ import annotations

from typing import Optional
import typer

from subscribe import __version__
from subscribe.config import Settings
from subscribe.utils.logging import setup_logging
from subscribe.utils.device import detect_device

app = typer.Typer(help="SubScribe — local media transcription with word-level timestamps.")


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
    setup_logging(log_level)
    settings = Settings.load()
    effective_device = detect_device(device if device != "auto" else settings.device)
    app.info = app.info  # keep typer happy; device stored implicitly via log


@app.command()
def run(
    input_file: str = typer.Argument(..., help="Path to video or audio file"),
    lang: str = typer.Option("auto", "--lang", help="Language code (e.g. de, en) or 'auto'"),
    format: str = typer.Option("srt", "--format", help="Output format: srt | vtt | json"),
    model: str = typer.Option("medium", "--model", help="Whisper model size: tiny|base|small|medium|large-v3"),
) -> None:
    """Transcribe a media file and export subtitles."""
    typer.echo("Sprint 1 not yet implemented.")
    raise typer.Exit(code=0)
