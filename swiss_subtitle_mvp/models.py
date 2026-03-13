from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class SubtitleSegment(BaseModel):
    id: int
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    raw_text: str
    normalized_text: Optional[str] = None
    standard_text: Optional[str] = None


class JobMetadata(BaseModel):
    job_id: str
    created_at: datetime
    input_url: str
    output_dir: Path
    title: Optional[str] = None
    whisper_model: str
    language: str
    raw_srt_path: Optional[Path] = None
    normalized_srt_path: Optional[Path] = None


class JobResult(BaseModel):
    metadata: JobMetadata
    segments: List[SubtitleSegment]
