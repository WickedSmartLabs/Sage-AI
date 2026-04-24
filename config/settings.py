"""
Sage AI — Central settings loader.
All configuration comes from environment variables or .env file.
No hardcoded paths, no machine-specific assumptions.
"""
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # Mode
    sage_env: Literal["development", "production"] = "development"
    sage_log_level: str = "INFO"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"

    # ElevenLabs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Memory / Vector DB
    sage_memory_backend: Literal["chroma", "qdrant"] = "chroma"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_persist_dir: str = "./data/chroma"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Market Scanner
    scanner_base_url: str = "http://localhost:9000"
    scanner_api_key: str = ""

    # Docker
    docker_host: str = "unix:///var/run/docker.sock"

    # Home Assistant
    ha_base_url: str = ""
    ha_token: str = ""

    # Sage API
    sage_host: str = "0.0.0.0"
    sage_port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()