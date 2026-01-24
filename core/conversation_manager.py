from datetime import datetime
from typing import Dict, Any, Optional


class ConversationManager:
    def __init__(self):
        self.history = {}

    async def add_message(
        self,
        user_id: str,
        role: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.history.setdefault(user_id, []).append({
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat(),
        })
