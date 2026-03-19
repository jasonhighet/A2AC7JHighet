import pytest
import respx
from httpx import Response
from .agent import DetectiveAgent
from .provider import LLMStudioProvider
from .persistence import FilePersistence
from .models import Message

@pytest.fixture
def mock_persistence(tmp_path):
    return FilePersistence(str(tmp_path))

@pytest.mark.asyncio
async def test_agent_default_system_prompt(mock_persistence):
    from .config import settings
    from .prompts import DEFAULT_SYSTEM_PROMPT
    provider = LLMStudioProvider()
    agent = DetectiveAgent(provider, mock_persistence)
    assert agent.system_prompt == DEFAULT_SYSTEM_PROMPT

@pytest.mark.asyncio
async def test_agent_send_message(mock_persistence):
    provider = LLMStudioProvider()
    agent = DetectiveAgent(provider, mock_persistence)
    
    with respx.mock:
        respx.post("http://localhost:1234/v1/chat/completions").mock(return_value=Response(200, json={
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": "I am an agent."
                }
            }]
        }))
        
        conversation = await agent.send_message("Who are you?")
        assert len(conversation.messages) == 2
        assert conversation.messages[0].content == "Who are you?"
        assert conversation.messages[1].content == "I am an agent."
        
        # Test persistence
        loaded = mock_persistence.load(conversation.id)
        assert loaded is not None
        assert len(loaded.messages) == 2

@pytest.mark.asyncio
async def test_agent_resume_conversation(mock_persistence):
    provider = LLMStudioProvider()
    agent = DetectiveAgent(provider, mock_persistence)
    
    # Save a conversation first
    conversation = await agent.send_message("First message")
    with respx.mock:
        respx.post("http://localhost:1234/v1/chat/completions").mock(return_value=Response(200, json={
            "choices": [{"message": {"role": "assistant", "content": "Second response"}}]
        }))
        
        # Resume it
        updated = await agent.send_message("Second message", conversation_id=conversation.id)
        assert len(updated.messages) == 4 # User1, Asst1, User2, Asst2
        assert updated.id == conversation.id
