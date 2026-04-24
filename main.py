"""
Sage AI — Entry point.
Run with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import uvicorn
from fastapi import FastAPI
from sage.api.routes import router
from config.settings import settings

app = FastAPI(
    title="Sage AI",
    description="Unified Personal Assistant System",
    version="0.1.0",
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": "Sage",
        "version": "0.1.0",
        "status": "online",
        "tagline": "Polite. Efficient. Occasionally judgmental.",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.sage_host,
        port=settings.sage_port,
        reload=(settings.sage_env == "development"),
    )
