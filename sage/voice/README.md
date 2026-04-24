# Voice -- Phase 8

This module will contain:
- Whisper STT adapter
- ElevenLabs TTS adapter
- Streaming response path
- Barge-in / interruption handling

## Key principle:

Voice is an interface layer, not core logic.
The assistant must work identically via text and voice.
Do not couple assistant.py to audio concerns.

## Laptop vs server note:

Audio device handling differs significantly between environments.
Use ELEVENLABS_VOICE_ID and audio device names from config/.env.
Never hardcode device names or file paths in voice adapters.

## Build order:

1. Get text + tools working well first (Phase 1-3)
2. Add Whisper STT as a thin wrapper around the /chat endpoint
3. Add ElevenLabs TTS as a post-processing step on response text
4. Add streaming response path to reduce perceived latency
5. Add barge-in support last (requires streaming STT + TTS interrupt)

## Latency budget:

Whisper (local): ~300-800ms
OpenAI GPT-4o (streaming): ~500-1500ms first token
ElevenLabs TTS: ~300-600ms
Total target: under 3s for a full voice turn
