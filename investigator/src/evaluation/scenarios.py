"""Test scenario definitions and LangSmith dataset creation.

This module defines evaluation test scenarios and provides functions to create
and update the LangSmith dataset for agent evaluation.
"""

import os
from typing import Any

from langsmith import Client

from src.utils.config import load_config


def get_test_scenarios() -> list[dict[str, Any]]:
    """Define comprehensive test scenarios for agent evaluation.

    Returns:
        List of test scenario dicts with inputs, outputs, and metadata
    """
    scenarios = [
        # ===== HAPPY PATH SCENARIOS =====
        {
            "inputs": {
                "user_query": "Is the maintenance scheduling feature ready for its next phase?"
            },
            "outputs": {
                "expected_decision": "ready",
                "expected_feature_id": "FEAT-MS-001",
                "should_call_jira": True,
                "should_call_analysis": True,
                "should_cite_test_metrics": True,
                "analysis_types_required": [
                    "metrics/unit_test_results",
                    "metrics/test_coverage_report",
                ],
            },
            "metadata": {
                "category": "happy_path",
                "difficulty": "easy",
                "description": "Clear feature name with all tests passing",
            },
        },
        {
            "inputs": {"user_query": "Is QR code check-in ready for production?"},
            "outputs": {
                "expected_decision": "not_ready",
                "expected_feature_id": "FEAT-QR-002",
                "should_call_jira": True,
                "should_call_analysis": True,
                "should_cite_failures": True,
                "failure_reason": "failing_tests",
            },
            "metadata": {
                "category": "failing_tests",
                "difficulty": "medium",
                "description": "Feature with failing unit tests should block progression",
            },
        },
        # ===== AMBIGUOUS QUERY SCENARIOS =====
        {
            "inputs": {"user_query": "Is the QR feature ready?"},
            "outputs": {
                "expected_feature_id": "FEAT-QR-002",
                "should_call_jira": True,
                "should_identify_feature": True,
                "acceptable_clarification": False,  # Should handle "QR" -> "QR Code Check-in"
            },
            "metadata": {
                "category": "ambiguous_query",
                "difficulty": "medium",
                "description": "Partial feature name (QR) should match QR Code Check-in",
            },
        },
        {
            "inputs": {"user_query": "What's the status of maintenance scheduling?"},
            "outputs": {
                "expected_feature_id": "FEAT-MS-001",
                "should_call_jira": True,
                "should_call_analysis": True,
                "expected_decision": "ready",
            },
            "metadata": {
                "category": "happy_path",
                "difficulty": "easy",
                "description": "Natural language status query",
            },
        },
        # ===== EDGE CASES =====
        {
            "inputs": {"user_query": "Is the unicorn management feature ready?"},
            "outputs": {
                "expected_decision": "unknown",
                "should_call_jira": True,
                "should_handle_gracefully": True,
                "should_explain_not_found": True,
            },
            "metadata": {
                "category": "edge_case",
                "difficulty": "easy",
                "description": "Non-existent feature should be handled gracefully",
            },
        },
        # ===== TOOL USAGE VERIFICATION =====
        {
            "inputs": {
                "user_query": "Can the resource reservation system go to production?"
            },
            "outputs": {
                "expected_feature_id": "FEAT-RS-003",
                "should_call_jira": True,
                "should_call_analysis": True,
                "analysis_types_required": [
                    "metrics/unit_test_results",
                    "metrics/test_coverage_report",
                ],
                "must_check_both_metrics": True,
            },
            "metadata": {
                "category": "tool_usage",
                "difficulty": "medium",
                "description": "Verify agent calls both unit test and coverage analysis",
            },
        },
        {
            "inputs": {
                "user_query": "Is the contribution tracking feature ready for UAT?"
            },
            "outputs": {
                "expected_feature_id": "FEAT-CT-004",
                "should_call_jira": True,
                "should_call_analysis": True,
                "expected_decision": "not_ready",
            },
            "metadata": {
                "category": "phase_specific",
                "difficulty": "hard",
                "description": "Phase-specific readiness query (Development -> UAT)",
            },
        },
    ]

    return scenarios


def create_evaluation_dataset(
    dataset_name: str = "investigator-agent-eval",
    description: str = "Evaluation scenarios for Investigator Agent - Step 6",
) -> str:
    """Create or update the evaluation dataset in LangSmith.

    Args:
        dataset_name: Name of the dataset in LangSmith
        description: Description of the dataset

    Returns:
        Dataset name for use in evaluations
    """
    config = load_config()

    if not config.langsmith_api_key:
        raise ValueError(
            "LangSmith API key not configured. "
            "Please set LANGSMITH_API_KEY in your .env file."
        )

    # Set environment variables for LangSmith client
    os.environ["LANGSMITH_API_KEY"] = config.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = config.langsmith_project

    client = Client()

    # Get test scenarios
    scenarios = get_test_scenarios()

    # Create or retrieve dataset
    try:
        if client.has_dataset(dataset_name=dataset_name):
            dataset = client.read_dataset(dataset_name=dataset_name)
            # Delete existing examples to ensure a clean refresh
            examples = list(client.list_examples(dataset_id=dataset.id))
            for example in examples:
                client.delete_example(example.id)
        else:
            dataset = client.create_dataset(
                dataset_name=dataset_name, description=description
            )
    except Exception:
        # Fallback if has_dataset or read_dataset fails
        dataset = client.create_dataset(
            dataset_name=dataset_name, description=description
        )

    # Add examples
    for scenario in scenarios:
        client.create_example(
            inputs=scenario["inputs"],
            outputs=scenario["outputs"],
            metadata=scenario["metadata"],
            dataset_id=dataset.id,
        )

    return dataset_name
