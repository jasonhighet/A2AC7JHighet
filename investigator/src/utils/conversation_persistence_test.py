"""Unit tests for conversation history persistence."""

import json
from pathlib import Path

import pytest
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

from src.utils.config import Config
from src.utils.conversation_persistence import ConversationPersistence


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing."""
    config = Config(gemini_api_key="test-api-key")
    config.model_name = "gemini-1.5-flash"
    return config


@pytest.fixture
def persistence(tmp_path, mock_config):
    """Initialise persistence in a temporary directory."""
    return ConversationPersistence(
        directory=tmp_path,
        config=mock_config,
        system_prompt="Initial Prompt",
    )


def test_persistence_creates_directory(tmp_path, mock_config):
    """Initialising Persistence creates the target directory."""
    new_dir = tmp_path / "new_convs"
    assert not new_dir.exists()
    ConversationPersistence(new_dir, mock_config, "Prompt")
    assert new_dir.exists()


def test_persistence_generates_id(persistence):
    """Persistence generates a unique ID on initialisation."""
    id1 = persistence.conversation_id
    assert id1.startswith("conv_")
    assert len(id1) > 15


def test_persistence_saves_and_loads_messages(persistence):
    """Messages are correctly preserved across save and load calls."""
    messages = [
        SystemMessage(content="You are a helper."),
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there!"),
    ]

    persistence.save(messages)
    loaded_messages = persistence.load()

    assert len(loaded_messages) == 3
    assert isinstance(loaded_messages[0], SystemMessage)
    assert loaded_messages[0].content == "You are a helper."
    assert isinstance(loaded_messages[1], HumanMessage)
    assert loaded_messages[1].content == "Hello"
    assert isinstance(loaded_messages[2], AIMessage)
    assert loaded_messages[2].content == "Hi there!"


def test_persistence_handles_non_existent_file(persistence, tmp_path):
    """Loading from a non-existent file returns an empty list."""
    missing_file = tmp_path / "not_there.json"
    result = persistence.load(filepath=missing_file)
    assert result == []


def test_persistence_serialisation_format(persistence, tmp_path):
    """The saved JSON matches the expected structure."""
    messages = [HumanMessage(content="Test content")]
    persistence.save(messages)

    saved_file = persistence.get_filepath()
    with open(saved_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "conversation_id" in data
    assert "messages" in data
    assert len(data["messages"]) == 1
    assert data["messages"][0]["id"] == ["langchain", "schema", "messages", "HumanMessage"]
    assert data["messages"][0]["kwargs"]["content"] == "Test content"
