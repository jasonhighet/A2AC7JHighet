"""Conversation persistence for saving and loading message history.

This module provides the ConversationPersistence class that manages
storing conversation history as JSON files using a unique session ID.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Sequence

from langchain_core.load import dumpd, load
from langchain_core.messages import (
    BaseMessage,
)

from src.utils.config import Config

logger = logging.getLogger(__name__)


class ConversationPersistence:
    """Manage conversation history persistence on disk."""

    def __init__(self, directory: Path, config: Config, system_prompt: str):
        """Initialise the conversation persistence manager.

        Args:
            directory: Directory for storing conversation JSON files.
            config: Application configuration.
            system_prompt: Default system prompt for new conversations.
        """
        self.directory = directory
        self.config = config
        self.system_prompt = system_prompt
        self.conversation_id = self._generate_id()
        self.filepath = self.directory / f"{self.conversation_id}.json"

        # Create persistence directory if it doesn't exist
        self.directory.mkdir(parents=True, exist_ok=True)

    def _generate_id(self) -> str:
        """Generate a unique conversation ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_part = uuid.uuid4().hex[:5]
        return f"conv_{timestamp}_{unique_part}"

    def get_filepath(self) -> Path:
        """Return the current conversation's file path."""
        return self.filepath

    def save(self, messages: Sequence[BaseMessage], summary: str = "") -> None:
        """Save message history and summary to the conversation file.
        
        Args:
            messages: Sequence of LangChain BaseMessage objects.
            summary: Optional conversation summary string.
        """
        # Serialise messages to a list of dicts using LangChain's dumpd
        serialised = [dumpd(msg) for msg in messages]

        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "conversation_id": self.conversation_id,
                        "metadata": {
                            "updated_at": datetime.now().isoformat(),
                            "model": self.config.model_name,
                        },
                        "summary": summary,
                        "messages": serialised,
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
            logger.debug(f"Saved conversation to {self.filepath}")
        except OSError as e:
            logger.error(f"Failed to save conversation: {e}")

    def load(self, filepath: Path | None = None) -> List[BaseMessage]:
        """Load message history from a conversation file.

        Args:
            filepath: Optional path to an existing conversation file.
                      If None, tries to load the current session's file.

        Returns:
            Tuple of (List of BaseMessage objects, summary string).
        """
        target = filepath or self.filepath
        if not target.exists():
            return [], ""

        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)

            summary = data.get("summary", "")
            messages = []
            for item in data.get("messages", []):
                msg = load(item)
                if isinstance(msg, BaseMessage):
                    messages.append(msg)

            # Update state with loaded ID and path on success
            if filepath:
                self.conversation_id = data.get("conversation_id", self.conversation_id)
                self.filepath = filepath

            return messages, summary
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load conversation from {target}: {e}")
            return [], ""
