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
def batch(
    input_dir: str = typer.Argument(..., help="Directory with media files"),
    lang: str = typer.Option("auto", "--lang"),
    format: str = typer.Option("srt", "--format", help="srt | vtt | json"),
    model: str = typer.Option("medium", "--model"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output directory (default: same as input)"),
    word_level: bool = typer.Option(True, "--word-level/--no-word-level"),
    vad: bool = typer.Option(True, "--vad/--no-vad", help="Voice activity detection (filters silence/noise)"),
    beam_size: int = typer.Option(5, "--beam-size", help="Beam size: 1 = fast/greedy, 5 = default, 10 = more accurate"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Context/jargon/names to guide recognition"),
    normalize: bool = typer.Option(True, "--normalize/--no-normalize", help="Normalize loudness + speech-band filter"),
    denoise: bool = typer.Option(False, "--denoise/--no-denoise", help="FFT denoise (for noisy audio)"),
    align: bool = typer.Option(False, "--align/--no-align", help="Forced alignment via whisperX (sharper word timings)"),
    glob: str = typer.Option("*", "--glob", help="File glob pattern (e.g. '*.mp4')"),
) -> None:
    """Transcribe all media files in a directory."""
    from subscribe.audio_extract import extract_audio
    from subscribe.transcribe import transcribe as do_transcribe
    from subscribe.export.srt import export_srt
    from subscribe.export.vtt import export_vtt
    from subscribe.export.json_export import export_json
    import tempfile

    MEDIA_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}

    dir_path = Path(input_dir)
    if not dir_path.is_dir():
        typer.echo(f"Error: not a directory: {dir_path}", err=True)
        raise typer.Exit(code=1)

    if format not in ("srt", "vtt", "json"):
        typer.echo(f"Error: unsupported format '{format}'.", err=True)
        raise typer.Exit(code=1)

    out_dir = Path(output) if output else dir_path
    out_dir.mkdir(parents=True, exist_ok=True)

    files = [f for f in sorted(dir_path.glob(glob)) if f.suffix.lower() in MEDIA_EXTS]
    if not files:
        typer.echo("No media files found.")
        raise typer.Exit()

    typer.echo(f"Found {len(files)} file(s). Processing…")
    ok = fail = 0

    for f in files:
        typer.echo(f"  [{ok + fail + 1}/{len(files)}] {f.name}")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                audio_path = extract_audio(f, Path(tmp) / "audio.wav", normalize=normalize, denoise=denoise)
                transcript = do_transcribe(
                    audio_path, language=lang, model_size=model,
                    device=_device, word_timestamps=word_level, vad=vad,
                    vad_threshold=_settings.vad_threshold,
                    vad_min_silence_ms=_settings.vad_min_silence_ms,
                    vad_speech_pad_ms=_settings.vad_speech_pad_ms,
                    beam_size=beam_size,
                    initial_prompt=prompt or _settings.initial_prompt,
                    condition_on_previous_text=_settings.condition_on_previous_text,
                    no_speech_threshold=_settings.no_speech_threshold,
                    compression_ratio_threshold=_settings.compression_ratio_threshold,
                    log_prob_threshold=_settings.log_prob_threshold,
                    hallucination_silence_threshold=_settings.hallucination_silence_threshold,
                    align=align or _settings.align,
                    align_device=_settings.align_device,
                )
            out_path = out_dir / f"{f.stem}.{format}"
            if format == "srt":
                export_srt(transcript, out_path)
            elif format == "vtt":
                export_vtt(transcript, out_path)
            elif format == "json":
                export_json(transcript, out_path)
            typer.echo(f"    ✓ {out_path.name}")
            ok += 1
        except Exception as exc:
            typer.echo(f"    ✗ {exc}", err=True)
            fail += 1

    typer.echo(f"\nDone: {ok} succeeded, {fail} failed.")


@app.command()
def run(
    input_file: str = typer.Argument(..., help="Path to video or audio file"),
    lang: str = typer.Option("auto", "--lang", help="Language code (e.g. de, en) or 'auto'"),
    format: str = typer.Option("srt", "--format", help="Output format: srt | vtt | json"),
    model: str = typer.Option("medium", "--model", help="Whisper model size: tiny|base|small|medium|large-v3"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (default: next to input)"),
    word_level: bool = typer.Option(True, "--word-level/--no-word-level", help="Include word-level timestamps"),
    vad: bool = typer.Option(True, "--vad/--no-vad", help="Voice activity detection (filters silence/noise)"),
    beam_size: int = typer.Option(5, "--beam-size", help="Beam size: 1 = fast/greedy, 5 = default, 10 = more accurate"),
    prompt: Optional[str] = typer.Option(None, "--prompt", help="Context/jargon/names to guide recognition"),
    normalize: bool = typer.Option(True, "--normalize/--no-normalize", help="Normalize loudness + speech-band filter"),
    denoise: bool = typer.Option(False, "--denoise/--no-denoise", help="FFT denoise (for noisy audio)"),
    align: bool = typer.Option(False, "--align/--no-align", help="Forced alignment via whisperX (sharper word timings)"),
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
        audio_path = extract_audio(input_path, Path(tmp) / "audio.wav", normalize=normalize, denoise=denoise)
        transcript = transcribe(
            audio_path,
            language=lang,
            model_size=model,
            device=_device,
            word_timestamps=word_level,
            vad=vad,
            vad_threshold=_settings.vad_threshold,
            vad_min_silence_ms=_settings.vad_min_silence_ms,
            vad_speech_pad_ms=_settings.vad_speech_pad_ms,
            beam_size=beam_size,
            initial_prompt=prompt or _settings.initial_prompt,
            condition_on_previous_text=_settings.condition_on_previous_text,
            no_speech_threshold=_settings.no_speech_threshold,
            compression_ratio_threshold=_settings.compression_ratio_threshold,
            log_prob_threshold=_settings.log_prob_threshold,
            hallucination_silence_threshold=_settings.hallucination_silence_threshold,
            align=align or _settings.align,
            align_device=_settings.align_device,
        )

    if format == "srt":
        result = export_srt(transcript, out_path)
    elif format == "vtt":
        result = export_vtt(transcript, out_path)
    elif format == "json":
        result = export_json(transcript, out_path)

    typer.echo(f"Saved: {result}")
