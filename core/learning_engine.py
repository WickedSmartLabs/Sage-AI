import json
from pathlib import Path
from rapidfuzz import fuzz


class LearningEngine:
    """
    Handles user-taught phrases and meanings.
    """

    def __init__(self, path: str = "data/learned_phrases.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    async def check_learned(self, text: str):
        learned = json.loads(self.path.read_text())
        text_lower = text.lower()

        for phrase, meaning in learned.items():
            score = fuzz.partial_ratio(text_lower, phrase.lower())
            if score >= 80:
                return meaning

        return None

    async def learn(self, phrase: str, meaning: str):
        learned = json.loads(self.path.read_text())
        learned[phrase] = meaning
        self.path.write_text(json.dumps(learned, indent=2))
