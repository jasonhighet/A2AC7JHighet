"""Unit tests for conversation persistence."""

import json
from unittest.mock import Mock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.utils.conversation_persistence import ConversationPersistence


@pytest.fixture
def mock_config():
    """Create a mock configuration object.

    Returns:
        Mock config with model settings
    """
    config = Mock()
    config.model_name = "claude-3-5-haiku-latest"
    config.temperature = 0.2
    config.max_tokens = 4096
    return config


@pytest.fixture
def temp_conversations_dir(tmp_path):
    """Create a temporary directory for conversations.

    Args:
        tmp_path: pytest temporary path fixture

    Returns:
        Path to temporary conversations directory
    """
    conversations_dir = tmp_path / "conversations"
    conversations_dir.mkdir()
    return conversations_dir


class TestConversationPersistence:
    """Test suite for ConversationPersistence class."""

    def test_initialization(self, temp_conversations_dir, mock_config):
        """Test that persistence initializes correctly."""
        system_prompt = "You are a helpful assistant."
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, system_prompt
        )

        assert persistence.conversation_id.startswith("conv_")
        assert "+00:00" in persistence.started_at or persistence.started_at.endswith(
            "Z"
        )
        assert persistence.conversations_dir == temp_conversations_dir
        assert persistence.system_prompt == system_prompt

    def test_conversation_id_format(self, temp_conversations_dir, mock_config):
        """Test that conversation ID has correct format."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "Test prompt"
        )

        # Format: conv_YYYYMMdd_HHmmss_xxxxx
        parts = persistence.conversation_id.split("_")
        assert len(parts) == 4
        assert parts[0] == "conv"
        assert len(parts[1]) == 8  # YYYYMMdd
        assert len(parts[2]) == 6  # HHmmss
        assert len(parts[3]) == 5  # random hash

    def test_conversation_id_uniqueness(self, temp_conversations_dir, mock_config):
        """Test that each conversation gets a unique ID."""
        persistence1 = ConversationPersistence(
            temp_conversations_dir, mock_config, "Test prompt"
        )
        persistence2 = ConversationPersistence(
            temp_conversations_dir, mock_config, "Test prompt"
        )

        assert persistence1.conversation_id != persistence2.conversation_id

    def test_save_simple_conversation(self, temp_conversations_dir, mock_config):
        """Test saving a simple conversation without tool calls."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "You are a helpful assistant."
        )

        messages = [
            HumanMessage(content="What is 2+2?"),
            AIMessage(content="2+2 equals 4."),
        ]

        filepath = persistence.save(messages)

        assert filepath.exists()
        assert filepath.suffix == ".json"
        assert filepath.name == f"{persistence.conversation_id}.json"

        # Verify content
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["messages"]) == 2
        assert data["messages"][0]["type"] == "human"
        assert data["messages"][0]["content"] == "What is 2+2?"
        assert data["messages"][1]["type"] == "ai"
        assert data["messages"][1]["content"] == "2+2 equals 4."

    def test_save_with_tool_calls(self, temp_conversations_dir, mock_config):
        """Test saving a conversation with tool calls."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "You are a helpful assistant."
        )

        # Simulate a conversation with tool calls
        messages = [
            HumanMessage(content="What features are available?"),
            AIMessage(
                content="Let me check that for you.",
                tool_calls=[
                    {
                        "id": "call_123",
                        "name": "get_jira_data",
                        "args": {},
                    }
                ],
            ),
            ToolMessage(
                content='[{"feature_id": "FEAT-001"}]',
                tool_call_id="call_123",
                name="get_jira_data",
            ),
            AIMessage(content="Here are the available features: FEAT-001"),
        ]

        filepath = persistence.save(messages)

        # Verify content
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["messages"]) == 4
        assert data["messages"][0]["type"] == "human"
        assert data["messages"][1]["type"] == "ai"
        assert "tool_calls" in data["messages"][1]
        assert len(data["messages"][1]["tool_calls"]) == 1
        assert data["messages"][2]["type"] == "tool"
        assert data["messages"][2]["tool_call_id"] == "call_123"
        assert data["messages"][2]["name"] == "get_jira_data"
        assert data["messages"][3]["type"] == "ai"
        assert (
            data["messages"][3]["content"]
            == "Here are the available features: FEAT-001"
        )

    def test_save_json_structure(self, temp_conversations_dir, mock_config):
        """Test that saved JSON has correct structure."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "You are a helpful assistant."
        )

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]

        filepath = persistence.save(messages)

        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

        # Check top-level structure
        assert "conversation_id" in data
        assert "started_at" in data
        assert "updated_at" in data
        assert "system_prompt" in data
        assert "metadata" in data
        assert "messages" in data

        # Check system prompt
        assert data["system_prompt"] == "You are a helpful assistant."

        # Check metadata
        assert data["metadata"]["model"] == "claude-3-5-haiku-latest"
        assert data["metadata"]["temperature"] == 0.2
        assert data["metadata"]["max_tokens"] == 4096

        # Check messages
        assert len(data["messages"]) == 2

    def test_save_incremental_updates(self, temp_conversations_dir, mock_config):
        """Test that save() can be called multiple times (incremental)."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "You are a helpful assistant."
        )

        # First save
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]
        filepath1 = persistence.save(messages)

        # Second save with more messages
        messages.extend(
            [
                HumanMessage(content="Goodbye"),
                AIMessage(content="See you later!"),
            ]
        )
        filepath2 = persistence.save(messages)

        # Should be same file
        assert filepath1 == filepath2

        # File should have all messages
        with open(filepath2, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["messages"]) == 4
        assert data["messages"][0]["content"] == "Hello"
        assert data["messages"][2]["content"] == "Goodbye"

    def test_get_filepath(self, temp_conversations_dir, mock_config):
        """Test getting the filepath without saving."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "Test prompt"
        )

        filepath = persistence.get_filepath()

        assert (
            filepath == temp_conversations_dir / f"{persistence.conversation_id}.json"
        )
        assert not filepath.exists()  # File not created until save()

    def test_json_formatting(self, temp_conversations_dir, mock_config):
        """Test that JSON is properly formatted (human-readable)."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "You are a helpful assistant."
        )

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
        ]

        filepath = persistence.save(messages)

        # Read raw file content
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        # Check for indentation (pretty-printed)
        assert "  " in content  # Has indentation
        assert "\n" in content  # Has newlines

        # Verify it's valid JSON
        json.loads(content)

    def test_message_to_dict(self, temp_conversations_dir, mock_config):
        """Test message to dict conversion."""
        persistence = ConversationPersistence(
            temp_conversations_dir, mock_config, "Test prompt"
        )

        # Test human message
        human_msg = HumanMessage(content="Hello")
        human_dict = persistence._message_to_dict(human_msg)
        assert human_dict["type"] == "human"
        assert human_dict["content"] == "Hello"

        # Test AI message with tool calls
        ai_msg = AIMessage(
            content="Let me help",
            tool_calls=[{"id": "1", "name": "test_tool", "args": {}}],
        )
        ai_dict = persistence._message_to_dict(ai_msg)
        assert ai_dict["type"] == "ai"
        assert ai_dict["content"] == "Let me help"
        assert "tool_calls" in ai_dict

        # Test tool message
        tool_msg = ToolMessage(content="result", tool_call_id="1", name="test_tool")
        tool_dict = persistence._message_to_dict(tool_msg)
        assert tool_dict["type"] == "tool"
        assert tool_dict["tool_call_id"] == "1"
        assert tool_dict["name"] == "test_tool"
