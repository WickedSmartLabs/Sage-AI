from dataclasses import dataclass
from core.conversation_manager import ConversationManager
from core.learning_engine import LearningEngine
from integrations.openai_client import OpenAIClient


@dataclass
class AIResult:
    response_text: str
    source: str
    confidence: float = 0.8


class AIEngine:
    """
    Central orchestration engine for Sage v2.
    """

    def __init__(self, settings: dict):
        self.settings = settings
        self.conversation = ConversationManager()
        self.learning = LearningEngine()
        self.llm = OpenAIClient()

    async def process_input(self, prompt: str, user_id: str = "default") -> AIResult:
        await self.conversation.add_message(user_id, "user", prompt)

        learned = await self.learning.check_learned(prompt)
        if learned:
            return AIResult(learned, "learned", 1.0)

        context = await self.conversation.get_context(user_id)
        reply = await self.llm.chat(prompt, context)

        await self.conversation.add_message(user_id, "assistant", reply)

        return AIResult(reply, "llm")
