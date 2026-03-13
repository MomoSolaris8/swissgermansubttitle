from __future__ import annotations

from pathlib import Path
from typing import List

from faster_whisper import WhisperModel

from swiss_subtitle_mvp.models import SubtitleSegment


def transcribe_audio(
    audio_path: Path,
    model_size: str,
    language: str,
    device: str,
    compute_type: str,
) -> List[SubtitleSegment]:
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    segments, _ = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        beam_size=5,
    )

    items: List[SubtitleSegment] = []
    for index, segment in enumerate(segments, start=1):
        text = segment.text.strip()
        if not text:
            continue
        items.append(
            SubtitleSegment(
                id=index,
                start_seconds=segment.start,
                end_seconds=segment.end,
                raw_text=text,
            )
        )
    if not items:
        raise RuntimeError("No transcript segments were produced")
    return items
