"""Unit tests for the agent graph workflow."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.graph import create_agent_graph
from src.agent.prompts import get_system_prompt
from src.utils.config import Config


@pytest.fixture
def mock_config() -> Config:
    """Create a mock configuration for testing."""
    config = MagicMock(spec=Config)
    config.model_name = "gemini-1.5-flash"
    config.gemini_api_key = "test-api-key"
    config.temperature = 0.0
    config.max_tokens = 4096
    config.llm_max_retry_attempts = 3
    config.llm_retry_exponential_jitter = True
    config.tool_max_retry_attempts = 3
    config.tool_retry_exponential_jitter = True
    return config


def test_create_agent_graph_returns_compiled_graph(mock_config):
    """create_agent_graph returns a compiled graph with an invoke method."""
    with patch("src.agent.graph.ChatOpenAI"):
        graph = create_agent_graph(mock_config)

    assert graph is not None
    assert hasattr(graph, "invoke")


def test_create_agent_graph_uses_gemini_base_url(mock_config):
    """create_agent_graph initialises ChatOpenAI with the Gemini base URL."""
    with patch("src.agent.graph.ChatOpenAI") as mock_chat:
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        mock_llm.with_retry.return_value = mock_llm

        create_agent_graph(mock_config)

        call_kwargs = mock_chat.call_args[1]
        assert "generativelanguage.googleapis.com" in call_kwargs["base_url"]


def test_create_agent_graph_passes_config_values(mock_config):
    """create_agent_graph passes model configuration correctly."""
    with patch("src.agent.graph.ChatOpenAI") as mock_chat:
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        # Ensure bind_tools is never called (tools list is empty in Step 1)
        mock_llm.with_retry.return_value = mock_llm

        create_agent_graph(mock_config)

        mock_chat.assert_called_once_with(
            model=mock_config.model_name,
            api_key=mock_config.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=mock_config.temperature,
            max_tokens=mock_config.max_tokens,
        )


def test_create_agent_graph_applies_retry(mock_config):
    """create_agent_graph applies with_retry to the LLM (no tools in Step 1)."""
    with patch("src.agent.graph.ChatOpenAI") as mock_chat:
        mock_llm = MagicMock()
        mock_llm_with_retry = MagicMock()

        mock_chat.return_value = mock_llm
        # In Step 1 tools list is empty so with_retry is applied directly to llm
        mock_llm.with_retry.return_value = mock_llm_with_retry

        create_agent_graph(mock_config)

        assert mock_llm.with_retry.called
        kwargs = mock_llm.with_retry.call_args[1]
        assert kwargs["stop_after_attempt"] == mock_config.llm_max_retry_attempts
        assert kwargs["wait_exponential_jitter"] == mock_config.llm_retry_exponential_jitter
        assert "retry_if_exception_type" in kwargs


def test_no_bind_tools_when_tool_list_empty(mock_config):
    """bind_tools is NOT called when the tools list is empty (avoids Gemini blank response)."""
    with patch("src.agent.graph.ChatOpenAI") as mock_chat:
        mock_llm = MagicMock()
        mock_chat.return_value = mock_llm
        mock_llm.with_retry.return_value = mock_llm

        create_agent_graph(mock_config)

        mock_llm.bind_tools.assert_not_called()


def test_call_model_prepends_system_message(mock_config):
    """Agent node prepends the system message when none exists in state."""
    mock_llm = MagicMock()
    mock_llm_with_retry = MagicMock()

    mock_response = AIMessage(content="I assess feature readiness")
    mock_response.tool_calls = []

    mock_llm.with_retry.return_value = mock_llm_with_retry
    mock_llm_with_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        graph.invoke({"messages": [HumanMessage(content="What do you do?")]})

    invoked_messages = mock_llm_with_retry.invoke.call_args[0][0]
    assert isinstance(invoked_messages[0], SystemMessage)
    # With no tools registered, graph uses BASE_SYSTEM_PROMPT (with_tools=False)
    from src.agent.prompts import BASE_SYSTEM_PROMPT
    assert BASE_SYSTEM_PROMPT in invoked_messages[0].content


def test_call_model_does_not_duplicate_system_message(mock_config):
    """Agent node does not prepend a second system message if one already exists."""
    mock_llm = MagicMock()
    mock_llm_with_retry = MagicMock()

    mock_response = AIMessage(content="Sure!")
    mock_response.tool_calls = []

    mock_llm.with_retry.return_value = mock_llm_with_retry
    mock_llm_with_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        graph.invoke({
            "messages": [
                SystemMessage(content="Existing system message"),
                HumanMessage(content="Hello"),
            ]
        })

    invoked_messages = mock_llm_with_retry.invoke.call_args[0][0]
    system_messages = [m for m in invoked_messages if isinstance(m, SystemMessage)]
    assert len(system_messages) == 1


def test_graph_routes_to_end_when_no_tool_calls(mock_config):
    """Graph ends correctly when agent returns no tool calls."""
    mock_llm = MagicMock()
    mock_llm_with_retry = MagicMock()

    mock_response = AIMessage(content="Here is my answer.")
    mock_response.tool_calls = []

    mock_llm.with_retry.return_value = mock_llm_with_retry
    mock_llm_with_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        result = graph.invoke({"messages": [HumanMessage(content="What do you do?")]})

    assert "messages" in result
    assert len(result["messages"]) > 0


def test_multiple_invocations_accumulate_messages(mock_config):
    """Consecutive invocations accumulate conversation history."""
    mock_llm = MagicMock()
    mock_llm_with_retry = MagicMock()

    resp1 = AIMessage(content="First response")
    resp1.tool_calls = []
    resp2 = AIMessage(content="Second response")
    resp2.tool_calls = []

    mock_llm.with_retry.return_value = mock_llm_with_retry
    mock_llm_with_retry.invoke.side_effect = [resp1, resp2]

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        state = graph.invoke({"messages": [HumanMessage(content="Turn one")]})
        state["messages"] = list(state["messages"]) + [HumanMessage(content="Turn two")]
        result = graph.invoke(state)

    # System + first human + first AI + second human + second AI = 5 minimum
    assert len(result["messages"]) >= 4
