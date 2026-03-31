"""Tests for constants module to ensure consistency."""

from src.utils.constants import (
    ALL_TOOL_NAMES,
    TOOL_GET_ANALYSIS,
    TOOL_GET_JIRA_DATA,
    VALID_ANALYSIS_TYPES,
    VALID_DECISIONS,
)


def test_tool_names_are_strings():
    """Test that all tool names are strings."""
    for tool_name in ALL_TOOL_NAMES:
        assert isinstance(tool_name, str)
        assert len(tool_name) > 0


def test_tool_names_match_actual_tools():
    """Test that tool name constants match actual tool names."""
    # Import actual tools
    from src.tools.analysis import get_analysis
    from src.tools.jira import get_jira_data
    from src.tools.planning import (
        list_planning_docs,
        read_planning_doc,
        search_planning_docs,
    )

    # Check that constant names match actual tool names
    assert get_jira_data.name == TOOL_GET_JIRA_DATA
    assert get_analysis.name == TOOL_GET_ANALYSIS
    assert list_planning_docs.name == "list_planning_docs"
    assert read_planning_doc.name == "read_planning_doc"
    assert search_planning_docs.name == "search_planning_docs"


def test_analysis_types_are_valid():
    """Test that all analysis types follow the correct format."""
    for analysis_type in VALID_ANALYSIS_TYPES:
        assert isinstance(analysis_type, str)
        assert "/" in analysis_type
        # Should be either metrics/* or reviews/*
        assert analysis_type.startswith("metrics/") or analysis_type.startswith(
            "reviews/"
        )


def test_decision_types_are_lowercase():
    """Test that decision types are lowercase and non-empty."""
    for decision in VALID_DECISIONS:
        assert isinstance(decision, str)
        assert decision == decision.lower()
        assert len(decision) > 0
