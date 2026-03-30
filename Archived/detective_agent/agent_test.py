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
        
@pytest.mark.asyncio
async def test_agent_tool_loop(mock_persistence):
    provider = LLMStudioProvider()
    agent = DetectiveAgent(provider, mock_persistence)
    
    with respx.mock:
        # Mocking 3 turns: tool_call_1 -> tool_call_2 -> final_response
        respx.post("http://localhost:1234/v1/chat/completions").mock(
            side_effect=[
                Response(200, json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "get_release_summary", "arguments": "{\"release_id\": \"v2.1.0\"}"}
                            }]
                        }
                    }]
                }),
                Response(200, json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": "call_2",
                                "type": "function",
                                "function": {"name": "file_risk_report", "arguments": "{\"release_id\": \"v2.1.0\", \"severity\": \"HIGH\", \"findings\": [\"test failures\"]}"}
                            }]
                        }
                    }]
                }),
                Response(200, json={
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": "Risk assessment complete. I've filed a HIGH severity report for v2.1.0."
                        }
                    }]
                })
            ]
        )
        
        conversation = await agent.send_message("Analyze v2.1.0")
        
        # 0: User, 1: Asst(TC1), 2: Tool(R1), 3: Asst(TC2), 4: Tool(R2), 5: Asst(Final)
        assert len(conversation.messages) == 6
        assert conversation.messages[5].role == "assistant"
        assert "v2.1.0" in conversation.messages[5].content
