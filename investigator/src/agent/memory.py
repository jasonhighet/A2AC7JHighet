"""Context management and summarisation logic for the Investigator Agent.

This module provides utilities for summarising conversation history to prevent
context window overflow while maintaining essential feature readiness context.
"""

import logging
from typing import List, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.utils.config import Config

logger = logging.getLogger(__name__)


def summarize_messages(
    llm: ChatOpenAI,
    messages: Sequence[BaseMessage],
    existing_summary: str = ""
) -> str:
    """Summarise the conversation history using the provided LLM.

    Args:
        llm: The language model to use for summarisation.
        messages: The sequence of messages to summarise.
        existing_summary: The previous summary to build upon.

    Returns:
        A concise summary of the conversation so far.
    """
    logger.info("Summarising conversation history...")
    
    if existing_summary:
        summary_prompt = (
            f"This is a summary of the conversation so far: {existing_summary}\n\n"
            "Extend the summary by incorporating the new messages below. "
            "Focus on feature IDs, metrics retrieved, and readiness conclusions. "
            "Keep the summary concise but comprehensive for a technical investigator."
        )
    else:
        summary_prompt = (
            "Summarise the following conversation about feature readiness. "
            "Focus on feature IDs, metrics retrieved (unit tests, coverage, security, etc.), "
            "and any conclusions or risks identified. "
            "Keep the summary concise but comprehensive for a technical investigator."
        )

    # Prepare messages for the summarisation call
    summarize_messages = [
        SystemMessage(content=summary_prompt),
        *messages
    ]
    
    response = llm.invoke(summarize_messages)
    return str(response.content)
