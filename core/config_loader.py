from pathlib import Path
import os
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


def load_secrets() -> None:
    """
    Load secrets from config/secrets.env into environment variables.
    Safe for WSL, Docker, and local runs.
    """
    secrets_path = BASE_DIR / "config" / "secrets.env"

    if not secrets_path.exists():
        raise FileNotFoundError(
            f"Secrets file not found at {secrets_path}. "
            "Create config/secrets.env before running Sage."
        )

    load_dotenv(dotenv_path=secrets_path)

