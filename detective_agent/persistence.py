import json
from pathlib import Path
from typing import Optional
from .models import Conversation

class FilePersistence:
    def __init__(self, directory: str = ".conversations"):
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True, parents=True)

    def _get_path(self, conversation_id: str) -> Path:
        return self.directory / f"{conversation_id}.json"

    def save(self, conversation: Conversation):
        path = self._get_path(conversation.id)
        with open(path, "w", encoding="utf-8") as f:
            f.write(conversation.model_dump_json(indent=2))

    def load(self, conversation_id: str) -> Optional[Conversation]:
        path = self._get_path(conversation_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return Conversation(**data)
    
    def list_conversations(self) -> list[str]:
        return [p.stem for p in self.directory.glob("*.json")]
