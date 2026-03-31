"""Unit tests for evaluation evaluator functions."""

from unittest.mock import Mock

from src.evaluation.evaluators import (
    _contains_failure_mentions,
    _contains_test_counts,
    _extract_agent_response,
    _extract_feature_from_run,
    _extract_tool_calls,
    _parse_decision_from_response,
    evaluate_decision_quality,
    evaluate_feature_identification,
    evaluate_tool_usage,
)


# ===== Helper Function Tests =====


def test_extract_feature_from_run_with_analysis_call():
    """Test extracting feature_id from get_analysis tool call."""
    # Create mock run with child runs
    child_run = Mock()
    child_run.name = "get_analysis"
    child_run.inputs = {"feature_id": "FEAT-MS-001", "analysis_type": "unit_test"}

    run = Mock()
    run.child_runs = [child_run]

    result = _extract_feature_from_run(run)
    assert result == "FEAT-MS-001"


def test_extract_feature_from_run_no_child_runs():
    """Test extracting feature_id when no child runs exist."""
    run = Mock()
    run.child_runs = []

    result = _extract_feature_from_run(run)
    assert result is None


def test_extract_feature_from_run_no_analysis_calls():
    """Test extracting feature_id when no get_analysis calls."""
    child_run = Mock()
    child_run.name = "get_jira_data"
    child_run.inputs = {}
    child_run.child_runs = []  # No nested children

    run = Mock()
    run.child_runs = [child_run]

    result = _extract_feature_from_run(run)
    assert result is None


def test_extract_feature_from_run_nested():
    """Test extracting feature_id from nested child runs (LangGraph structure)."""
    # Create nested structure: run -> agent_node -> tool_call -> get_analysis
    analysis_call = Mock()
    analysis_call.name = "get_analysis"
    analysis_call.inputs = {"feature_id": "FEAT-MS-001", "analysis_type": "unit_test"}
    analysis_call.child_runs = []

    tool_node = Mock()
    tool_node.name = "tools"
    tool_node.inputs = {}
    tool_node.child_runs = [analysis_call]

    agent_node = Mock()
    agent_node.name = "agent"
    agent_node.inputs = {}
    agent_node.child_runs = [tool_node]

    run = Mock()
    run.child_runs = [agent_node]

    result = _extract_feature_from_run(run)
    assert result == "FEAT-MS-001"


def test_extract_tool_calls():
    """Test extracting all tool calls from run."""
    # Create mock child runs
    jira_call = Mock()
    jira_call.run_type = "tool"
    jira_call.name = "get_jira_data"
    jira_call.inputs = {}
    jira_call.outputs = {"features": []}
    jira_call.child_runs = []  # No nested children

    analysis_call = Mock()
    analysis_call.run_type = "tool"
    analysis_call.name = "get_analysis"
    analysis_call.inputs = {"feature_id": "FEAT-MS-001", "analysis_type": "unit_test"}
    analysis_call.outputs = {"summary": {}}
    analysis_call.child_runs = []  # No nested children

    run = Mock()
    run.child_runs = [jira_call, analysis_call]

    result = _extract_tool_calls(run)

    assert len(result) == 2
    assert result[0]["name"] == "get_jira_data"
    assert result[1]["name"] == "get_analysis"
    assert result[1]["inputs"]["feature_id"] == "FEAT-MS-001"


def test_extract_tool_calls_nested():
    """Test extracting tool calls from nested runs (LangGraph structure)."""
    # Create nested structure: run -> agent_node -> tool_node -> tool_calls
    jira_call = Mock()
    jira_call.run_type = "tool"
    jira_call.name = "get_jira_data"
    jira_call.inputs = {}
    jira_call.outputs = {"features": []}
    jira_call.child_runs = []

    analysis_call = Mock()
    analysis_call.run_type = "tool"
    analysis_call.name = "get_analysis"
    analysis_call.inputs = {"feature_id": "FEAT-MS-001", "analysis_type": "unit_test"}
    analysis_call.outputs = {"summary": {}}
    analysis_call.child_runs = []

    tool_node = Mock()
    tool_node.run_type = "chain"
    tool_node.name = "tools"
    tool_node.inputs = {}
    tool_node.child_runs = [jira_call, analysis_call]

    agent_node = Mock()
    agent_node.run_type = "chain"
    agent_node.name = "agent"
    agent_node.inputs = {}
    agent_node.child_runs = [tool_node]

    run = Mock()
    run.child_runs = [agent_node]

    result = _extract_tool_calls(run)

    assert len(result) == 2
    assert result[0]["name"] == "get_jira_data"
    assert result[1]["name"] == "get_analysis"
    assert result[1]["inputs"]["feature_id"] == "FEAT-MS-001"


def test_extract_agent_response_from_dict():
    """Test extracting agent response from outputs dict."""
    run = Mock()
    run.outputs = {"output": "The feature is ready!"}

    result = _extract_agent_response(run)
    assert result == "The feature is ready!"


def test_extract_agent_response_from_string():
    """Test extracting agent response when outputs is a string."""
    run = Mock()
    run.outputs = "The feature is ready!"

    result = _extract_agent_response(run)
    assert result == "The feature is ready!"


def test_extract_agent_response_no_outputs():
    """Test extracting agent response when no outputs."""
    run = Mock()
    run.outputs = {}

    result = _extract_agent_response(run)
    assert result == ""


def test_parse_decision_ready():
    """Test parsing 'ready' decision from response."""
    responses = [
        "The feature is ready for production.",
        "✅ Ready to proceed",
        "This feature is ready!",
    ]

    for response in responses:
        result = _parse_decision_from_response(response)
        assert result == "ready", f"Failed for: {response}"


def test_parse_decision_not_ready():
    """Test parsing 'not_ready' decision from response."""
    responses = [
        "The feature is not ready",
        "❌ Not ready due to failing tests",
        "This feature isn't ready for production",
    ]

    for response in responses:
        result = _parse_decision_from_response(response)
        assert result == "not_ready", f"Failed for: {response}"


def test_parse_decision_needs_info():
    """Test parsing 'needs_info' decision from response."""
    responses = [
        "I need more information to assess readiness",
        "Need clarification about which feature",
        "I'm not sure which feature you're referring to",
    ]

    for response in responses:
        result = _parse_decision_from_response(response)
        assert result == "needs_info", f"Failed for: {response}"


def test_parse_decision_unknown():
    """Test parsing decision when unclear."""
    response = "Here's some information about the feature."

    result = _parse_decision_from_response(response)
    assert result == "unknown"


def test_contains_test_counts():
    """Test detecting test count mentions in text."""
    texts_with_counts = [
        "Found 3 tests failing",
        "487 tests passed",
        "Total: 42 unit tests",
        "2 failures detected",
    ]

    for text in texts_with_counts:
        result = _contains_test_counts(text)
        assert result is True, f"Failed for: {text}"


def test_contains_test_counts_no_counts():
    """Test when no test counts in text."""
    texts_without_counts = [
        "The tests are failing",
        "Some issues were found",
        "No problems detected",
    ]

    for text in texts_without_counts:
        result = _contains_test_counts(text)
        assert result is False, f"Failed for: {text}"


def test_contains_failure_mentions():
    """Test detecting failure mentions in text."""
    texts_with_failures = [
        "3 tests are failing",
        "Test failed due to timeout",
        "Multiple failures detected",
        "The test fails intermittently",
    ]

    for text in texts_with_failures:
        result = _contains_failure_mentions(text)
        assert result is True, f"Failed for: {text}"


def test_contains_failure_mentions_no_failures():
    """Test when no failure mentions in text."""
    texts_without_failures = [
        "All tests passed",
        "Coverage is at 85%",
        "Ready for production",
    ]

    for text in texts_without_failures:
        result = _contains_failure_mentions(text)
        assert result is False, f"Failed for: {text}"


# ===== Evaluator Tests =====


def test_evaluate_feature_identification_correct():
    """Test feature identification evaluator with correct feature."""
    # Create mock run
    child_run = Mock()
    child_run.name = "get_analysis"
    child_run.inputs = {"feature_id": "FEAT-MS-001"}

    run = Mock()
    run.child_runs = [child_run]

    # Create mock example
    example = Mock()
    example.outputs = {"expected_feature_id": "FEAT-MS-001"}

    result = evaluate_feature_identification(run, example)

    assert result["key"] == "feature_identification"
    assert result["score"] == 1.0
    assert "FEAT-MS-001" in result["comment"]


def test_evaluate_feature_identification_incorrect():
    """Test feature identification evaluator with wrong feature."""
    # Create mock run
    child_run = Mock()
    child_run.name = "get_analysis"
    child_run.inputs = {"feature_id": "FEAT-QR-002"}

    run = Mock()
    run.child_runs = [child_run]

    # Create mock example
    example = Mock()
    example.outputs = {"expected_feature_id": "FEAT-MS-001"}

    result = evaluate_feature_identification(run, example)

    assert result["key"] == "feature_identification"
    assert result["score"] == 0.0


def test_evaluate_feature_identification_not_evaluated():
    """Test feature identification evaluator when not required."""
    run = Mock()
    run.child_runs = []

    example = Mock()
    example.outputs = {}  # No expected_feature_id

    result = evaluate_feature_identification(run, example)

    assert result["key"] == "feature_identification"
    assert result["score"] is None


def test_evaluate_tool_usage_all_correct():
    """Test tool usage evaluator when all tools called correctly."""
    # Create mock tool calls
    jira_call = Mock()
    jira_call.run_type = "tool"
    jira_call.name = "get_jira_data"
    jira_call.inputs = {}
    jira_call.outputs = {}
    jira_call.child_runs = []  # No nested children

    analysis_call1 = Mock()
    analysis_call1.run_type = "tool"
    analysis_call1.name = "get_analysis"
    analysis_call1.inputs = {
        "feature_id": "FEAT-MS-001",
        "analysis_type": "metrics/unit_test_results",
    }
    analysis_call1.outputs = {}
    analysis_call1.child_runs = []  # No nested children

    analysis_call2 = Mock()
    analysis_call2.run_type = "tool"
    analysis_call2.name = "get_analysis"
    analysis_call2.inputs = {
        "feature_id": "FEAT-MS-001",
        "analysis_type": "metrics/test_coverage_report",
    }
    analysis_call2.outputs = {}
    analysis_call2.child_runs = []  # No nested children

    run = Mock()
    run.child_runs = [jira_call, analysis_call1, analysis_call2]

    # Create mock example
    example = Mock()
    example.outputs = {
        "should_call_jira": True,
        "should_call_analysis": True,
        "analysis_types_required": [
            "metrics/unit_test_results",
            "metrics/test_coverage_report",
        ],
    }

    result = evaluate_tool_usage(run, example)

    assert result["key"] == "tool_usage"
    assert result["score"] == 1.0


def test_evaluate_tool_usage_missing_jira():
    """Test tool usage evaluator when JIRA call missing."""
    run = Mock()
    run.child_runs = []

    example = Mock()
    example.outputs = {"should_call_jira": True}

    result = evaluate_tool_usage(run, example)

    assert result["key"] == "tool_usage"
    assert result["score"] < 1.0
    assert "get_jira_data" in result["comment"]


def test_evaluate_decision_quality_correct_with_evidence():
    """Test decision quality evaluator with correct decision and evidence."""
    run = Mock()
    run.outputs = {
        "output": "❌ Not ready: 2 tests are failing in the QR validation module"
    }
    run.child_runs = []

    example = Mock()
    example.outputs = {
        "expected_decision": "not_ready",
        "should_cite_failures": True,
    }

    result = evaluate_decision_quality(run, example)

    assert result["key"] == "decision_quality"
    assert result["score"] == 1.0


def test_evaluate_decision_quality_correct_no_evidence():
    """Test decision quality evaluator with correct decision but missing evidence."""
    run = Mock()
    run.outputs = {"output": "❌ Not ready"}
    run.child_runs = []

    example = Mock()
    example.outputs = {
        "expected_decision": "not_ready",
        "should_cite_failures": True,
    }

    result = evaluate_decision_quality(run, example)

    assert result["key"] == "decision_quality"
    assert result["score"] == 0.6  # Correct decision only


def test_evaluate_decision_quality_incorrect():
    """Test decision quality evaluator with wrong decision."""
    run = Mock()
    run.outputs = {"output": "✅ Ready for production"}
    run.child_runs = []

    example = Mock()
    example.outputs = {
        "expected_decision": "not_ready",
        "should_cite_failures": True,
    }

    result = evaluate_decision_quality(run, example)

    assert result["key"] == "decision_quality"
    assert result["score"] < 0.6


def test_evaluate_decision_quality_not_evaluated():
    """Test decision quality evaluator when not required."""
    run = Mock()
    run.outputs = {"output": "Some response"}
    run.child_runs = []

    example = Mock()
    example.outputs = {}  # No expected_decision

    result = evaluate_decision_quality(run, example)

    assert result["key"] == "decision_quality"
    assert result["score"] is None
