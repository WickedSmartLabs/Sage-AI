import json
from pathlib import Path
from typing import Dict, Optional


class LearningEngine:
    def __init__(self):
        self.file = Path("data/learned_phrases.json")
        self.file.parent.mkdir(exist_ok=True)
        self.learned = self._load()

    def _load(self) -> Dict[str, str]:
        if self.file.exists():
            return json.loads(self.file.read_text())
        return {}

    def _save(self):
        self.file.write_text(json.dumps(self.learned, indent=2))

    async def check_learned(self, phrase: str) -> Optional[Dict[str, str]]:
        key = phrase.lower().strip()
        if key in self.learned:
            return {"phrase": key, "meaning": self.learned[key]}
        return None

    async def learn(self, phrase: str, meaning: str):
        self.learned[phrase.lower().strip()] = meaning
        self._save()
