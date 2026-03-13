from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from swiss_subtitle_mvp.download import download_youtube_source
from swiss_subtitle_mvp.export_srt import write_srt
from swiss_subtitle_mvp.io_utils import build_job_dir, write_json
from swiss_subtitle_mvp.media import extract_wav
from swiss_subtitle_mvp.models import JobMetadata, JobResult
from swiss_subtitle_mvp.normalize import dump_segments_json, load_segments_json, normalize_segments
from swiss_subtitle_mvp.transcribe import transcribe_audio


def run_pipeline(
    url: str,
    runs_dir: Path,
    whisper_model: str,
    language: str,
    device: str,
    compute_type: str,
    deepseek_model: str,
    cookies_from_browser: Optional[str] = None,
    api_key: Optional[str] = None,
) -> JobResult:
    job_dir = build_job_dir(runs_dir, "youtube")
    source_path = download_youtube_source(url, job_dir, cookies_from_browser=cookies_from_browser)
    audio_path = extract_wav(source_path, job_dir / "audio.wav")

    raw_segments = transcribe_audio(
        audio_path=audio_path,
        model_size=whisper_model,
        language=language,
        device=device,
        compute_type=compute_type,
    )
    raw_json_path = job_dir / "raw_segments.json"
    dump_segments_json(raw_json_path, raw_segments)
    raw_srt_path = job_dir / "raw_subtitle.srt"
    write_srt(raw_srt_path, raw_segments, "raw_text")

    normalized_segments = normalize_segments(
        raw_segments,
        model_name=deepseek_model,
        api_key=api_key,
    )
    normalized_json_path = job_dir / "normalized_segments.json"
    dump_segments_json(normalized_json_path, normalized_segments)

    normalized_srt_path = job_dir / "zurich_subtitle.srt"
    write_srt(normalized_srt_path, normalized_segments, "normalized_text")

    metadata = JobMetadata(
        job_id=job_dir.name,
        created_at=datetime.utcnow(),
        input_url=url,
        output_dir=job_dir,
        title=source_path.stem,
        whisper_model=whisper_model,
        language=language,
        raw_srt_path=raw_srt_path,
        normalized_srt_path=normalized_srt_path,
    )
    write_json(job_dir / "job.json", metadata.model_dump(mode="json"))
    return JobResult(metadata=metadata, segments=normalized_segments)


def normalize_existing_run(
    job_dir: Path,
    input_url: str,
    whisper_model: str,
    language: str,
    deepseek_model: str,
    api_key: Optional[str] = None,
) -> JobResult:
    raw_json_path = job_dir / "raw_segments.json"
    if not raw_json_path.exists():
        raise RuntimeError(f"Missing raw segments file: {raw_json_path}")

    raw_segments = load_segments_json(raw_json_path)
    raw_srt_path = job_dir / "raw_subtitle.srt"
    if not raw_srt_path.exists():
        write_srt(raw_srt_path, raw_segments, "raw_text")

    normalized_segments = normalize_segments(
        raw_segments,
        model_name=deepseek_model,
        api_key=api_key,
    )
    normalized_json_path = job_dir / "normalized_segments.json"
    normalized_srt_path = job_dir / "zurich_subtitle.srt"
    dump_segments_json(normalized_json_path, normalized_segments)
    write_srt(normalized_srt_path, normalized_segments, "normalized_text")

    metadata = JobMetadata(
        job_id=job_dir.name,
        created_at=datetime.utcnow(),
        input_url=input_url,
        output_dir=job_dir,
        title=job_dir.name,
        whisper_model=whisper_model,
        language=language,
        raw_srt_path=raw_srt_path,
        normalized_srt_path=normalized_srt_path,
    )
    write_json(job_dir / "job.json", metadata.model_dump(mode="json"))
    return JobResult(metadata=metadata, segments=normalized_segments)
