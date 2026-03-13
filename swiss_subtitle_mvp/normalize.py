from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List
from urllib import error, request

from swiss_subtitle_mvp.models import SubtitleSegment

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"


def normalize_segments(
    segments: List[SubtitleSegment],
    model_name: str,
    api_key: str | None = None,
    batch_size: int = 8,
) -> List[SubtitleSegment]:
    key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY")

    normalized: List[SubtitleSegment] = []
    for batch in _chunked(segments, batch_size):
        normalized.extend(_rewrite_batch(batch, key, model_name))
    return normalized


def translate_segments_to_hochdeutsch(
    segments: List[SubtitleSegment],
    model_name: str,
    api_key: str | None = None,
    batch_size: int = 8,
) -> List[SubtitleSegment]:
    key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY")

    translated: List[SubtitleSegment] = []
    for batch in _chunked(segments, batch_size):
        translated.extend(_translate_batch(batch, key, model_name))
    return translated


def _rewrite_batch(
    batch: List[SubtitleSegment],
    api_key: str,
    model_name: str,
) -> List[SubtitleSegment]:
    system_prompt = (
        "You normalize Swiss German subtitle text into readable Zurich-style Swiss German. "
        "Preserve the original meaning, tone, and brevity. "
        "Do not translate into Hochdeutsch or Chinese. "
        "Keep the same number of items and the same ids. "
        "Return only valid JSON: "
        '[{"id": 1, "normalized_text": "..."}, {"id": 2, "normalized_text": "..."}].'
    )
    user_payload = [
        {"id": segment.id, "text": segment.raw_text}
        for segment in batch
    ]
    payload = {
        "model": model_name,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    }

    parsed = _call_deepseek(payload, api_key)
    try:
        content = parsed["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected DeepSeek response: {json.dumps(parsed)}") from exc

    try:
        items = json.loads(_strip_code_fences(content))
        normalized_by_id = {
            int(item["id"]): str(item["normalized_text"]).strip()
            for item in items
        }
        return [
            segment.model_copy(
                update={
                    "normalized_text": normalized_by_id.get(segment.id, "").strip()
                    or segment.raw_text
                }
            )
            for segment in batch
        ]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _rewrite_batch_fallback(batch, api_key, model_name)


def _rewrite_batch_fallback(
    batch: List[SubtitleSegment],
    api_key: str,
    model_name: str,
) -> List[SubtitleSegment]:
    normalized: List[SubtitleSegment] = []
    for segment in batch:
        payload = {
            "model": model_name,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Normalize Swiss German subtitle text into readable Zurich-style Swiss German. "
                        "Preserve meaning and brevity. Return only the normalized subtitle text."
                    ),
                },
                {"role": "user", "content": segment.raw_text},
            ],
        }
        parsed = _call_deepseek(payload, api_key)
        try:
            content = parsed["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected DeepSeek response: {json.dumps(parsed)}") from exc
        normalized.append(
            segment.model_copy(update={"normalized_text": content.strip() or segment.raw_text})
        )
    return normalized


def _translate_batch(
    batch: List[SubtitleSegment],
    api_key: str,
    model_name: str,
) -> List[SubtitleSegment]:
    system_prompt = (
        "You convert Swiss German subtitle text into natural Hochdeutsch subtitle text. "
        "Preserve meaning, tone, and brevity. "
        "Keep the same number of items and the same ids. "
        "Return only valid JSON: "
        '[{"id": 1, "standard_text": "..."}, {"id": 2, "standard_text": "..."}].'
    )
    user_payload = [
        {"id": segment.id, "text": segment.normalized_text or segment.raw_text}
        for segment in batch
    ]
    payload = {
        "model": model_name,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
        ],
    }

    parsed = _call_deepseek(payload, api_key)
    try:
        content = parsed["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected DeepSeek response: {json.dumps(parsed)}") from exc

    try:
        items = json.loads(_strip_code_fences(content))
        standard_by_id = {
            int(item["id"]): str(item["standard_text"]).strip()
            for item in items
        }
        return [
            segment.model_copy(
                update={
                    "standard_text": standard_by_id.get(segment.id, "").strip()
                    or segment.normalized_text
                    or segment.raw_text
                }
            )
            for segment in batch
        ]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return _translate_batch_fallback(batch, api_key, model_name)


def _translate_batch_fallback(
    batch: List[SubtitleSegment],
    api_key: str,
    model_name: str,
) -> List[SubtitleSegment]:
    translated: List[SubtitleSegment] = []
    for segment in batch:
        payload = {
            "model": model_name,
            "temperature": 0.1,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Convert Swiss German subtitle text into natural Hochdeutsch subtitle text. "
                        "Preserve meaning and brevity. Return only the Hochdeutsch subtitle text."
                    ),
                },
                {"role": "user", "content": segment.normalized_text or segment.raw_text},
            ],
        }
        parsed = _call_deepseek(payload, api_key)
        try:
            content = parsed["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected DeepSeek response: {json.dumps(parsed)}") from exc
        translated.append(
            segment.model_copy(
                update={
                    "standard_text": content.strip()
                    or segment.normalized_text
                    or segment.raw_text
                }
            )
        )
    return translated


def _call_deepseek(payload: dict, api_key: str) -> dict:
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        DEEPSEEK_API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=45) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"DeepSeek API error: {exc.code} {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"DeepSeek API unreachable: {exc}") from exc
    return json.loads(raw)


def _strip_code_fences(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _chunked(items: List[SubtitleSegment], size: int) -> List[List[SubtitleSegment]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def dump_segments_json(path: Path, segments: List[SubtitleSegment]) -> None:
    payload = [segment.model_dump(mode="json") for segment in segments]
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_segments_json(path: Path) -> List[SubtitleSegment]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [SubtitleSegment.model_validate(item) for item in payload]
