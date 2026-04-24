"""
Short-term conversation memory.
In-process for Phase 1. Replace with Redis or persistent store for production.
"""
from collections import defaultdict


# session_id -> list of message dicts
_sessions: dict[str, list[dict]] = defaultdict(list)

MAX_HISTORY = 20  # messages per session before trimming


def get_history(session_id: str) -> list[dict]:
    return _sessions[session_id]


def save_turn(session_id: str, user: str, assistant: str) -> None:
    history = _sessions[session_id]
    history.append({"role": "user", "content": user})
    history.append({"role": "assistant", "content": assistant})
    # Trim to keep context window manageable
    if len(history) > MAX_HISTORY:
        _sessions[session_id] = history[-MAX_HISTORY:]


def clear(session_id: str) -> None:
    _sessions.pop(session_id, None)
