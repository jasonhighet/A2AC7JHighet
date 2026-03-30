"""Conversation persistence to filesystem for troubleshooting and analysis.

This module provides functionality to save agent conversations to disk in a
structured JSON format. Conversations are saved incrementally, making them
useful for troubleshooting, training, analysis, and evaluation.
"""

import hashlib
import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage


class ConversationPersistence:
    """Manages conversation persistence to filesystem.

    Saves conversations in simple JSON format with:
    - System prompt
    - Messages array (exactly as stored in LangGraph state)
    - Metadata for analysis
    """

    def __init__(self, conversations_dir: Path, config, system_prompt: str):
        """Initialize conversation persistence.

        Args:
            conversations_dir: Directory to save conversations
            config: Application config with model settings
            system_prompt: System prompt for the conversation
        """
        self.conversations_dir = Path(conversations_dir)
        self.conversations_dir.mkdir(exist_ok=True)

        self.conversation_id = self._generate_conversation_id()
        self.started_at = datetime.now(UTC).isoformat()

        self.config = config
        self.system_prompt = system_prompt

    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID with timestamp and random hash.

        Returns:
            Conversation ID in format: conv_YYYYMMdd_HHmmss_xxxxx
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_hash = hashlib.md5(str(random.random()).encode()).hexdigest()[:5]
        return f"conv_{timestamp}_{random_hash}"

    def _message_to_dict(self, message: BaseMessage) -> dict[str, Any]:
        """Convert a LangChain message to a dictionary.

        Args:
            message: LangChain message object

        Returns:
            Dictionary representation of the message
        """
        result: dict[str, Any] = {
            "type": message.type,
            "content": message.content,
        }

        # Add tool calls if present (for AI messages)
        if hasattr(message, "tool_calls") and message.tool_calls:
            result["tool_calls"] = message.tool_calls

        # Add tool call ID if present (for tool messages)
        if hasattr(message, "tool_call_id") and message.tool_call_id:
            result["tool_call_id"] = message.tool_call_id

        # Add tool name if present (for tool messages)
        if hasattr(message, "name") and message.name:
            result["name"] = message.name

        return result

    def save(self, messages: list[BaseMessage]) -> Path:
        """Save conversation to disk.

        Args:
            messages: List of messages from LangGraph state

        Returns:
            Path to saved conversation file
        """
        filepath = self.conversations_dir / f"{self.conversation_id}.json"

        conversation_data = {
            "conversation_id": self.conversation_id,
            "started_at": self.started_at,
            "updated_at": datetime.now(UTC).isoformat(),
            "system_prompt": self.system_prompt,
            "metadata": {
                "model": self.config.model_name,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            },
            "messages": [self._message_to_dict(msg) for msg in messages],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)

        return filepath

    def get_filepath(self) -> Path:
        """Get the filepath for this conversation.

        Returns:
            Path where conversation will be/is saved
        """
        return self.conversations_dir / f"{self.conversation_id}.json"
