"""Memory management for the Investigator Agent.

This module provides utilities for managing conversation context to prevent
context window overflow when dealing with large planning documents and
comprehensive data retrieval.
"""

import logging
from typing import List, Sequence
from langchain_core.messages import BaseMessage, SystemMessage

logger = logging.getLogger(__name__)


def trim_messages(
    messages: Sequence[BaseMessage], max_messages: int = 20, keep_system: bool = True
) -> List[BaseMessage]:
    """Trim message history to prevent context overflow.

    This implements a simple but effective strategy:
    - Always keep the system message (if present)
    - Keep the most recent N messages
    - Discard older messages to stay within limits

    Args:
        messages: Sequence of messages to trim
        max_messages: Maximum number of messages to keep (excluding system)
        keep_system: Whether to always keep the system message

    Returns:
        Trimmed list of messages

    Note: For Module 8, this provides a simple context management strategy.
    A production system might use more sophisticated summarization.
    """
    if len(messages) <= max_messages:
        return list(messages)

    # Find system message
    system_msg = None
    other_messages = []

    for msg in messages:
        if isinstance(msg, SystemMessage) and keep_system:
            system_msg = msg
        else:
            other_messages.append(msg)

    # Keep only the most recent messages
    recent_messages = other_messages[-max_messages:]

    # Reconstruct with system message first
    result: List[BaseMessage] = []
    if system_msg:
        logger.info(
            f"Trimmed messages from {len(messages)} to {len(recent_messages) + 1}"
        )
        result = [system_msg]
        result.extend(recent_messages)
    else:
        logger.info(f"Trimmed messages from {len(messages)} to {len(recent_messages)}")
        result = list(recent_messages)

    return result


def estimate_token_count(messages: Sequence[BaseMessage]) -> int:
    """Estimate token count for a sequence of messages.

    This is a rough estimate based on character count.
    4 characters ≈ 1 token (rough heuristic for English text)

    Args:
        messages: Sequence of messages

    Returns:
        Estimated token count
    """
    total_chars = 0

    for msg in messages:
        if hasattr(msg, "content"):
            total_chars += len(str(msg.content))
        if hasattr(msg, "tool_calls"):
            tool_calls = getattr(msg, "tool_calls", None)
            if tool_calls:
                # Tool calls add to context
                total_chars += int(len(str(tool_calls)) * 0.5)  # Rough estimate

    # Rough conversion: 4 characters per token
    estimated_tokens = int(total_chars // 4)

    return estimated_tokens


def should_trim_messages(
    messages: Sequence[BaseMessage], token_threshold: int = 50000
) -> bool:
    """Determine if messages should be trimmed based on estimated token count.

    Args:
        messages: Sequence of messages
        token_threshold: Token threshold to trigger trimming

    Returns:
        True if messages should be trimmed
    """
    estimated_tokens = estimate_token_count(messages)

    if estimated_tokens > token_threshold:
        logger.warning(
            f"Context size ({estimated_tokens} tokens) exceeds threshold "
            f"({token_threshold}). Trimming recommended."
        )
        return True

    return False
