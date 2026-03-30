"""Unit tests for system prompts."""

from src.agent.prompts import BASE_SYSTEM_PROMPT, FULL_SYSTEM_PROMPT, SYSTEM_PROMPT, get_system_prompt


def test_get_system_prompt_returns_string():
    """get_system_prompt returns a non-empty string."""
    prompt = get_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_get_system_prompt_default_is_base_prompt():
    """get_system_prompt default (no tools) returns the base prompt."""
    assert get_system_prompt() == BASE_SYSTEM_PROMPT
    assert get_system_prompt(with_tools=False) == BASE_SYSTEM_PROMPT


def test_get_system_prompt_with_tools_returns_full_prompt():
    """get_system_prompt(with_tools=True) returns the full tool-aware prompt."""
    assert get_system_prompt(with_tools=True) == FULL_SYSTEM_PROMPT


def test_system_prompt_alias_is_full_prompt():
    """SYSTEM_PROMPT constant is the full prompt (backward compatibility)."""
    assert SYSTEM_PROMPT == FULL_SYSTEM_PROMPT


def test_base_prompt_mentions_communityshare():
    """Base prompt identifies the platform context."""
    assert "CommunityShare" in BASE_SYSTEM_PROMPT


def test_base_prompt_mentions_pipeline_phases():
    """Base prompt explains the Dev → UAT → Production pipeline."""
    assert "Development" in BASE_SYSTEM_PROMPT
    assert "UAT" in BASE_SYSTEM_PROMPT
    assert "Production" in BASE_SYSTEM_PROMPT


def test_base_prompt_does_not_mention_tools():
    """Base prompt does NOT reference tool names (so Gemini won't try to call them)."""
    assert "get_jira_data" not in BASE_SYSTEM_PROMPT
    assert "get_analysis" not in BASE_SYSTEM_PROMPT


def test_full_prompt_mentions_tools():
    """Full prompt documents available tools."""
    assert "get_jira_data" in FULL_SYSTEM_PROMPT
    assert "get_analysis" in FULL_SYSTEM_PROMPT


def test_full_prompt_includes_guiding_principles():
    """Full prompt includes the guiding principles for step-by-step thinking."""
    assert "Guiding Principles" in FULL_SYSTEM_PROMPT
    assert "Think Step-by-Step" in FULL_SYSTEM_PROMPT


def test_full_prompt_includes_critical_rule():
    """Full prompt includes the critical failing-test rule."""
    assert "ANY failing tests" in FULL_SYSTEM_PROMPT
    assert "NOT READY" in FULL_SYSTEM_PROMPT


def test_full_prompt_includes_workflow():
    """Full prompt includes the explicit 6-step agent workflow."""
    assert "Workflow" in FULL_SYSTEM_PROMPT
    assert "State your plan" in FULL_SYSTEM_PROMPT


def test_base_prompt_asks_for_clarification():
    """Base prompt asks for more details on vague feature names."""
    assert "ask the user for more details" in BASE_SYSTEM_PROMPT
