import os
import httpx
from typing import List, Dict, Any


class OpenAIClient:
    """
    Thin wrapper around OpenAI Chat Completions.
    Keeps API logic out of the core engine.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def get_response(
        self,
        user_input: str,
        system_prompt: str = "",
        context: List[Dict[str, Any]] | None = None,
    ) -> str:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if context:
            messages.extend(context)

        messages.append({"role": "user", "content": user_input})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.6,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(self.base_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]
