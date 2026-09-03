from __future__ import annotations

import uuid
from pathlib import Path

from app.config import AUDIO_DIR, settings
from app.services.openai_client import OpenAIError, speak

PLACEHOLDER_URL = "/static/audio/placeholder.wav"


def audio_url(filename: str) -> str:
    return f"/media/audio/{filename}"


def save_bytes(data: bytes, suffix: str = ".mp3") -> str:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    (AUDIO_DIR / name).write_bytes(data)
    return name


def synthesize(text: str, cache_key: str | None = None) -> str:
    """Return a playable audio URL. Falls back to placeholder without a key."""
    text = (text or "").strip()
    if not text:
        return PLACEHOLDER_URL

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    if cache_key:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cache_key)
        cached = AUDIO_DIR / f"{safe}.mp3"
        if cached.exists() and cached.stat().st_size > 0:
            return audio_url(cached.name)

    if not settings.has_openai:
        return PLACEHOLDER_URL

    try:
        data = speak(text)
    except OpenAIError:
        return PLACEHOLDER_URL

    if cache_key:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cache_key)
        name = f"{safe}.mp3"
        (AUDIO_DIR / name).write_bytes(data)
        return audio_url(name)

    return audio_url(save_bytes(data))


def existing_cache(cache_key: str) -> Path | None:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in cache_key)
    path = AUDIO_DIR / f"{safe}.mp3"
    return path if path.exists() else None
