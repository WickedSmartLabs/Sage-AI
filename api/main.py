from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.ai_engine import AIEngine

app = FastAPI(title="Sage v2 API", version="2.0")

engine = AIEngine()


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    response: str
    confidence: float
    source: str


@app.get("/")
async def root():
    return {"status": "online", "service": "Sage v2"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await engine.handle_input(request.message)
        return ChatResponse(
            response=result.response_text,
            confidence=result.confidence,
            source=result.source,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
