"""Integration tests for agent with tool calling.

These tests verify that the agent can successfully integrate with tools
to retrieve feature data and respond to user queries.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.agent.graph import create_agent_graph
from src.utils.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = MagicMock(spec=Config)
    config.model_name = "claude-sonnet-4-5"
    config.anthropic_api_key = "test-api-key"
    config.temperature = 0.0
    config.max_tokens = 4096
    config.llm_max_retry_attempts = 3
    config.llm_retry_exponential_jitter = True
    config.tool_max_retry_attempts = 3
    config.tool_retry_exponential_jitter = True
    return config


@pytest.fixture
def mock_jira_tool_response():
    """Mock response from get_jira_data tool."""
    return [
        {
            "folder": "feature1",
            "jira_key": "PLAT-1523",
            "feature_id": "FEAT-MS-001",
            "summary": "Maintenance Scheduling & Alert System",
            "status": "Production Ready",
            "data_quality": "MEDIUM",
        },
        {
            "folder": "feature2",
            "jira_key": "PLAT-1678",
            "feature_id": "FEAT-QR-002",
            "summary": "QR Code Check-in System",
            "status": "Development",
            "data_quality": "HIGH",
        },
    ]


def test_agent_calls_jira_tool_successfully(mock_config, mock_jira_tool_response):
    """Test that agent successfully calls get_jira_data tool."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    # First call: agent decides to use tool
    tool_call_response = AIMessage(content="Let me check the available features.")
    tool_call_response.tool_calls = [
        {"name": "get_jira_data", "args": {}, "id": "call_123"}
    ]

    # Second call: agent processes tool results
    final_response = AIMessage(
        content="I found 2 features: Maintenance Scheduling and QR Code Check-in."
    )
    final_response.tool_calls = []

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.side_effect = [
        tool_call_response,
        final_response,
    ]

    # Mock the actual tool execution
    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        with patch("src.tools.jira.get_jira_data") as mock_tool:
            mock_tool.invoke = MagicMock(return_value=mock_jira_tool_response)
            mock_tool.name = "get_jira_data"

            graph = create_agent_graph(mock_config)

            # User asks about features
            initial_state = {
                "messages": [HumanMessage(content="What features do you know about?")]
            }

            # Invoke the graph
            result = graph.invoke(initial_state)

            # Verify the workflow completed
            assert "messages" in result
            assert len(result["messages"]) > 1

            # Verify LLM chain was called multiple times (initial + after tool)
            assert mock_llm_with_tools_and_retry.invoke.call_count >= 2


def test_agent_workflow_with_tool_routing(mock_config, mock_jira_tool_response):
    """Test the complete workflow: agent -> tools -> agent."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry

    # Simulate agent calling tool
    tool_call_response = AIMessage(content="")
    tool_call_response.tool_calls = [
        {"name": "get_jira_data", "args": {}, "id": "call_456"}
    ]

    # Simulate agent processing tool result
    final_response = AIMessage(
        content="The maintenance scheduling feature is production ready."
    )
    final_response.tool_calls = []

    mock_llm_with_tools_and_retry.invoke.side_effect = [
        tool_call_response,
        final_response,
    ]

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        with patch("src.tools.jira.get_jira_data") as mock_tool:
            mock_tool.invoke = MagicMock(return_value=mock_jira_tool_response)
            mock_tool.name = "get_jira_data"

            graph = create_agent_graph(mock_config)

            initial_state = {
                "messages": [
                    HumanMessage(content="Is the maintenance scheduling feature ready?")
                ]
            }

            result = graph.invoke(initial_state)

            # Verify completion
            assert "messages" in result
            assert len(result["messages"]) > 0

            # Verify the last message is from the agent (not a tool)
            last_message = result["messages"][-1]
            assert isinstance(last_message, AIMessage)


def test_agent_handles_conversation_without_tools(mock_config):
    """Test that agent can respond without calling tools when appropriate."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    # Agent responds directly without calling tools
    direct_response = AIMessage(
        content="I help assess whether software features are ready to progress."
    )
    direct_response.tool_calls = []

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.return_value = direct_response

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        initial_state = {"messages": [HumanMessage(content="What do you do?")]}

        result = graph.invoke(initial_state)

        # Verify response without tool calls
        assert "messages" in result
        assert len(result["messages"]) > 0

        # Should only call LLM chain once (no tool loop)
        assert mock_llm_with_tools_and_retry.invoke.call_count == 1


def test_agent_maintains_conversation_context_with_tools(
    mock_config, mock_jira_tool_response
):
    """Test that conversation context is maintained across tool calls."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry

    # First interaction: call tool
    tool_call_response = AIMessage(content="")
    tool_call_response.tool_calls = [
        {"name": "get_jira_data", "args": {}, "id": "call_789"}
    ]

    # Second interaction: respond with tool results
    first_final_response = AIMessage(content="I found 2 features.")
    first_final_response.tool_calls = []

    # Third interaction: answer follow-up without tools
    second_response = AIMessage(
        content="The QR Code Check-in System is in Development."
    )
    second_response.tool_calls = []

    mock_llm_with_tools_and_retry.invoke.side_effect = [
        tool_call_response,
        first_final_response,
        second_response,
    ]

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        with patch("src.tools.jira.get_jira_data") as mock_tool:
            mock_tool.invoke = MagicMock(return_value=mock_jira_tool_response)
            mock_tool.name = "get_jira_data"

            graph = create_agent_graph(mock_config)

            # First question
            state = {"messages": [HumanMessage(content="What features are available?")]}
            result = graph.invoke(state)

            # Follow-up question using accumulated state
            state = result
            state["messages"].append(
                HumanMessage(content="What's the status of the QR system?")
            )
            result = graph.invoke(state)

            # Verify context was maintained
            assert "messages" in result
            # Should have: user msg 1, tool call, tool result, agent response, user msg 2, agent response
            assert len(result["messages"]) >= 4
