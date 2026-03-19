from typing import List, Protocol, runtime_checkable
import httpx
from .models import Message

@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, messages: List[Message], system_prompt: str) -> Message:
        """Complete the conversation using the provided messages and system prompt."""
        ...

class LLMStudioProvider:
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "local-model"):
        self.base_url = base_url
        self.model = model

    async def complete(self, messages: List[Message], system_prompt: str) -> Message:
        async with httpx.AsyncClient() as client:
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                formatted_messages.append({"role": msg.role, "content": msg.content})
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": formatted_messages,
                    "temperature": 0.7,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return Message(role="assistant", content=content)
