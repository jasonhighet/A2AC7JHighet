"""Custom evaluator functions for scoring agent performance.

This module implements three core evaluators:
1. Feature Identification: Does the agent identify the correct feature?
2. Tool Usage: Does the agent call the right tools with correct parameters?
3. Decision Quality: Does the agent make correct decisions with proper evidence?

Note: LangSmith's evaluate() function does not populate child_runs by default.
We must fetch them explicitly using the LangSmith client when needed.
"""

import ast
import re
from typing import Any

from langsmith import Client
from langsmith.schemas import Example, Run


def _get_run_with_child_runs(run: Run) -> Run:
    """Fetch the full run with child_runs populated from LangSmith API.

    LangSmith's evaluate() doesn't populate child_runs by default.
    This function fetches them when we need to inspect tool calls.

    Args:
        run: The run object (may not have child_runs populated)

    Returns:
        Run with child_runs loaded, or original run if fetch fails
    """
    # If child_runs is already populated, use it
    if run.child_runs:
        return run

    # Try to fetch child runs from API
    try:
        client = Client()
        full_run = client.read_run(run.id, load_child_runs=True)
        return full_run
    except Exception:
        # If fetch fails (e.g., no API key, network error), return original
        return run


def evaluate_feature_identification(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent correctly identified the feature.

    Checks if the agent identified the correct feature_id by examining
    tool calls (especially get_analysis calls which require feature_id).

    Args:
        run: The actual agent run with trace data
        example: The test example with expected outputs

    Returns:
        Evaluation result dict with key, score, and comment
    """
    expected_feature_id = example.outputs.get("expected_feature_id")

    # If no expected feature_id specified, check if should_identify_feature is set
    should_identify = example.outputs.get("should_identify_feature", False)
    if not expected_feature_id and not should_identify:
        # Not testing feature identification for this example
        return {
            "key": "feature_identification",
            "score": None,  # Skip scoring
            "comment": "Feature identification not evaluated for this scenario",
        }

    # Extract feature_id from agent's tool calls
    actual_feature_id = _extract_feature_from_run(run)

    if expected_feature_id:
        correct = actual_feature_id == expected_feature_id
        score = 1.0 if correct else 0.0
        comment = f"Expected {expected_feature_id}, got {actual_feature_id or 'None'}"
    else:
        # Just check if agent identified some feature
        correct = actual_feature_id is not None
        score = 1.0 if correct else 0.0
        comment = f"Agent {'identified' if correct else 'did not identify'} a feature"

    return {"key": "feature_identification", "score": score, "comment": comment}


def evaluate_tool_usage(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent called the correct tools with correct parameters.

    Checks:
    - Did agent call get_jira_data (if required)?
    - Did agent call get_analysis (if required)?
    - Did agent retrieve both unit test and coverage data (if required)?
    - Are tool parameters correct?

    Args:
        run: The actual agent run with trace data
        example: The test example with expected outputs

    Returns:
        Evaluation result dict with key, score, and comment
    """
    expected_outputs = example.outputs

    should_call_jira = expected_outputs.get("should_call_jira", False)
    should_call_analysis = expected_outputs.get("should_call_analysis", False)
    must_check_both_metrics = expected_outputs.get("must_check_both_metrics", False)
    analysis_types_required = expected_outputs.get("analysis_types_required", [])

    # Extract tool calls from run
    tool_calls = _extract_tool_calls(run)

    # Check individual requirements
    called_jira = any(tc["name"] == "get_jira_data" for tc in tool_calls)
    called_analysis = any(tc["name"] == "get_analysis" for tc in tool_calls)

    # Check specific analysis types
    analysis_calls = [tc for tc in tool_calls if tc["name"] == "get_analysis"]
    analysis_types_called = set()
    for call in analysis_calls:
        analysis_type = call.get("inputs", {}).get("analysis_type", "")
        if analysis_type:
            analysis_types_called.add(analysis_type)

    # Scoring logic
    score = 0.0
    issues = []

    # Check JIRA call (30% of score)
    if should_call_jira:
        if called_jira:
            score += 0.3
        else:
            issues.append("Missing get_jira_data call")

    # Check analysis call (30% of score)
    if should_call_analysis:
        if called_analysis:
            score += 0.3
        else:
            issues.append("Missing get_analysis call")

    # Check specific analysis types (40% of score)
    if analysis_types_required:
        types_found = 0
        types_missing = []
        for required_type in analysis_types_required:
            if required_type in analysis_types_called:
                types_found += 1
            else:
                types_missing.append(required_type)

        # Proportional scoring
        if analysis_types_required:
            score += 0.4 * (types_found / len(analysis_types_required))

        if types_missing:
            issues.append(f"Missing analysis types: {', '.join(types_missing)}")

    # If no specific requirements, full score for calling tools appropriately
    if (
        not should_call_jira
        and not should_call_analysis
        and not analysis_types_required
    ):
        score = 1.0
        issues.append("No specific tool requirements for this scenario")

    comment = "; ".join(issues) if issues else "All required tools called correctly"

    return {"key": "tool_usage", "score": score, "comment": comment}


def evaluate_decision_quality(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent made the correct readiness decision with proper evidence.

    Checks:
    - Correct decision (ready/not_ready/needs_info)
    - Cites specific test metrics (e.g., "3 tests failing")
    - References evidence from analysis data
    - Explains reasoning clearly

    Args:
        run: The actual agent run with trace data
        example: The test example with expected outputs

    Returns:
        Evaluation result dict with key, score, and comment
    """
    expected_outputs = example.outputs
    expected_decision = expected_outputs.get("expected_decision")

    # If no expected decision, skip evaluation
    if not expected_decision:
        return {
            "key": "decision_quality",
            "score": None,
            "comment": "Decision quality not evaluated for this scenario",
        }

    # Parse agent's final response
    agent_response = _extract_agent_response(run)
    actual_decision = _parse_decision_from_response(agent_response)

    # Check if decision is correct
    decision_correct = actual_decision == expected_decision

    # Check if agent cited specific evidence
    should_cite_failures = expected_outputs.get("should_cite_failures", False)
    should_cite_test_metrics = expected_outputs.get("should_cite_test_metrics", False)

    cites_test_counts = _contains_test_counts(agent_response)
    cites_failures = _contains_failure_mentions(agent_response)
    cites_metrics = cites_test_counts or cites_failures

    # Scoring logic
    score = 0.0
    issues = []

    # Decision correctness (60% of score)
    if decision_correct:
        score += 0.6
    else:
        issues.append(
            f"Wrong decision: expected {expected_decision}, got {actual_decision}"
        )

    # Evidence citation (40% of score)
    if should_cite_failures:
        if cites_failures:
            score += 0.4
        else:
            issues.append("Missing failure citations")
    elif should_cite_test_metrics:
        if cites_metrics:
            score += 0.4
        else:
            issues.append("Missing test metric citations")
    else:
        # No specific citation requirements, give full evidence score
        score += 0.4

    comment = "; ".join(issues) if issues else "Correct decision with proper evidence"

    return {"key": "decision_quality", "score": score, "comment": comment}


# ===== Helper Functions =====


def _extract_feature_from_run(run: Run) -> str | None:
    """Extract the feature_id the agent identified.

    Looks through tool calls for get_analysis calls which require feature_id.
    Reuses _extract_tool_calls to ensure consistent extraction logic.

    Args:
        run: The agent run with trace data

    Returns:
        Feature ID string or None if not found
    """
    # Reuse the working _extract_tool_calls function
    tool_calls = _extract_tool_calls(run)

    # Look for get_analysis calls with feature_id
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_inputs = tool_call.get("inputs", {})

        # Check if this is a get_analysis call (or contains get_analysis in name)
        if "get_analysis" in tool_name and isinstance(tool_inputs, dict):
            feature_id = tool_inputs.get("feature_id")
            if feature_id:
                return feature_id

    # Fallback: check any tool with feature_id in inputs
    for tool_call in tool_calls:
        tool_inputs = tool_call.get("inputs", {})
        if isinstance(tool_inputs, dict):
            feature_id = tool_inputs.get("feature_id")
            if feature_id:
                return feature_id

    return None


def _normalize_tool_inputs(inputs: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize tool inputs from LangSmith trace format.

    LangSmith traces store tool inputs in a nested format:
    {'input': "{'feature_id': 'FEAT-MS-001', 'analysis_type': 'metrics/unit_test_results'}"}

    This function extracts and parses the actual arguments.

    Args:
        inputs: Raw inputs dict from LangSmith trace

    Returns:
        Normalized dict with actual tool arguments
    """
    if not inputs:
        return {}

    # If inputs has an 'input' key with a string value, try to parse it
    if "input" in inputs and isinstance(inputs["input"], str):
        input_str = inputs["input"]
        # Try to parse as Python dict literal
        try:
            parsed = ast.literal_eval(input_str)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            pass

    # Return inputs as-is if no normalization needed
    return inputs


def _extract_tool_calls(run: Run) -> list[dict[str, Any]]:
    """Extract all tool calls from the run.

    Recursively searches all child runs since LangGraph nests tools deeply.
    Fetches child_runs from API if not already populated.

    Args:
        run: The agent run with trace data

    Returns:
        List of dicts with tool name and inputs (normalized)
    """
    # Ensure we have child_runs populated
    run_with_children = _get_run_with_child_runs(run)

    tool_calls: list[dict[str, Any]] = []

    def search_recursive(node: Run) -> None:
        """Recursively search through run tree for tool calls."""
        # Check if this node is a tool call
        if node.run_type == "tool":
            # Normalize inputs to extract actual arguments
            normalized_inputs = _normalize_tool_inputs(node.inputs)
            tool_calls.append(
                {"name": node.name, "inputs": normalized_inputs, "outputs": node.outputs or {}}
            )

        # Recursively search children
        if hasattr(node, "child_runs") and node.child_runs:
            for child in node.child_runs:
                search_recursive(child)

    search_recursive(run_with_children)
    return tool_calls


def _extract_agent_response(run: Run) -> str:
    """Extract the agent's final response from the run.

    Args:
        run: The agent run with trace data

    Returns:
        Agent response string
    """
    if hasattr(run, "outputs") and run.outputs:
        if isinstance(run.outputs, dict):
            # Try different output key formats
            for key in ["output", "response", "content", "text"]:
                if key in run.outputs:
                    return str(run.outputs[key])
        elif isinstance(run.outputs, str):
            return run.outputs

    return ""


def _parse_decision_from_response(response: str) -> str:
    """Parse the agent's decision from its response text.

    Looks for keywords indicating ready/not_ready/needs_info/unknown.

    Args:
        response: Agent response text

    Returns:
        Decision string: "ready", "not_ready", "needs_info", or "unknown"
    """
    response_lower = response.lower()

    # Check for "not ready" first (more specific than "ready")
    if "not ready" in response_lower or "❌" in response or "isn't ready" in response_lower:
        return "not_ready"
    elif "ready" in response_lower or "✅" in response or "is ready" in response_lower:
        return "ready"
    elif (
        "need" in response_lower
        or "more information" in response_lower
        or "clarification" in response_lower
        or "not sure" in response_lower
    ):
        return "needs_info"
    else:
        return "unknown"


def _contains_test_counts(text: str) -> bool:
    """Check if text contains test count mentions (e.g., "3 tests", "487 tests").

    Args:
        text: Text to check

    Returns:
        True if test counts found
    """
    # Look for patterns like "N tests", "N test", "N failing", "N passed"
    patterns = [
        r"\d+\s+tests?",
        r"\d+\s+failing",
        r"\d+\s+passed",
        r"\d+\s+failures?",
        r"\d+\s+unit\s+tests?",
    ]

    for pattern in patterns:
        if re.search(pattern, text.lower()):
            return True

    return False


def _contains_failure_mentions(text: str) -> bool:
    """Check if text contains mentions of test failures.

    Args:
        text: Text to check

    Returns:
        True if failure mentions found
    """
    failure_keywords = [
        "failing",
        "failed",
        "failure",
        "failures",
        "test fail",
        "tests fail",
    ]

    text_lower = text.lower()
    return any(keyword in text_lower for keyword in failure_keywords)
