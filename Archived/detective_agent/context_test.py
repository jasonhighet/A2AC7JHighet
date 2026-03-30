import pytest
from .models import Message, Conversation
from .context import ContextManager

def test_token_counting():
    cm = ContextManager(max_tokens=200)
    system_prompt = "You are a helpful assistant."
    messages = [
        Message(role="user", content="Hello, how are you?"),
        Message(role="assistant", content="I am good, thank you!")
    ]
    
    tokens = cm.count_tokens(messages, system_prompt)
    assert tokens > 0
    # Basic check: longer content -> more tokens
    messages.append(Message(role="user", content="Tell me a very long story about a detective."))
    more_tokens = cm.count_tokens(messages, system_prompt)
    assert more_tokens > tokens

def test_truncation():
    # Set a small limit to force truncation
    cm = ContextManager(max_tokens=60) 
    system_prompt = "You are a helpful assistant."
    conversation = Conversation(
        system_prompt=system_prompt,
        messages=[
            Message(role="user", content="Msg 1 " * 10), # ~20-30 tokens
            Message(role="assistant", content="Msg 2 " * 10), # ~20-30 tokens
            Message(role="user", content="Msg 3 " * 10), # ~20-30 tokens
        ]
    )
    
    truncated = cm.get_truncated_messages(conversation)
    # The total should be within 60 tokens, including system prompt.
    # At least one message should be dropped.
    assert len(truncated) < len(conversation.messages)
    assert len(truncated) >= 1
    # Ensure Msg 3 is kept
    assert "Msg 3" in truncated[-1].content
