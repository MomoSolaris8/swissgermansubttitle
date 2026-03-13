from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional


def ensure_binary(name: str) -> None:
    if shutil.which(name):
        return
    raise RuntimeError(f"Required binary not found on PATH: {name}")


def download_youtube_source(
    url: str,
    job_dir: Path,
    cookies_from_browser: Optional[str] = None,
) -> Path:
    ensure_binary("yt-dlp")
    output_template = str(job_dir / "source.%(ext)s")
    command = [
        "yt-dlp",
        "--no-playlist",
        "--format",
        "bestaudio/best",
        "-o",
        output_template,
    ]
    if cookies_from_browser:
        command.extend(["--cookies-from-browser", cookies_from_browser])
    command.append(url)
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        hint = ""
        if "HTTP Error 403" in stderr or "SABR" in stderr:
            hint = (
                " YouTube blocked the request. Retry with --cookies-from-browser "
                "using a logged-in browser profile, for example: --cookies-from-browser chrome."
            )
        raise RuntimeError(f"yt-dlp failed: {stderr}{hint}")

    matches = sorted(job_dir.glob("source.*"))
    if not matches:
        raise RuntimeError("yt-dlp finished but no source file was created")
    return matches[0]
