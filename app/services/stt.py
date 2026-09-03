from app.services.openai_client import OpenAIError, transcribe


def guess_filename(content_type: str) -> str:
    mapping = {
        "audio/webm": "speech.webm",
        "audio/mp4": "speech.mp4",
        "audio/mpeg": "speech.mp3",
        "audio/wav": "speech.wav",
        "audio/x-wav": "speech.wav",
        "audio/mp4;codecs=opus": "speech.mp4",
        "audio/webm;codecs=opus": "speech.webm",
    }
    if content_type in mapping:
        return mapping[content_type]
    if "mp4" in content_type:
        return "speech.mp4"
    if "wav" in content_type:
        return "speech.wav"
    if "mpeg" in content_type or "mp3" in content_type:
        return "speech.mp3"
    return "speech.webm"


def speech_to_text(audio_bytes: bytes, content_type: str = "") -> str | None:
    """Return transcript, empty string if unintelligible, or None if API unavailable."""
    if not audio_bytes:
        return ""
    try:
        return transcribe(audio_bytes, guess_filename(content_type), content_type)
    except OpenAIError:
        return None
