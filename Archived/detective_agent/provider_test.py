import pytest
import respx
import httpx
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

@pytest.mark.asyncio
async def test_llm_studio_provider_retries():
    provider = LLMStudioProvider()
    
    with respx.mock:
        # Mock 2 failures (503) followed by 1 success (200)
        respx.post("http://localhost:1234/v1/chat/completions").mock(
            side_effect=[
                Response(503),
                Response(503),
                Response(200, json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "Finally succeeded!"
                        }
                    }]
                })
            ]
        )
        
        messages = [Message(role="user", content="Retry test")]
        # This should succeed after 2 retries
        response = await provider.complete(messages, "test")
        
        assert response.content == "Finally succeeded!"
        assert len(respx.calls) == 3

@pytest.mark.asyncio
async def test_llm_studio_provider_max_retries():
    provider = LLMStudioProvider()
    
    with respx.mock:
        # Mock 4 failures (exceeds max 3 attempts)
        respx.post("http://localhost:1234/v1/chat/completions").mock(return_value=Response(503))
        
        messages = [Message(role="user", content="Fail test")]
        with pytest.raises(httpx.HTTPStatusError):
            await provider.complete(messages, "test")
        
        assert len(respx.calls) == 3
