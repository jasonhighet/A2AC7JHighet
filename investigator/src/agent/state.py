"""Agent state definition for LangGraph workflow.

This module defines the state schema used by the Investigator Agent's
LangGraph workflow. The state maintains conversation history using
LangChain's message types.
"""

from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema for the Investigator Agent workflow.

    Attributes:
        messages: Sequence of conversation messages with automatic accumulation.
                  The add_messages reducer handles message accumulation
                  and deduplication across graph invocations.
    """

    messages: Annotated[Sequence[BaseMessage], add_messages]
    summary: str
