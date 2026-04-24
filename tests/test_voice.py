from elevenlabs.client import ElevenLabs
from config.settings import settings

client = ElevenLabs(api_key=settings.elevenlabs_api_key)

audio = client.text_to_speech.convert(
    voice_id=settings.elevenlabs_voice_id,
    model_id="eleven_multilingual_v2",
    text="Good evening, sir. Sage voice systems are now online."
)

with open("sage_test_voice.mp3", "wb") as f:
    for chunk in audio:
        f.write(chunk)

print("Saved: sage_test_voice.mp3")