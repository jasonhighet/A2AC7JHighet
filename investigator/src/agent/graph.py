"""LangGraph workflow definition for the Investigator Agent.

This module creates the agent's graph-based workflow using LangGraph.
The agent uses Gemini 1.5 Flash via the OpenAI-compatible Google AI Studio
endpoint, accessed through langchain-openai's ChatOpenAI class.
"""

from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts import get_system_prompt
from src.agent.state import AgentState
from src.utils.config import Config

# The OpenAI-compatible base URL for Google AI Studio
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


def create_agent_graph(config: Config):
    """Create and compile the Investigator Agent LangGraph workflow.

    Builds a graph-based workflow that:
    1. Receives user messages
    2. Calls Gemini 1.5 Flash (via OpenAI-compatible endpoint) with tools bound
    3. Routes to tools if the agent requests them
    4. Returns to the agent node after tool execution
    5. Ends when the agent produces a final response

    Args:
        config: Application configuration containing API keys and model settings.

    Returns:
        The compiled LangGraph workflow ready for invocation.
    """
    # Initialise Gemini via the OpenAI-compatible endpoint using ChatOpenAI
    llm = ChatOpenAI(
        model=config.model_name,
        api_key=config.gemini_api_key,  # type: ignore[arg-type]
        base_url=GEMINI_BASE_URL,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    # Tools are registered here; Steps 2 and 3 will populate this list.
    # For Step 1 the list is empty so the agent responds conversationally.
    # NOTE: Gemini returns an empty content string when bind_tools([]) is called
    # with an empty list, so we only bind tools when there are tools to bind.
    tools: list = []

    llm_callable = llm.bind_tools(tools) if tools else llm

    # Add retry logic for transient API/network errors.
    # Applied AFTER binding tools so the entire LLM call (including tool use) is retryable.
    llm_with_retry = llm_callable.with_retry(
        retry_if_exception_type=(
            ConnectionError,
            TimeoutError,
        ),
        wait_exponential_jitter=config.llm_retry_exponential_jitter,
        stop_after_attempt=config.llm_max_retry_attempts,
    )

    def call_model(state: AgentState) -> dict[str, list]:
        """Agent node — calls the LLM with the full conversation history.

        Prepends the system message once on the first turn, then accumulates
        subsequent messages through LangGraph's add_messages reducer.

        Args:
            state: Current agent state containing message history.

        Returns:
            dict with updated messages list.
        """
        messages = list(state["messages"])

        # Prepend system message only if one hasn't been added yet.
        # Use the tool-aware version of the prompt if tools are registered.
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=get_system_prompt(with_tools=bool(tools)))] + messages

        response = llm_with_retry.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine whether to route to the tools node or end.

        Args:
            state: Current agent state.

        Returns:
            "tools" if the agent requested a tool call, "end" otherwise.
        """
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # Build the LangGraph workflow
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools execute, return control to the agent to process results
    workflow.add_edge("tools", "agent")

    return workflow.compile()
