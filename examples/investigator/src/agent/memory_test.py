"""Unit tests for memory management."""

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from src.agent.memory import trim_messages, estimate_token_count, should_trim_messages


class TestTrimMessages:
    """Tests for trim_messages function."""

    def test_trim_messages_under_limit(self):
        """Test that messages under limit are not trimmed."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
        ]

        result = trim_messages(messages, max_messages=20)

        assert len(result) == 3
        assert result == messages

    def test_trim_messages_over_limit(self):
        """Test that messages over limit are trimmed."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="Message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Message 2"),
            AIMessage(content="Response 2"),
            HumanMessage(content="Message 3"),
            AIMessage(content="Response 3"),
        ]

        result = trim_messages(messages, max_messages=4)

        # Should keep system message + 4 most recent
        assert len(result) == 5
        assert isinstance(result[0], SystemMessage)
        # Should have the last 4 messages
        assert result[1:] == messages[-4:]

    def test_trim_messages_preserves_system(self):
        """Test that system message is always preserved."""
        messages = [
            SystemMessage(content="System prompt"),
            HumanMessage(content="Message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Message 2"),
            AIMessage(content="Response 2"),
        ]

        result = trim_messages(messages, max_messages=2, keep_system=True)

        # Should keep system + 2 most recent
        assert len(result) == 3
        assert isinstance(result[0], SystemMessage)

    def test_trim_messages_no_system(self):
        """Test trimming when there's no system message."""
        messages = [
            HumanMessage(content="Message 1"),
            AIMessage(content="Response 1"),
            HumanMessage(content="Message 2"),
            AIMessage(content="Response 2"),
            HumanMessage(content="Message 3"),
        ]

        result = trim_messages(messages, max_messages=3)

        # Should keep only 3 most recent
        assert len(result) == 3
        assert result == messages[-3:]

    def test_trim_messages_exact_limit(self):
        """Test when message count equals limit."""
        messages = [
            SystemMessage(content="System"),
            HumanMessage(content="Hello"),
            AIMessage(content="Hi"),
        ]

        result = trim_messages(messages, max_messages=2)

        # System + 2 others = 3 total
        assert len(result) == 3


class TestEstimateTokenCount:
    """Tests for estimate_token_count function."""

    def test_estimate_token_count_single_message(self):
        """Test token estimation for a single message."""
        messages = [HumanMessage(content="Hello" * 100)]  # 500 characters

        tokens = estimate_token_count(messages)

        # ~500 chars / 4 = ~125 tokens
        assert 100 <= tokens <= 150

    def test_estimate_token_count_multiple_messages(self):
        """Test token estimation for multiple messages."""
        messages = [
            HumanMessage(content="a" * 400),  # ~100 tokens
            AIMessage(content="b" * 800),  # ~200 tokens
        ]

        tokens = estimate_token_count(messages)

        # ~1200 chars / 4 = ~300 tokens
        assert 250 <= tokens <= 350

    def test_estimate_token_count_empty_messages(self):
        """Test token estimation for empty messages."""
        messages = []

        tokens = estimate_token_count(messages)

        assert tokens == 0

    def test_estimate_token_count_with_system_message(self):
        """Test that system messages are counted."""
        messages = [
            SystemMessage(content="System prompt that is quite long" * 10),
            HumanMessage(content="User message"),
        ]

        tokens = estimate_token_count(messages)

        # Should count both messages
        assert tokens > 50


class TestShouldTrimMessages:
    """Tests for should_trim_messages function."""

    def test_should_trim_below_threshold(self):
        """Test that trimming is not recommended below threshold."""
        messages = [
            HumanMessage(content="Short message"),
        ]

        should_trim = should_trim_messages(messages, token_threshold=1000)

        assert should_trim is False

    def test_should_trim_above_threshold(self):
        """Test that trimming is recommended above threshold."""
        # Create a large message
        large_content = "a" * 100000  # ~25k tokens
        messages = [
            HumanMessage(content=large_content),
        ]

        should_trim = should_trim_messages(messages, token_threshold=10000)

        assert should_trim is True

    def test_should_trim_at_threshold(self):
        """Test behavior exactly at threshold."""
        # Create message with exactly threshold tokens
        content = "a" * 4000  # ~1000 tokens
        messages = [
            HumanMessage(content=content),
        ]

        should_trim = should_trim_messages(messages, token_threshold=1000)

        # At or below threshold should not trim
        assert should_trim is False


class TestMemoryIntegration:
    """Integration tests for memory management."""

    def test_trim_and_estimate_workflow(self):
        """Test the workflow of checking and trimming."""
        # Create many messages
        messages = [SystemMessage(content="System")]
        for i in range(30):
            messages.append(HumanMessage(content=f"Message {i}" * 10))  # type: ignore
            messages.append(AIMessage(content=f"Response {i}" * 10))  # type: ignore

        # Check if should trim
        if should_trim_messages(messages, token_threshold=500):
            trimmed = trim_messages(messages, max_messages=10)

            # Verify trimming reduced size
            assert len(trimmed) < len(messages)
            # System message should be preserved
            assert isinstance(trimmed[0], SystemMessage)

    def test_realistic_conversation(self):
        """Test with a realistic conversation pattern."""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="What is the capital of France?"),
            AIMessage(content="The capital of France is Paris."),
            HumanMessage(content="What about Germany?"),
            AIMessage(content="The capital of Germany is Berlin."),
            HumanMessage(content="And Italy?"),
            AIMessage(content="The capital of Italy is Rome."),
        ]

        # Estimate tokens
        tokens = estimate_token_count(messages)

        # Should be reasonable for this conversation
        assert tokens > 0
        assert tokens < 500  # These are short messages

        # Should not need trimming for small conversations
        assert not should_trim_messages(messages, token_threshold=10000)
