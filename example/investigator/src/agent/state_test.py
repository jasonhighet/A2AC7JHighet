"""Unit tests for agent state definition."""

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph.message import add_messages

from src.agent.state import AgentState


def test_agent_state_structure():
    """Test that AgentState has the expected structure."""
    # Create a state instance
    state: AgentState = {"messages": []}

    # Verify the state has messages key
    assert "messages" in state
    assert isinstance(state["messages"], list)


def test_agent_state_with_messages():
    """Test that AgentState can hold messages."""
    # Create messages
    human_msg = HumanMessage(content="Hello")
    ai_msg = AIMessage(content="Hi there!")

    # Create state with messages
    state: AgentState = {"messages": [human_msg, ai_msg]}

    # Verify messages are stored
    assert len(state["messages"]) == 2
    assert state["messages"][0].content == "Hello"
    assert state["messages"][1].content == "Hi there!"

