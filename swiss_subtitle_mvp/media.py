from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def extract_wav(source_path: Path, output_path: Path) -> Path:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("Required binary not found on PATH: ffmpeg")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.strip()}")
    return output_path
