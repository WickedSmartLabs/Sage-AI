"""
Structured interaction logger.
Captures every request/response cycle from day one.
tool_success tri-state: True = succeeded, False = failed, None = no tool invoked.
"""
import json
import logging
import time
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_interaction_log = LOG_DIR / "interactions.jsonl"
_tool_log = LOG_DIR / "tool_calls.jsonl"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sage")


def log_interaction(
    user_message: str,
    assistant_response: str,
    latency_ms: int,
    tool_name: str | None = None,
    tool_success: bool | None = None,  # None = no tool invoked
    session_id: str = "default",
    extra: dict | None = None,
) -> None:
    """Append one structured record to interactions.jsonl."""
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": session_id,
        "user_message": user_message,
        "tool_used": tool_name,
        "tool_success": tool_success,  # null in JSON = no tool ran
        "assistant_response": assistant_response,
        "latency_ms": latency_ms,
        **(extra or {}),
    }
    with open(_interaction_log, "a") as f:
        f.write(json.dumps(record) + "\n")


def log_tool_call(
    tool_name: str,
    inputs: dict,
    output: str,
    success: bool,
    latency_ms: int,
) -> None:
    """Log a raw tool call separately for tool-level evals."""
    record = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tool": tool_name,
        "inputs": inputs,
        "output": output[:500],
        "success": success,
        "latency_ms": latency_ms,
    }
    with open(_tool_log, "a") as f:
        f.write(json.dumps(record) + "\n")
