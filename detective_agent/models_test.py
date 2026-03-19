from .models import Message, Conversation
from datetime import datetime
import uuid

def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"
    assert isinstance(msg.timestamp, datetime)

def test_conversation_creation():
    conv = Conversation(system_prompt="be helpful")
    assert conv.system_prompt == "be helpful"
    assert len(conv.messages) == 0
    assert isinstance(conv.id, str)
    assert len(conv.id) == 36

def test_message_serialization():
    msg = Message(role="user", content="test")
    data = msg.model_dump()
    assert data["role"] == "user"
    assert data["content"] == "test"
    
    new_msg = Message(**data)
    assert new_msg.role == msg.role
    assert new_msg.content == msg.content
