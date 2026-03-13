from __future__ import annotations

from pathlib import Path
from typing import Iterable

from swiss_subtitle_mvp.models import SubtitleSegment


def _format_srt_timestamp(value: float) -> str:
    total_ms = int(round(value * 1000))
    hours = total_ms // 3_600_000
    minutes = (total_ms % 3_600_000) // 60_000
    seconds = (total_ms % 60_000) // 1000
    milliseconds = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def write_srt(path: Path, segments: Iterable[SubtitleSegment], field: str) -> None:
    blocks = []
    for segment in segments:
        text = getattr(segment, field, None)
        if not text:
            continue
        blocks.append(
            "\n".join(
                [
                    str(segment.id),
                    f"{_format_srt_timestamp(segment.start_seconds)} --> {_format_srt_timestamp(segment.end_seconds)}",
                    text.strip(),
                ]
            )
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def write_dual_srt(
    path: Path,
    segments: Iterable[SubtitleSegment],
    top_field: str,
    bottom_field: str,
) -> None:
    blocks = []
    for segment in segments:
        top_text = getattr(segment, top_field, None)
        bottom_text = getattr(segment, bottom_field, None)
        lines = [text.strip() for text in (top_text, bottom_text) if text]
        if not lines:
            continue
        blocks.append(
            "\n".join(
                [
                    str(segment.id),
                    f"{_format_srt_timestamp(segment.start_seconds)} --> {_format_srt_timestamp(segment.end_seconds)}",
                    "\n".join(lines),
                ]
            )
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")
