"""Custom evaluator functions for scoring agent performance.

This module implements three core evaluators:
1. Feature Identification: Does the agent identify the correct feature?
2. Tool Usage: Does the agent call the right tools with correct parameters?
3. Decision Quality: Does the agent make correct decisions with proper evidence?
"""

import ast
import re
from typing import Any

from langsmith.schemas import Example, Run

from src.utils.constants import (
    DECISION_NEEDS_INFO,
    DECISION_NOT_READY,
    DECISION_READY,
    DECISION_UNKNOWN,
    EVAL_KEY_DECISION_QUALITY,
    EVAL_KEY_FEATURE_IDENTIFICATION,
    EVAL_KEY_TOOL_USAGE,
    OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED,
    OUTPUT_KEY_EXPECTED_DECISION,
    OUTPUT_KEY_EXPECTED_FEATURE_ID,
    OUTPUT_KEY_SHOULD_CALL_ANALYSIS,
    OUTPUT_KEY_SHOULD_CALL_JIRA,
    OUTPUT_KEY_SHOULD_CITE_FAILURES,
    OUTPUT_KEY_SHOULD_CITE_TEST_METRICS,
    OUTPUT_KEY_SHOULD_IDENTIFY_FEATURE,
    RUN_TYPE_TOOL,
    TOOL_GET_ANALYSIS,
    TOOL_GET_JIRA_DATA,
)


def evaluate_feature_identification(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent correctly identified the feature.

    Checks if the agent identified the correct feature_id by examining
    tool calls (especially get_analysis calls which require feature_id).

    Args:
        run: The actual agent run with trace data (already includes child runs)
        example: The test example with expected outputs

    Returns:
        Evaluation result dict with key, score, and comment
    """
    expected_feature_id = example.outputs.get(OUTPUT_KEY_EXPECTED_FEATURE_ID)

    # If no expected feature_id specified, check if should_identify_feature is set
    should_identify = example.outputs.get(OUTPUT_KEY_SHOULD_IDENTIFY_FEATURE, False)
    if not expected_feature_id and not should_identify:
        # Not testing feature identification for this example
        return {
            "key": EVAL_KEY_FEATURE_IDENTIFICATION,
            "score": None,  # Skip scoring
            "comment": "Feature identification not evaluated for this scenario",
        }

    # Extract feature_id from agent's tool calls
    # Note: run already has child_runs loaded by LangSmith
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

    return {"key": EVAL_KEY_FEATURE_IDENTIFICATION, "score": score, "comment": comment}


def evaluate_tool_usage(run: Run, example: Example) -> dict[str, Any]:
    """Evaluate if the agent called the correct tools with correct parameters.

    Checks:
    - Did agent call get_jira_data (if required)?
    - Did agent call get_analysis (if required)?
    - Did agent retrieve both unit test and coverage data (if required)?
    - Are tool parameters correct?

    Args:
        run: The actual agent run with trace data (already includes child runs)
        example: The test example with expected outputs

    Returns:
        Evaluation result dict with key, score, and comment
    """
    expected_outputs = example.outputs

    should_call_jira = expected_outputs.get(OUTPUT_KEY_SHOULD_CALL_JIRA, False)
    should_call_analysis = expected_outputs.get(OUTPUT_KEY_SHOULD_CALL_ANALYSIS, False)
    analysis_types_required = expected_outputs.get(
        OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED, []
    )

    # Extract tool calls from run
    # Note: run already has child_runs loaded by LangSmith
    tool_calls = _extract_tool_calls(run)

    # Check individual requirements
    called_jira = any(tc["name"] == TOOL_GET_JIRA_DATA for tc in tool_calls)
    called_analysis = any(tc["name"] == TOOL_GET_ANALYSIS for tc in tool_calls)

    # Check specific analysis types
    analysis_calls = [tc for tc in tool_calls if tc["name"] == TOOL_GET_ANALYSIS]
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

    return {"key": EVAL_KEY_TOOL_USAGE, "score": score, "comment": comment}


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
    expected_decision = expected_outputs.get(OUTPUT_KEY_EXPECTED_DECISION)

    # If no expected decision, skip evaluation
    if not expected_decision:
        return {
            "key": EVAL_KEY_DECISION_QUALITY,
            "score": None,
            "comment": "Decision quality not evaluated for this scenario",
        }

    # Parse agent's final response
    agent_response = _extract_agent_response(run)
    actual_decision = _parse_decision_from_response(agent_response)

    # Check if decision is correct
    decision_correct = actual_decision == expected_decision

    # Check if agent cited specific evidence
    should_cite_failures = expected_outputs.get(OUTPUT_KEY_SHOULD_CITE_FAILURES, False)
    should_cite_test_metrics = expected_outputs.get(
        OUTPUT_KEY_SHOULD_CITE_TEST_METRICS, False
    )

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

    return {"key": EVAL_KEY_DECISION_QUALITY, "score": score, "comment": comment}


# ===== Helper Functions =====


def _extract_feature_from_run(run: Run) -> str | None:
    """Extract the feature_id the agent identified.

    Looks through tool calls for get_analysis calls which require feature_id.
    Recursively searches through all child runs to handle nested structures.

    Args:
        run: The agent run with trace data

    Returns:
        Feature ID string or None if not found
    """
    if not hasattr(run, "child_runs") or not run.child_runs:
        return None

    for child in run.child_runs:
        child_name = getattr(child, "name", None)

        # Check if this child is the get_analysis tool
        if child_name == TOOL_GET_ANALYSIS:
            # Handle both dict and object-style access to inputs
            if hasattr(child, "inputs") and child.inputs:
                if isinstance(child.inputs, dict):
                    # Try direct access first (for backwards compatibility)
                    feature_id = child.inputs.get("feature_id")
                    if feature_id:
                        return feature_id

                    # LangGraph wraps tool inputs in an 'input' key with string value
                    # Parse from the 'input' key
                    if "input" in child.inputs:
                        input_str = child.inputs["input"]
                        try:
                            # Try to parse as Python literal
                            parsed = ast.literal_eval(input_str)
                            if isinstance(parsed, dict):
                                feature_id = parsed.get("feature_id")
                                if feature_id:
                                    return feature_id
                        except Exception:
                            # If parsing fails, try regex as fallback
                            match = re.search(r"'feature_id':\s*'([^']+)'", input_str)
                            if match:
                                return match.group(1)

        # Recursively search child's children
        nested_feature_id = _extract_feature_from_run(child)
        if nested_feature_id:
            return nested_feature_id

    return None


def _extract_tool_calls(run: Run) -> list[dict[str, Any]]:
    """Extract all tool calls from the run.

    Recursively searches through all child runs to handle nested structures
    like those created by LangGraph.

    Args:
        run: The agent run with trace data

    Returns:
        List of dicts with tool name and inputs
    """
    tool_calls = []

    if not hasattr(run, "child_runs") or not run.child_runs:
        return tool_calls

    for child in run.child_runs:
        # Check if this child is a tool call
        if child.run_type == RUN_TYPE_TOOL:
            tool_calls.append(
                {
                    "name": child.name,
                    "inputs": child.inputs or {},
                    "outputs": child.outputs or {},
                }
            )

        # Recursively search this child's children
        nested_tool_calls = _extract_tool_calls(child)
        tool_calls.extend(nested_tool_calls)

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
    if (
        "not ready" in response_lower
        or "❌" in response
        or "isn't ready" in response_lower
    ):
        return DECISION_NOT_READY
    elif "ready" in response_lower or "✅" in response or "is ready" in response_lower:
        return DECISION_READY
    elif (
        "need" in response_lower
        or "more information" in response_lower
        or "clarification" in response_lower
        or "not sure" in response_lower
    ):
        return DECISION_NEEDS_INFO
    else:
        return DECISION_UNKNOWN


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
