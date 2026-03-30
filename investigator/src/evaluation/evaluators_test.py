"""Unit tests for the custom evaluators."""

from unittest.mock import MagicMock
import pytest
from src.evaluation.evaluators import (
    evaluate_feature_identification,
    evaluate_tool_usage,
    evaluate_decision_quality,
)

@pytest.fixture
def mock_run():
    run = MagicMock()
    run.run_type = "chain"
    run.name = "agent"
    run.inputs = {"user_query": "Test query"}
    run.outputs = {"output": "The feature FEAT-MS-001 is ready. 156 tests passed."}
    run.child_runs = []
    return run

@pytest.fixture
def mock_example():
    example = MagicMock()
    example.inputs = {"user_query": "Test query"}
    example.outputs = {
        "expected_decision": "ready",
        "expected_feature_id": "FEAT-MS-001",
        "should_call_jira": True,
        "should_call_analysis": True,
    }
    return example

def test_evaluate_feature_identification_success(mock_run, mock_example):
    # Mock a tool call child run
    tool_run = MagicMock()
    tool_run.run_type = "tool"
    tool_run.name = "get_analysis"
    tool_run.inputs = {"feature_id": "FEAT-MS-001", "analysis_type": "metrics"}
    tool_run.child_runs = []
    mock_run.child_runs = [tool_run]

    result = evaluate_feature_identification(mock_run, mock_example)
    assert result["score"] == 1.0
    assert "FEAT-MS-001" in result["comment"]

def test_evaluate_tool_usage_success(mock_run, mock_example):
    jira_tool = MagicMock()
    jira_tool.run_type = "tool"
    jira_tool.name = "get_jira_data"
    jira_tool.inputs = {}
    jira_tool.child_runs = []

    analysis_tool = MagicMock()
    analysis_tool.run_type = "tool"
    analysis_tool.name = "get_analysis"
    analysis_tool.inputs = {"feature_id": "FEAT-MS-001"}
    analysis_tool.child_runs = []

    mock_run.child_runs = [jira_tool, analysis_tool]

    result = evaluate_tool_usage(mock_run, mock_example)
    assert result["score"] == 1.0
    assert "correctly" in result["comment"]

def test_evaluate_decision_quality_success(mock_run, mock_example):
    result = evaluate_decision_quality(mock_run, mock_example)
    assert result["score"] == 1.0
    assert "Correct decision" in result["comment"]

def test_evaluate_decision_quality_missing_metrics(mock_run, mock_example):
    mock_run.outputs = {"output": "The feature is ready."} # No numbers/metrics
    result = evaluate_decision_quality(mock_run, mock_example)
    assert result["score"] == 0.6 # Only decision is correct
    assert "Missing specific" in result["comment"]
