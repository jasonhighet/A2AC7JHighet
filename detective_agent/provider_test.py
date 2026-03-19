import pytest
import respx
from httpx import Response
from .provider import LLMStudioProvider
from .models import Message

@pytest.mark.asyncio
async def test_llm_studio_provider_complete():
    provider = LLMStudioProvider()
    
    with respx.mock:
        respx.post("http://localhost:1234/v1/chat/completions").mock(return_value=Response(200, json={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "Hello there!"
                }
            }]
        }))
        
        messages = [Message(role="user", content="Hi")]
        response = await provider.complete(messages, "system prompt")
        
        assert response.role == "assistant"
        assert response.content == "Hello there!"
