# Swiss Subtitle MVP

Swiss Subtitle MVP is a local CLI pipeline for turning Swiss German video audio into subtitle files with:

- raw ASR subtitles
- Zurich-style Swiss German normalized subtitles
- JSON artifacts for further analysis

The current focus is offline subtitle generation for Swiss German content. Live translation is out of scope for this MVP.

## Preview

The repository includes a 120-second preview rendered from a real run:

- Dual-subtitle video: [assets/preview/preview_120s_dual_subs.mp4](assets/preview/preview_120s_dual_subs.mp4)
- Dual-subtitle GIF preview: [assets/preview/preview_120s_dual_preview.gif](assets/preview/preview_120s_dual_preview.gif)
- Swiss German SRT: [assets/preview/zurich_preview_120s.srt](assets/preview/zurich_preview_120s.srt)
- Hochdeutsch SRT: [assets/preview/hochdeutsch_preview_120s.srt](assets/preview/hochdeutsch_preview_120s.srt)
- Combined dual-subtitle SRT: [assets/preview/zurich_hochdeutsch_preview_120s.srt](assets/preview/zurich_hochdeutsch_preview_120s.srt)

[![120-second dual-subtitle preview](assets/preview/preview_120s_dual_preview.gif)](assets/preview/preview_120s_dual_subs.mp4)

Click the GIF to open the full MP4 preview with Swiss German and Hochdeutsch subtitles.

Example subtitle pair:

```text
Swiss German: Das macht sich so einiges in de junge, dassi guet hie nöd bi.
Hochdeutsch: Das macht sich so einiges in den jungen Jahren, dass ich hier nicht gut dabei bin.
```

## What It Does

1. Download audio from a YouTube video with `yt-dlp`
2. Extract a mono 16 kHz WAV with `ffmpeg`
3. Transcribe Swiss German speech locally with `faster-whisper`
4. Normalize each subtitle segment into readable Zurich-style Swiss German with DeepSeek
5. Export `.srt` and `.json` outputs under `runs/<job_id>/`

Time alignment always comes from the ASR step. The LLM only rewrites subtitle text.

## Requirements

- Python 3.10+
- `ffmpeg`
- `yt-dlp`
- A DeepSeek API key

Recommended:

- Python 3.11
- A machine that can run `faster-whisper` efficiently

## Installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install yt-dlp
```

## Environment Variables

Do not commit API keys.

1. Copy the example file:

```bash
cp .env.example .env
```

2. Put your key into `.env`:

```dotenv
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

`.env` is ignored by git, and the CLI loads it automatically.

## Usage

Run the full pipeline:

```bash
python3 main.py run "https://www.youtube.com/watch?v=_qJdJTekb64"
```

If YouTube blocks the request, retry with browser cookies:

```bash
python3 main.py run "https://www.youtube.com/watch?v=_qJdJTekb64" --cookies-from-browser chrome
```

Normalize an existing run again:

```bash
python3 main.py resume-normalize runs/<job_id> --url "https://www.youtube.com/watch?v=_qJdJTekb64"
```

## Output Files

Each run writes files under `runs/<job_id>/`:

- `source.*`
- `audio.wav`
- `raw_segments.json`
- `normalized_segments.json`
- `raw_subtitle.srt`
- `zurich_subtitle.srt`
- `job.json`

## Current Limitations

- Swiss German accuracy is currently limited more by ASR quality than by token budget.
- Normalization improves readability, but it cannot fully recover meaning from a badly transcribed segment.
- The current implementation is optimized for local batch processing, not low-latency streaming.

## Repository Notes

- `.env` and runtime `runs/` outputs are excluded from git.
- The committed preview asset is stored under `assets/preview/` so the repository can show a polished example without leaking local runtime data.
