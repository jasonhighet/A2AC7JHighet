"""LangGraph workflow definition for the Investigator Agent.

This module creates the agent's graph-based workflow using LangGraph.
The workflow handles conversation flow and coordinates LLM interactions.
"""

from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.prompts import get_system_prompt
from src.agent.state import AgentState
from src.agent.memory import trim_messages, should_trim_messages
from src.tools.jira import get_jira_data
from src.tools.analysis import get_analysis
from src.tools.planning import (
    list_planning_docs,
    read_planning_doc,
    search_planning_docs,
)
from src.utils.config import Config


def create_agent_graph(config: Config):
    """Create and compile the Investigator Agent LangGraph workflow.

    This creates a workflow with tool integration:
    1. Receives user messages
    2. Calls the LLM (Claude) with system prompt and tools
    3. Routes to tools if the agent calls them
    4. Returns final response

    Args:
        config: Application configuration containing API keys and model settings

    Returns:
        The compiled LangGraph workflow ready for invocation
    """
    # Initialize the Claude model with configuration
    llm = ChatAnthropic(
        model=config.model_name,
        api_key=config.anthropic_api_key,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )

    # Bind tools to the LLM first
    # This enables the model to call tools when needed
    tools = [
        get_jira_data,
        get_analysis,
        list_planning_docs,
        read_planning_doc,
        search_planning_docs,
    ]
    llm_with_tools = llm.bind_tools(tools)

    # Add retry logic to the LLM+tools chain for transient API errors
    # This handles network issues, rate limits, and temporary service outages
    # Note: We apply retry AFTER binding tools so the entire LLM call (including tool use) is retryable
    llm_with_tools_and_retry = llm_with_tools.with_retry(
        retry_if_exception_type=(
            # Retry on network/API errors, not validation errors
            ConnectionError,
            TimeoutError,
            # Note: Anthropic SDK wraps API errors, but these are the base types
        ),
        wait_exponential_jitter=config.llm_retry_exponential_jitter,
        stop_after_attempt=config.llm_max_retry_attempts,
    )

    # Define the agent node function
    def call_model(state: AgentState) -> dict[str, list]:
        """Agent node that calls the LLM with conversation history.

        Args:
            state: Current agent state containing message history

        Returns:
            dict with updated messages list
        """
        messages = state["messages"]

        # Prepend system message if this is the first turn
        # (LangGraph will manage the accumulation)
        if not messages or not any(isinstance(m, SystemMessage) for m in messages):
            system_message = SystemMessage(content=get_system_prompt())
            messages = [system_message] + list(messages)

        # Trim messages if context is getting too large
        # This prevents context overflow when dealing with large planning documents
        if should_trim_messages(messages, token_threshold=50000):
            messages = trim_messages(messages, max_messages=20, keep_system=True)

        # Call the LLM with tools and retry logic
        response = llm_with_tools_and_retry.invoke(messages)

        # Return the new message to be added to state
        return {"messages": [response]}

    # Define conditional routing function
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine if we should route to tools or end the conversation.

        Args:
            state: Current agent state

        Returns:
            "tools" if the agent called a tool, "end" otherwise
        """
        messages = state["messages"]
        last_message = messages[-1]

        # If the last message has tool calls, route to tools node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # Otherwise, we're done
        return "end"

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add the agent node
    workflow.add_node("agent", call_model)

    # Add the tools node using LangGraph's ToolNode
    # This automatically handles tool execution
    workflow.add_node("tools", ToolNode(tools))

    # Set entry point
    workflow.set_entry_point("agent")

    # Add conditional edges from agent
    # If agent calls tools, go to tools node; otherwise end
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # After tools execute, go back to agent to process results
    workflow.add_edge("tools", "agent")

    # Compile and return the graph
    return workflow.compile()
