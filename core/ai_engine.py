from dataclasses import dataclass
from typing import Optional

from core.conversation_manager import ConversationManager
from core.learning_engine import LearningEngine


@dataclass
class ProcessingResult:
    response_text: str
    confidence: float
    source: str
    context_used: bool = False


class AIEngine:
    def __init__(self):
        self.learning_engine = LearningEngine()
        self.conversation_manager = ConversationManager()

    async def handle_input(self, prompt: str) -> ProcessingResult:
        await self.conversation_manager.add_message(
            user_id="default",
            role="user",
            message=prompt,
        )

        learned = await self.learning_engine.check_learned(prompt)
        if learned:
            return ProcessingResult(
                response_text=learned["meaning"],
                confidence=1.0,
                source="learned",
            )

        return ProcessingResult(
            response_text=(
                f"I heard: '{prompt}'. "
                "You can teach me by saying: "
                "'Learn that X means Y.'"
            ),
            confidence=0.7,
            source="simple",
        )
