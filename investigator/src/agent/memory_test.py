"""Unit tests for context management and summarisation."""

from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agent.memory import summarize_messages


def test_summarize_messages_initial():
    """summarize_messages creates an initial summary."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="This is a summary.")
    
    messages = [
        HumanMessage(content="Is FEAT-123 ready?"),
        AIMessage(content="Checking metrics...")
    ]
    
    summary = summarize_messages(mock_llm, messages)
    
    assert summary == "This is a summary."
    # Check that system prompt was passed
    args, kwargs = mock_llm.invoke.call_args
    assert isinstance(args[0][0], SystemMessage)
    assert "Summarise" in args[0][0].content


def test_summarize_messages_extend():
    """summarize_messages extends an existing summary."""
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="Extended summary.")
    
    existing_summary = "Initial summary."
    messages = [
        HumanMessage(content="What about security?"),
        AIMessage(content="Security is low risk.")
    ]
    
    summary = summarize_messages(mock_llm, messages, existing_summary)
    
    assert summary == "Extended summary."
    # Check that existing summary was passed in the prompt
    args, kwargs = mock_llm.invoke.call_args
    assert "Initial summary." in args[0][0].content
    assert "Extend" in args[0][0].content
