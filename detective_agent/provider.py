import json
from typing import List, Protocol, runtime_checkable, Optional, Any, Dict
import httpx
from .models import Message, ToolCall

@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, messages: List[Message], system_prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Message:
        """Complete the conversation using the provided messages and system prompt."""
        ...

class LLMStudioProvider:
    def __init__(self, base_url: str = "http://localhost:1234/v1", model: str = "local-model"):
        self.base_url = base_url
        self.model = model

    async def complete(self, messages: List[Message], system_prompt: str, tools: Optional[List[Dict[str, Any]]] = None) -> Message:
        async with httpx.AsyncClient() as client:
            formatted_messages = [{"role": "system", "content": system_prompt}]
            for msg in messages:
                m = {"role": msg.role, "content": msg.content}
                if msg.tool_calls:
                    m["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": json.dumps(tc.arguments) if not isinstance(tc.arguments, str) else tc.arguments
                            }
                        }
                        for tc in msg.tool_calls
                    ]
                if msg.tool_call_id:
                    m["tool_call_id"] = msg.tool_call_id
                formatted_messages.append(m)
            
            payload = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": 0.0,
            }
            if tools:
                payload["tools"] = tools
            
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]["message"]
            
            tool_calls = None
            if "tool_calls" in choice:
                tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                    )
                    for tc in choice["tool_calls"]
                ]
            
            return Message(
                role="assistant",
                content=choice.get("content"),
                tool_calls=tool_calls
            )
