"""Unit tests for the agent graph workflow."""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.graph import create_agent_graph
from src.agent.prompts import FULL_SYSTEM_PROMPT, get_system_prompt
from src.tools.analysis import get_analysis
from src.tools.jira import get_jira_data
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


@pytest.fixture
def setup_llm_mocks():
    """Helper to setup the LLM mock chain used in graph.py."""
    mock_llm = MagicMock()
    mock_llm_bound = MagicMock()
    mock_llm_retry = MagicMock()

    mock_llm.bind_tools.return_value = mock_llm_bound
    mock_llm_bound.with_retry.return_value = mock_llm_retry
    # Fallback for cases where bind_tools might not be called (though it is in Step 2)
    mock_llm.with_retry.return_value = mock_llm_retry

    return mock_llm, mock_llm_retry


def test_create_agent_graph_returns_compiled_graph(mock_config):
    """create_agent_graph returns a compiled graph with an invoke method."""
    with patch("src.agent.graph.ChatOpenAI"):
        graph = create_agent_graph(mock_config)

    assert graph is not None
    assert hasattr(graph, "invoke")


def test_create_agent_graph_uses_gemini_base_url(mock_config, setup_llm_mocks):
    """create_agent_graph initialises ChatOpenAI with the Gemini base URL."""
    mock_llm, _ = setup_llm_mocks
    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm) as mock_chat:
        create_agent_graph(mock_config)

        call_kwargs = mock_chat.call_args[1]
        assert "generativelanguage.googleapis.com" in call_kwargs["base_url"]


def test_create_agent_graph_passes_config_values(mock_config, setup_llm_mocks):
    """create_agent_graph passes model configuration correctly."""
    mock_llm, _ = setup_llm_mocks
    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm) as mock_chat:
        create_agent_graph(mock_config)

        mock_chat.assert_called_once_with(
            model=mock_config.model_name,
            api_key=mock_config.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=mock_config.temperature,
            max_tokens=mock_config.max_tokens,
        )


def test_create_agent_graph_binds_tools(mock_config, setup_llm_mocks):
    """create_agent_graph binds the required tools to the LLM."""
    mock_llm, _ = setup_llm_mocks
    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        create_agent_graph(mock_config)

        # In Step 3, tools list contains [get_jira_data, get_analysis]
        mock_llm.bind_tools.assert_called_once()
        bound_tools = mock_llm.bind_tools.call_args[0][0]
        assert get_jira_data in bound_tools
        assert get_analysis in bound_tools


def test_create_agent_graph_applies_retry(mock_config, setup_llm_mocks):
    """create_agent_graph applies with_retry to the tool-bound LLM."""
    mock_llm, _ = setup_llm_mocks
    mock_llm_bound = mock_llm.bind_tools.return_value

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        create_agent_graph(mock_config)

        assert mock_llm_bound.with_retry.called
        kwargs = mock_llm_bound.with_retry.call_args[1]
        assert kwargs["stop_after_attempt"] == mock_config.llm_max_retry_attempts
        assert kwargs["wait_exponential_jitter"] == mock_config.llm_retry_exponential_jitter


def test_call_model_prepends_full_system_message(mock_config, setup_llm_mocks):
    """Agent node prepends the FULL system prompt when tools are registered."""
    mock_llm, mock_llm_retry = setup_llm_mocks

    mock_response = AIMessage(content="I assess feature readiness")
    mock_llm_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        graph.invoke({"messages": [HumanMessage(content="What do you do?")]})

    invoked_messages = mock_llm_retry.invoke.call_args[0][0]
    assert isinstance(invoked_messages[0], SystemMessage)
    # With get_jira_data registered, graph uses FULL_SYSTEM_PROMPT (with_tools=True)
    assert FULL_SYSTEM_PROMPT in invoked_messages[0].content


def test_call_model_does_not_duplicate_system_message(mock_config, setup_llm_mocks):
    """Agent node does not prepend a second system message if one already exists."""
    mock_llm, mock_llm_retry = setup_llm_mocks

    mock_response = AIMessage(content="Sure!")
    mock_llm_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        graph.invoke({
            "messages": [
                SystemMessage(content="Existing system message"),
                HumanMessage(content="Hello"),
            ]
        })

    invoked_messages = mock_llm_retry.invoke.call_args[0][0]
    system_messages = [m for m in invoked_messages if isinstance(m, SystemMessage)]
    assert len(system_messages) == 1


def test_graph_routes_to_end_when_no_tool_calls(mock_config, setup_llm_mocks):
    """Graph ends correctly when agent returns no tool calls."""
    mock_llm, mock_llm_retry = setup_llm_mocks

    mock_response = AIMessage(content="Here is my answer.")
    mock_llm_retry.invoke.return_value = mock_response

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)
        result = graph.invoke({"messages": [HumanMessage(content="What do you do?")]})

    assert "messages" in result
    assert len(result["messages"]) > 0


def test_multiple_invocations_accumulate_messages(mock_config, setup_llm_mocks):
    """Consecutive invocations accumulate conversation history."""
    mock_llm, mock_llm_retry = setup_llm_mocks

    resp1 = AIMessage(content="First response")
    resp2 = AIMessage(content="Second response")

    mock_llm_retry.invoke.side_effect = [resp1, resp2]

    with patch("src.agent.graph.ChatOpenAI", return_value=mock_llm):
        graph = create_agent_graph(mock_config)

        state = graph.invoke({"messages": [HumanMessage(content="Turn one")]})
        # Add messages back to state as the reducer would
        state["messages"] = list(state["messages"]) + [HumanMessage(content="Turn two")]
        result = graph.invoke(state)

    # System + human1 + AI1 + human2 + AI2 = 5
    assert len(result["messages"]) >= 4
