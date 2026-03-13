from __future__ import annotations

import sys
from pathlib import Path

import typer
from dotenv import load_dotenv

from swiss_subtitle_mvp.pipeline import normalize_existing_run, run_pipeline

app = typer.Typer(help="Swiss German video -> Zurich-style subtitle MVP")


def _ensure_supported_python() -> None:
    if sys.version_info >= (3, 10):
        return
    raise typer.BadParameter(
        "Python 3.10+ is required because yt-dlp no longer supports Python 3.9. "
        "Recreate the virtualenv with python3.11 -m venv .venv"
    )


def _load_environment() -> None:
    load_dotenv()


@app.command()
def run(
    url: str = typer.Argument(..., help="YouTube video URL"),
    runs_dir: Path = typer.Option(Path("runs"), help="Base directory for outputs"),
    whisper_model: str = typer.Option("tiny", help="faster-whisper model size"),
    language: str = typer.Option("de", help="Transcription language hint"),
    device: str = typer.Option("cpu", help="Whisper device, e.g. cpu or cuda"),
    compute_type: str = typer.Option("int8", help="Whisper compute type"),
    deepseek_model: str = typer.Option("deepseek-chat", help="DeepSeek model name"),
    cookies_from_browser: str = typer.Option(
        "",
        help="Browser name for yt-dlp cookies, e.g. chrome, safari, firefox",
    ),
) -> None:
    """Download, transcribe, normalize, and export subtitles."""
    _ensure_supported_python()
    _load_environment()
    result = run_pipeline(
        url=url,
        runs_dir=runs_dir,
        whisper_model=whisper_model,
        language=language,
        device=device,
        compute_type=compute_type,
        deepseek_model=deepseek_model,
        cookies_from_browser=cookies_from_browser or None,
    )
    typer.echo(f"Job: {result.metadata.job_id}")
    typer.echo(f"Output: {result.metadata.output_dir}")
    typer.echo(f"Raw SRT: {result.metadata.raw_srt_path}")
    typer.echo(f"Zurich SRT: {result.metadata.normalized_srt_path}")


@app.command()
def resume_normalize(
    job_dir: Path = typer.Argument(..., help="Existing run directory with raw_segments.json"),
    url: str = typer.Option("", help="Original YouTube URL for job metadata"),
    whisper_model: str = typer.Option("tiny", help="Whisper model used for the raw run"),
    language: str = typer.Option("de", help="Transcription language hint"),
    deepseek_model: str = typer.Option("deepseek-chat", help="DeepSeek model name"),
) -> None:
    """Normalize an existing raw_segments.json into Zurich-style subtitles."""
    _ensure_supported_python()
    _load_environment()
    result = normalize_existing_run(
        job_dir=job_dir,
        input_url=url,
        whisper_model=whisper_model,
        language=language,
        deepseek_model=deepseek_model,
    )
    typer.echo(f"Output: {result.metadata.output_dir}")
    typer.echo(f"Raw SRT: {result.metadata.raw_srt_path}")
    typer.echo(f"Zurich SRT: {result.metadata.normalized_srt_path}")
