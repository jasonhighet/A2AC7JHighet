"""Unit tests for agent prompts."""

from src.agent.prompts import SYSTEM_PROMPT, get_system_prompt


def test_system_prompt_exists():
    """Test that SYSTEM_PROMPT constant is defined."""
    assert SYSTEM_PROMPT is not None
    assert isinstance(SYSTEM_PROMPT, str)
    assert len(SYSTEM_PROMPT) > 0


def test_system_prompt_contains_key_elements():
    """Test that system prompt contains essential information."""
    prompt = SYSTEM_PROMPT.lower()

    # Should mention the agent's role
    assert "investigator" in prompt

    # Should mention CommunityShare
    assert "communityshare" in prompt

    # Should mention feature readiness assessment
    assert "ready" in prompt or "readiness" in prompt

    # Should mention the development pipeline
    assert "development" in prompt or "uat" in prompt or "production" in prompt

    # Should mention data analysis
    assert "analyze" in prompt or "analysis" in prompt

    # Should mention providing recommendations
    assert "recommend" in prompt or "decision" in prompt


def test_get_system_prompt_function():
    """Test that get_system_prompt() returns the system prompt."""
    prompt = get_system_prompt()

    assert prompt is not None
    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert prompt == SYSTEM_PROMPT


def test_system_prompt_structure():
    """Test that system prompt has proper structure."""
    prompt = SYSTEM_PROMPT

    # Should have multiple lines/sections
    assert "\n" in prompt

    # Should not be excessively long (reasonable length)
    assert len(prompt) < 3000  # Less than 3000 characters (increased for tool guidance)

    # Should not have leading/trailing excessive whitespace
    assert prompt == prompt.strip() or prompt.startswith("You")


def test_system_prompt_mentions_workflow_steps():
    """Test that system prompt mentions the workflow steps."""
    prompt = SYSTEM_PROMPT

    # Should mention the steps the agent follows
    # Looking for numbered steps or workflow description
    assert "1." in prompt or "identify" in prompt.lower()
    assert "gather" in prompt.lower() or "data" in prompt.lower()
    assert "analyze" in prompt.lower()
    assert "recommend" in prompt.lower() or "provide" in prompt.lower()


def test_system_prompt_mentions_tools():
    """Test that system prompt mentions available tools (Step 2.3)."""
    prompt = SYSTEM_PROMPT

    # Should mention available tools
    assert "tools" in prompt.lower() or "tool" in prompt.lower()

    # Should specifically mention get_jira_data tool
    assert "get_jira_data" in prompt


def test_system_prompt_contains_workflow_guidance():
    """Test that system prompt contains workflow guidance for using tools."""
    prompt = SYSTEM_PROMPT

    # Should contain workflow section
    assert "workflow" in prompt.lower()

    # Should mention calling get_jira_data first
    assert "call get_jira_data" in prompt.lower()

    # Should mention feature_id extraction
    assert "feature_id" in prompt
