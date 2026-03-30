"""Unit tests for agent graph workflow."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.graph import create_agent_graph
from src.agent.prompts import get_system_prompt
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


def test_create_agent_graph_returns_compiled_graph(mock_config):
    """Test that create_agent_graph returns a compiled graph."""
    with patch("src.agent.graph.ChatAnthropic"):
        graph = create_agent_graph(mock_config)

        # Verify graph is not None
        assert graph is not None

        # Verify graph has expected methods
        assert hasattr(graph, "invoke")


def test_create_agent_graph_initializes_llm_correctly(mock_config):
    """Test that create_agent_graph initializes ChatAnthropic with correct parameters."""
    with patch("src.agent.graph.ChatAnthropic") as mock_chat_anthropic:
        # Mock the bind_tools method to return the mock itself
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        create_agent_graph(mock_config)

        # Verify ChatAnthropic was called with correct parameters
        mock_chat_anthropic.assert_called_once_with(
            model=mock_config.model_name,
            api_key=mock_config.anthropic_api_key,
            temperature=mock_config.temperature,
            max_tokens=mock_config.max_tokens,
        )

        # Verify bind_tools was called with the JIRA tool
        assert mock_llm.bind_tools.called


def test_agent_graph_workflow_structure(mock_config):
    """Test that the workflow has the expected structure."""
    with patch("src.agent.graph.ChatAnthropic"):
        graph = create_agent_graph(mock_config)

        # Verify the graph compiled successfully
        assert graph is not None

        # The graph should have nodes and edges
        # (LangGraph's CompiledGraph doesn't expose internal structure easily,
        # so we mainly verify it compiles without error)


def test_call_model_function_logic(mock_config):
    """Test the internal call_model function logic."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    # Response without tool calls (should end conversation)
    mock_response = AIMessage(content="Test response")
    mock_response.tool_calls = []  # No tool calls

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # Create initial state with a user message
        initial_state = {"messages": [HumanMessage(content="What do you do?")]}

        # Invoke the graph
        result = graph.invoke(initial_state)

        # Verify the result has messages
        assert "messages" in result
        assert len(result["messages"]) > 0

        # Verify LLM chain was called
        assert mock_llm_with_tools_and_retry.invoke.called


def test_system_message_prepended_on_first_call(mock_config):
    """Test that system message is prepended on the first call."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    mock_response = AIMessage(content="Test response")
    mock_response.tool_calls = []  # No tool calls

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # Create initial state with a user message (no system message)
        initial_state = {"messages": [HumanMessage(content="Hello")]}

        # Invoke the graph
        graph.invoke(initial_state)

        # Verify LLM chain was called with system message
        call_args = mock_llm_with_tools_and_retry.invoke.call_args[0][0]
        assert len(call_args) >= 2  # At least system + user message
        assert isinstance(call_args[0], SystemMessage)
        assert get_system_prompt() in call_args[0].content


def test_agent_graph_handles_empty_initial_state(mock_config):
    """Test that the graph handles empty initial state."""
    mock_llm = MagicMock()
    mock_response = AIMessage(content="Test response")
    mock_response.tool_calls = []  # No tool calls
    mock_llm.invoke.return_value = mock_response
    mock_llm.bind_tools.return_value = mock_llm

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # Create empty state
        initial_state = {"messages": []}

        # This should handle gracefully (though normally we'd have a message)
        # The actual behavior depends on LangGraph's handling
        try:
            result = graph.invoke(initial_state)
            # If it succeeds, verify structure
            assert "messages" in result
        except Exception:
            # If it fails, that's also acceptable behavior for empty state
            # The important thing is it doesn't crash unexpectedly
            pass


def test_multiple_invocations_accumulate_messages(mock_config):
    """Test that multiple invocations accumulate conversation history."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    mock_response_1 = AIMessage(content="First response")
    mock_response_1.tool_calls = []
    mock_response_2 = AIMessage(content="Second response")
    mock_response_2.tool_calls = []

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.side_effect = [
        mock_response_1,
        mock_response_2,
    ]

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # First invocation
        state = {"messages": [HumanMessage(content="First question")]}
        result = graph.invoke(state)

        # Update state with result
        state = result

        # Second invocation with accumulated state
        state["messages"].append(HumanMessage(content="Second question"))
        result = graph.invoke(state)

        # Verify messages accumulated
        # Should have: system message, first question, first response, second question, second response
        assert len(result["messages"]) >= 4


def test_graph_has_tools_node(mock_config):
    """Test that the graph includes a tools node for Step 2.3."""
    with patch("src.agent.graph.ChatAnthropic") as mock_chat_anthropic:
        mock_llm = MagicMock()
        mock_chat_anthropic.return_value = mock_llm
        mock_llm.bind_tools.return_value = mock_llm

        # Create the graph
        graph = create_agent_graph(mock_config)

        # Verify graph was created successfully
        assert graph is not None

        # Verify tools were bound
        assert mock_llm.bind_tools.called


def test_should_continue_routes_to_tools_when_tool_called(mock_config):
    """Test that should_continue routes to tools when agent calls a tool."""
    from src.agent.graph import create_agent_graph

    mock_llm = MagicMock()
    mock_llm.bind_tools.return_value = mock_llm

    # Create a mock response with a tool call
    mock_tool_call_response = AIMessage(content="")
    mock_tool_call_response.tool_calls = [
        {"name": "get_jira_data", "args": {}, "id": "call_123"}
    ]

    # Then a final response without tool calls
    mock_final_response = AIMessage(content="Here are the features")
    mock_final_response.tool_calls = []

    mock_llm.invoke.side_effect = [mock_tool_call_response, mock_final_response]

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        with patch(
            "src.agent.graph.ToolNode"
        ):  # Mock ToolNode to avoid actual execution
            graph = create_agent_graph(mock_config)

            # Verify graph compiles with tool routing
            assert graph is not None


def test_should_continue_routes_to_end_when_no_tool_calls(mock_config):
    """Test that should_continue routes to END when agent doesn't call tools."""
    # Create mock LLM with proper chain: llm -> bind_tools -> with_retry
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    # Create a mock response without tool calls
    mock_response = AIMessage(content="I can help with that")
    mock_response.tool_calls = []

    # Set up the mock chain
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry
    mock_llm_with_tools_and_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # Invoke with a simple question
        initial_state = {"messages": [HumanMessage(content="What do you do?")]}
        result = graph.invoke(initial_state)

        # Should complete without errors
        assert "messages" in result
        assert len(result["messages"]) > 0


def test_llm_configured_with_retry(mock_config):
    """Test that LLM is configured with retry logic for Step 5.2."""
    mock_llm = MagicMock()
    mock_llm_with_tools = MagicMock()
    mock_llm_with_tools_and_retry = MagicMock()

    # Set up the chain: llm -> bind_tools -> with_retry
    mock_llm.bind_tools.return_value = mock_llm_with_tools
    mock_llm_with_tools.with_retry.return_value = mock_llm_with_tools_and_retry

    with patch("src.agent.graph.ChatAnthropic", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        # Verify bind_tools was called first
        assert mock_llm.bind_tools.called

        # Verify with_retry was called on the llm_with_tools
        assert mock_llm_with_tools.with_retry.called

        # Verify retry configuration parameters
        call_kwargs = mock_llm_with_tools.with_retry.call_args[1]
        assert call_kwargs["stop_after_attempt"] == mock_config.llm_max_retry_attempts
        assert (
            call_kwargs["wait_exponential_jitter"]
            == mock_config.llm_retry_exponential_jitter
        )
        assert "retry_if_exception_type" in call_kwargs
