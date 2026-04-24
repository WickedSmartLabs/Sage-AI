"""
Sage API routes -- FastAPI.
Keep routes thin. Business logic lives in sage/core/assistant.py.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from sage.voice.tts import speak
from pydantic import BaseModel
from sage.core.assistant import chat
from sage.memory.conversation import get_history, save_turn, clear

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    response: str
    tool_used: str | None = None
    latency_ms: int
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    history = get_history(req.session_id)

    try:
        result = await chat(
            user_message=req.message,
            conversation_history=history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e

    save_turn(req.session_id, req.message, result["response"])

    return ChatResponse(
        response=result["response"],
        tool_used=result.get("tool_used"),
        latency_ms=result["latency_ms"],
        session_id=req.session_id,
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    clear(session_id)
    return {"status": "cleared", "session_id": session_id}


@router.get("/health")
async def health():
    return {"status": "ok", "sage": "online"}


@router.get("/memory/health")
async def memory_health():
    """Check which memory backend is active and whether it's reachable."""
    from sage.memory.manager import get_memory
    from config.settings import settings
    store = get_memory()
    reachable = await store.health()
    return {
        "backend": settings.sage_memory_backend,
        "reachable": reachable,
        "status": "ok" if reachable else "degraded",
    }

@router.post("/speak")
async def speak_endpoint(req: ChatRequest):
    """
    Same as /chat but returns MP3 audio of Sage's response.
    """
    history = get_history(req.session_id)

    try:
        result = await chat(
            user_message=req.message,
            conversation_history=history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    save_turn(req.session_id, req.message, result["response"])

    audio = speak(result["response"])
    if audio is None:
        raise HTTPException(status_code=500, detail="TTS generation failed")

    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={
            "X-Sage-Response": result["response"][:200],
            "X-Tool-Used": result.get("tool_used") or "",
            "X-Latency-Ms": str(result["latency_ms"]),
        },
    )