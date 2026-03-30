"""Custom evaluator functions for scoring agent performance.

This module implements three core evaluators:
1. Feature Identification: Does the agent identify the correct feature?
2. Tool Usage: Does the agent call the right tools with correct parameters?
3. Decision Quality: Does the agent make correct decisions with proper evidence?
"""

import ast
import re
from typing import Any

from langsmith import Client
from langsmith.schemas import Example, Run


def _get_run_with_child_runs(run: Run) -> Run:
    """Fetch the full run with child_runs populated from LangSmith API."""
    if run.child_runs:
        return run
    try:
        client = Client()
        full_run = client.read_run(run.id, load_child_runs=True)
        return full_run
    except Exception:
        return run


def evaluate_feature_identification(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent correctly identified the feature."""
    expected_feature_id = example.outputs.get("expected_feature_id")
    should_identify = example.outputs.get("should_identify_feature", False)

    if not expected_feature_id and not should_identify:
        return {
            "key": "feature_identification",
            "score": None,
            "comment": "Not evaluated for this scenario",
        }

    actual_feature_id = _extract_feature_from_run(run)

    if expected_feature_id:
        correct = actual_feature_id == expected_feature_id
        score = 1.0 if correct else 0.0
        comment = f"Expected {expected_feature_id}, got {actual_feature_id or 'None'}"
    else:
        correct = actual_feature_id is not None
        score = 1.0 if correct else 0.0
        comment = f"Agent {'identified' if correct else 'did not identify'} a feature"

    return {"key": "feature_identification", "score": score, "comment": comment}


def evaluate_tool_usage(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent called the correct tools."""
    expected_outputs = example.outputs
    should_call_jira = expected_outputs.get("should_call_jira", False)
    should_call_analysis = expected_outputs.get("should_call_analysis", False)
    analysis_types_required = expected_outputs.get("analysis_types_required", [])

    tool_calls = _extract_tool_calls(run)
    called_jira = any(tc["name"] == "get_jira_data" for tc in tool_calls)
    called_analysis = any(tc["name"] == "get_analysis" for tc in tool_calls)

    analysis_types_called = set()
    for tc in tool_calls:
        if tc["name"] == "get_analysis":
            analysis_type = tc.get("inputs", {}).get("analysis_type", "")
            if analysis_type:
                analysis_types_called.add(analysis_type)

    score = 0.0
    issues = []

    if should_call_jira:
        if called_jira:
            score += 0.3
        else:
            issues.append("Missing get_jira_data call")
    if should_call_analysis:
        if called_analysis:
            score += 0.3
        else:
            issues.append("Missing get_analysis call")

    if analysis_types_required:
        found = sum(1 for t in analysis_types_required if t in analysis_types_called)
        score += 0.4 * (found / len(analysis_types_required))
        missing = [t for t in analysis_types_required if t not in analysis_types_called]
        if missing:
            issues.append(f"Missing analysis types: {', '.join(missing)}")
    else:
        score += 0.4  # Bonus or default for no specific analysis requirements

    comment = "; ".join(issues) if issues else "All required tools called correctly"
    return {"key": "tool_usage", "score": min(score, 1.0), "comment": comment}


def evaluate_decision_quality(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate decision correctness and metric citations."""
    expected_decision = example.outputs.get("expected_decision")
    if not expected_decision:
        return {
            "key": "decision_quality",
            "score": None,
            "comment": "Not evaluated for this scenario",
        }

    agent_response = _extract_agent_response(run)
    actual_decision = _parse_decision_from_response(agent_response)

    decision_correct = actual_decision == expected_decision
    has_metrics = _contains_metrics(agent_response)

    score = 0.0
    issues = []

    if decision_correct:
        score += 0.6
    else:
        issues.append(f"Expected {expected_decision}, got {actual_decision}")

    if has_metrics:
        score += 0.4
    else:
        issues.append("Missing specific test/coverage metrics in response")

    comment = "; ".join(issues) if issues else "Correct decision with evidence"
    return {"key": "decision_quality", "score": score, "comment": comment}


# ===== Helpers =====

def _extract_feature_from_run(run: Run) -> str | None:
    """Extract feature_id from tool calls."""
    tool_calls = _extract_tool_calls(run)
    for tc in tool_calls:
        feature_id = tc.get("inputs", {}).get("feature_id")
        if feature_id:
            return feature_id
    return None


def _extract_tool_calls(run: Run) -> list[dict[str, Any]]:
    """Recursively extract tool calls from run and children."""
    run_with_children = _get_run_with_child_runs(run)
    tool_calls: list[dict[str, Any]] = []

    def _traverse(node: Run):
        if node.run_type == "tool":
            inputs = node.inputs
            if inputs and "input" in inputs and isinstance(inputs["input"], str):
                try:
                    inputs = ast.literal_eval(inputs["input"])
                except (ValueError, SyntaxError):
                    pass
            tool_calls.append({"name": node.name, "inputs": inputs})
        if node.child_runs:
            for child in node.child_runs:
                _traverse(child)

    _traverse(run_with_children)
    return tool_calls


def _extract_agent_response(run: Run) -> str:
    """Extract final response string from agent run."""
    outputs = run.outputs or {}
    for key in ["output", "response", "content"]:
        if key in outputs:
            return str(outputs[key])
    return str(outputs)


def _parse_decision_from_response(response: str) -> str:
    """Determine decision category from response text."""
    lower = response.lower()
    if "not ready" in lower or "block" in lower or "failed" in lower:
        return "not_ready"
    if "ready" in lower or "production ready" in lower or "uat ready" in lower:
        return "ready"
    return "unknown"


def _contains_metrics(text: str) -> bool:
    """Checks for mentions of test counts or percentages."""
    patterns = [
        r"\d+\s+tests?",
        r"\d+%",
        r"coverage",
        r"passed",
        r"failed",
    ]
    return any(re.search(p, text.lower()) for p in patterns)
