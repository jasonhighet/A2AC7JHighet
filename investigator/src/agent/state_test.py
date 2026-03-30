"""Unit tests for agent state schema."""

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.state import AgentState


def test_agent_state_is_typed_dict():
    """AgentState is a TypedDict with a messages key."""
    assert "messages" in AgentState.__annotations__


def test_agent_state_accepts_message_list():
    """AgentState can hold a list of messages."""
    state: AgentState = {"messages": [HumanMessage(content="Hello")]}
    assert len(state["messages"]) == 1


def test_agent_state_accepts_multiple_message_types():
    """AgentState works with both HumanMessage and AIMessage."""
    state: AgentState = {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
    }
    assert len(state["messages"]) == 2
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)


def test_agent_state_accepts_empty_messages():
    """AgentState accepts an empty messages list."""
    state: AgentState = {"messages": []}
    assert state["messages"] == []
