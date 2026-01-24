import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict


class ConversationManager:
    """
    Stores and retrieves conversation history using SQLite.
    """

    def __init__(self, db_path: str = "data/conversation_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                message TEXT,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    async def add_message(self, user_id: str, role: str, message: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO conversations VALUES (NULL, ?, ?, ?, ?)",
            (user_id, role, message, datetime.utcnow().isoformat())
        )

        conn.commit()
        conn.close()

    async def get_context(self, user_id: str, limit: int = 6) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT role, message FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )

        rows = cursor.fetchall()
        conn.close()

        return [
            {"role": role, "content": message}
            for role, message in reversed(rows)
        ]
