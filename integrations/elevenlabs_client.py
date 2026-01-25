"""
ElevenLabs Client
Used by Sage and developer diagnostic tools

Location: integrations/elevenlabs_client.py
"""

import os
import aiohttp
from pathlib import Path
from typing import AsyncIterator


class ElevenLabsClient:
    """
    Thin async wrapper around ElevenLabs TTS API
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        voice_id: str | None = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.0,
    ):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID")

        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY not set")

        if not self.voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID not set")

        self.voice_settings = {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": True,
        }

        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

    async def speak(self, text: str, save_to: str | None = None) -> bytes:
        """
        Convert text to speech and return MP3 bytes
        """
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}"

        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": self.voice_settings,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    raise RuntimeError(f"ElevenLabs error {resp.status}: {detail}")

                audio = await resp.read()

        if save_to:
            Path(save_to).write_bytes(audio)

        return audio

    async def stream(self, text: str) -> AsyncIterator[bytes]:
        """
        Streaming TTS (used later for low-latency voice)
        """
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}/stream"

        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": self.voice_settings,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as resp:
                if resp.status != 200:
                    detail = await resp.text()
                    raise RuntimeError(f"ElevenLabs stream error {resp.status}: {detail}")

                async for chunk in resp.content.iter_chunked(4096):
                    yield chunk

    async def get_quota(self) -> dict:
        """
        Fetch character usage quota
        """
        url = f"{self.BASE_URL}/user/subscription"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status != 200:
                    raise RuntimeError("Failed to fetch quota")

                data = await resp.json()

        used = data["character_count"]
        limit = data["character_limit"]

        return {
            "used": used,
            "limit": limit,
            "remaining": limit - used,
            "percent": round((used / limit) * 100, 2),
        }
