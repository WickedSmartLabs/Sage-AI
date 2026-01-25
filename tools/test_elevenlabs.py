#!/usr/bin/env python3
"""
ElevenLabs Text-to-Speech Diagnostic Tool

PURPOSE:
- Validate ElevenLabs configuration
- Test chosen voice
- Tune voice parameters
- Check API quota
- Measure streaming latency

NOT USED BY SAGE AT RUNTIME.
This is a developer verification tool only.

Place in: sage-v2/tools/test_elevenlabs.py
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from integrations/
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the SAME client Sage uses
try:
    from integrations.elevenlabs_client import ElevenLabsClient
except ImportError as e:
    print("❌ Could not import ElevenLabsClient")
    print(f"   Error: {e}")
    print("\nEnsure integrations/elevenlabs_client.py exists")
    print(f"Current directory: {Path.cwd()}")
    print(f"Looking for: {Path.cwd() / 'integrations' / 'elevenlabs_client.py'}")
    sys.exit(1)


def play_audio(path: Path):
    """
    Best-effort audio playback.
    Playback is OPTIONAL and not required for validation.
    """
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        elif sys.platform == "darwin":
            os.system(f"afplay '{path}'")
        else:
            # Linux - try common players
            for player in ("mpg123", "ffplay", "vlc", "mplayer"):
                if os.system(f"which {player} > /dev/null 2>&1") == 0:
                    os.system(f"{player} '{path}' > /dev/null 2>&1")
                    print(f"🔊 Playing with {player}")
                    return
            print(f"💾 Audio saved to {path}")
            print("   Install mpg123 to auto-play: sudo apt install mpg123")
    except Exception as e:
        print(f"💾 Audio saved to {path}")


def validate_environment():
    """
    Ensure required environment variables exist.
    """
    print("\n🔍 Validating environment...")
    
    missing = []
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")
    
    if not api_key:
        missing.append("ELEVENLABS_API_KEY")
    else:
        print(f"✅ API Key: {api_key[:8]}...")
    
    if not voice_id:
        missing.append("ELEVENLABS_VOICE_ID")
    else:
        print(f"✅ Voice ID: {voice_id}")
    
    if missing:
        print("\n❌ Missing environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nSet them in your shell or .env file:")
        print("  export ELEVENLABS_API_KEY='your-key'")
        print("  export ELEVENLABS_VOICE_ID='your-voice-id'")
        sys.exit(1)
    
    print("✅ Environment validated")


async def test_basic_tts(text: str):
    """
    Basic TTS sanity test.
    """
    print("\n" + "="*60)
    print("🧪 TESTING BASIC TTS")
    print("="*60)
    
    print(f"\n📝 Text: \"{text}\"")
    print(f"   ({len(text)} characters)")
    
    try:
        client = ElevenLabsClient()
        output = Path("tts_basic_test.mp3")
        
        print("\n🎙️  Generating audio...")
        audio = await client.speak(text, save_to=str(output))
        
        print(f"\n✅ Success!")
        print(f"   Audio size: {len(audio)/1024:.1f} KB")
        print(f"   Saved to: {output}")
        
        play_audio(output)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


async def test_streaming_tts(text: str):
    """
    Streaming TTS latency test.
    """
    print("\n" + "="*60)
    print("⚡ TESTING STREAMING TTS")
    print("="*60)
    
    print(f"\n📝 Text: \"{text}\"")
    print(f"   ({len(text)} characters)")
    
    try:
        client = ElevenLabsClient()
        chunks = []
        
        print("\n🎙️  Streaming audio...")
        async for chunk in client.stream(text):
            chunks.append(chunk)
            print(f"   Received chunk {len(chunks)} ({len(chunk)} bytes)")
        
        full_audio = b"".join(chunks)
        output = Path("tts_streaming_test.mp3")
        output.write_bytes(full_audio)
        
        print(f"\n✅ Streaming complete!")
        print(f"   Total chunks: {len(chunks)}")
        print(f"   Total size: {len(full_audio)/1024:.1f} KB")
        print(f"   Saved to: {output}")
        
        play_audio(output)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


async def check_quota():
    """
    Query ElevenLabs quota.
    """
    print("\n" + "="*60)
    print("📊 CHECKING API QUOTA")
    print("="*60)
    
    try:
        client = ElevenLabsClient()
        quota = await client.get_quota()
        
        print(f"\n✅ Quota Information:")
        print(f"   Used: {quota['used']:,} characters")
        print(f"   Limit: {quota['limit']:,} characters")
        print(f"   Remaining: {quota['remaining']:,} characters")
        print(f"   Usage: {quota['percent']}%")
        
        if quota['percent'] > 80:
            print("\n⚠️  WARNING: Over 80% quota used!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


async def tune_settings():
    """
    Test different voice settings to find best configuration.
    """
    print("\n" + "="*60)
    print("🎛️  VOICE SETTINGS TUNER")
    print("="*60)
    
    test_text = "Good morning, sir. This is a test of different voice settings."
    
    settings = [
        {
            "name": "Default (Balanced)",
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0
        },
        {
            "name": "High Stability",
            "stability": 0.75,
            "similarity_boost": 0.75,
            "style": 0.0
        },
        {
            "name": "More Expressive",
            "stability": 0.3,
            "similarity_boost": 0.75,
            "style": 0.5
        },
        {
            "name": "Maximum Clarity",
            "stability": 0.5,
            "similarity_boost": 0.9,
            "style": 0.0
        }
    ]
    
    try:
        for i, s in enumerate(settings, 1):
            print(f"\n[{i}/{len(settings)}] Testing: {s['name']}")
            print(f"   Stability: {s['stability']}")
            print(f"   Similarity: {s['similarity_boost']}")
            print(f"   Style: {s['style']}")
            
            client = ElevenLabsClient(
                stability=s['stability'],
                similarity_boost=s['similarity_boost'],
                style=s['style']
            )
            
            filename = Path(f"tune_{s['name'].lower().replace(' ', '_')}.mp3")
            audio = await client.speak(test_text, save_to=str(filename))
            
            print(f"   ✅ Generated: {filename}")
            print(f"      Size: {len(audio)/1024:.1f} KB")
            
            # Brief pause between tests
            await asyncio.sleep(0.5)
        
        print("\n✅ All settings tested!")
        print("   Listen to the files and update your client settings accordingly.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ElevenLabs TTS Diagnostic Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic test with default text
  python tools/test_elevenlabs.py
  
  # Test with custom text
  python tools/test_elevenlabs.py "Hello Sage, are you operational?"
  
  # Check API quota
  python tools/test_elevenlabs.py --quota
  
  # Test streaming (lower latency)
  python tools/test_elevenlabs.py --streaming
  
  # Tune voice settings
  python tools/test_elevenlabs.py --tune
        """
    )
    
    parser.add_argument(
        "text",
        nargs="?",
        default="Good morning, sir. ElevenLabs text to speech is operational.",
        help="Text to synthesize"
    )
    
    parser.add_argument(
        "--streaming",
        action="store_true",
        help="Test streaming TTS"
    )
    
    parser.add_argument(
        "--quota",
        action="store_true",
        help="Check API quota"
    )
    
    parser.add_argument(
        "--tune",
        action="store_true",
        help="Test different voice settings"
    )
    
    args = parser.parse_args()
    
    # Validate environment first
    validate_environment()
    
    # Run appropriate test
    if args.quota:
        success = asyncio.run(check_quota())
    elif args.tune:
        success = asyncio.run(tune_settings())
    elif args.streaming:
        success = asyncio.run(test_streaming_tts(args.text))
    else:
        success = asyncio.run(test_basic_tts(args.text))
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
