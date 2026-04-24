"""
Sage Voice -- ElevenLabs TTS adapter.
Thin wrapper. Returns audio bytes. Nothing else.
"""
import logging
from elevenlabs.client import ElevenLabs
from config.settings import settings

logger = logging.getLogger(__name__)

_client = ElevenLabs(api_key=settings.elevenlabs_api_key)


def speak(text: str) -> bytes | None:
    """
    Convert text to audio bytes using ElevenLabs.
    Returns raw MP3 bytes or None on failure.
    """
    try:
        audio = _client.text_to_speech.convert(
            voice_id=settings.elevenlabs_voice_id,
            model_id="eleven_multilingual_v2",
            text=text,
        )
        return b"".join(audio)
    except Exception:
        logger.exception("TTS generation failed")
        return None