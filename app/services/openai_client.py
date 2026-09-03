from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class OpenAIError(Exception):
    pass


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.openai_api_key}",
    }


def _url(path: str) -> str:
    return f"{settings.openai_base_url.rstrip('/')}/{path.lstrip('/')}"


def chat(messages: list[dict[str, str]], *, temperature: float = 0.6) -> str:
    if not settings.has_openai:
        raise OpenAIError("missing_key")
    try:
        with httpx.Client(timeout=45.0) as client:
            res = client.post(
                _url("chat/completions"),
                headers={**_headers(), "Content-Type": "application/json"},
                json={
                    "model": settings.openai_chat_model,
                    "temperature": temperature,
                    "messages": messages,
                },
            )
            res.raise_for_status()
            data: dict[str, Any] = res.json()
            return data["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError:
        raise OpenAIError("http") from None
    except Exception as exc:
        raise OpenAIError(str(exc)) from exc


def transcribe(audio_bytes: bytes, filename: str, content_type: str) -> str:
    if not settings.has_openai:
        raise OpenAIError("missing_key")
    try:
        with httpx.Client(timeout=60.0) as client:
            res = client.post(
                _url("audio/transcriptions"),
                headers=_headers(),
                data={"model": settings.openai_stt_model, "language": "ja"},
                files={"file": (filename, audio_bytes, content_type or "application/octet-stream")},
            )
            res.raise_for_status()
            return (res.json().get("text") or "").strip()
    except httpx.HTTPStatusError:
        raise OpenAIError("http") from None
    except Exception as exc:
        raise OpenAIError(str(exc)) from exc


def speak(text: str) -> bytes:
    if not settings.has_openai:
        raise OpenAIError("missing_key")
    try:
        with httpx.Client(timeout=45.0) as client:
            res = client.post(
                _url("audio/speech"),
                headers={**_headers(), "Content-Type": "application/json"},
                json={
                    "model": settings.openai_tts_model,
                    "voice": settings.openai_tts_voice,
                    "input": text,
                },
            )
            res.raise_for_status()
            return res.content
    except httpx.HTTPStatusError:
        raise OpenAIError("http") from None
    except Exception as exc:
        raise OpenAIError(str(exc)) from exc
