"""LangGraph workflow definition for the Investigator Agent.

This module creates the agent's graph-based workflow using LangGraph.
The agent uses Gemini 1.5 Flash via the OpenAI-compatible Google AI Studio
endpoint, accessed through langchain-openai's ChatOpenAI class.
"""

from typing import Literal

from opentelemetry import trace
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.memory import summarize_messages
from src.agent.prompts import get_system_prompt
from src.agent.state import AgentState
from src.tools.analysis import get_analysis
from src.tools.jira import get_jira_data
from src.tools.planning import list_planning_docs, read_planning_doc, search_planning_docs
from src.utils.config import Config

# The OpenAI-compatible base URL for Google AI Studio
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

tracer = trace.get_tracer(__name__)


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

    # Tools are registered here; Module 8 adds analysis and planning capabilities.
    tools: list = [
        get_jira_data,
        get_analysis,
        list_planning_docs,
        read_planning_doc,
        search_planning_docs,
    ]

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
        messages = list(state.get("messages", []))
        summary = state.get("summary", "")

        # Prepend system message with the existing summary if available.
        system_content = get_system_prompt(with_tools=bool(tools))
        if summary:
            system_content += f"\n\n**Conversation Summary so far:**\n{summary}"

        # Ensure system message is always at the start and up to date
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_content)] + list(messages)
        else:
            # Update existing system message if summary changed
            new_messages = []
            for m in messages:
                if isinstance(m, SystemMessage):
                    new_messages.append(SystemMessage(content=system_content))
                else:
                    new_messages.append(m)
            messages = new_messages

        response = llm_with_retry.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "summarize", "end"]:
        """Determine whether to route to tools, summarisation, or end.

        Args:
            state: Current agent state.

        Returns:
            "tools" for tool calls, "summarize" if history is long, "end" otherwise.
        """
        messages = state["messages"]
        last_message = messages[-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        
        # Trigger summarisation if we have more than 6 messages (3 turns)
        # and haven't just summarised.
        if len(messages) > 6:
            return "summarize"

        return "end"

    def summarize_conversation(state: AgentState) -> dict:
        """Summarise the existing messages and prune the history.

        Returns:
            Updated state with new summary and pruned messages.
        """
        # Summarise all but the last 2 messages (the most recent turn)
        messages = state["messages"]
        summary = state.get("summary", "")
        
        # We summarize messages that aren't the last 2 (keep immediate context)
        with tracer.start_as_current_span("summarize_conversation") as span:
            span.set_attribute("message_count", len(messages))
            new_summary = summarize_messages(llm, messages[:-2], summary)
            span.set_attribute("summary_length", len(new_summary))
            
            # Prune messages: keep the new summary and the last 2 messages
            # LangGraph's add_messages reducer will handle the update
            return {
                "summary": new_summary,
                "messages": messages[-2:] # This might need careful handling with add_messages
            }

    # Build the LangGraph workflow
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("summarize", summarize_conversation)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "summarize": "summarize",
            "end": END,
        },
    )

    # After tools execute, return control to the agent to process results
    workflow.add_edge("tools", "agent")
    
    # After summarisation, return to end (as we only summarize before ending a turn)
    # or return to agent? Usually summarize should lead to END so the next user
    # input starts with the new summary.
    workflow.add_edge("summarize", END)

    return workflow.compile()
