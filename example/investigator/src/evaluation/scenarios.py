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
                "acceptable_clarification": False,  # Should handle "QR" → "QR Code Check-in"
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
        {
            "inputs": {"user_query": "Tell me about the reservation system."},
            "outputs": {
                "expected_feature_id": "FEAT-RS-003",
                "should_call_jira": True,
                "should_call_analysis": True,
                "should_provide_info": True,
            },
            "metadata": {
                "category": "informational",
                "difficulty": "medium",
                "description": "Informational query (not explicitly asking about readiness)",
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
                "phase_specific": "UAT",
            },
            "metadata": {
                "category": "phase_specific",
                "difficulty": "hard",
                "description": "Phase-specific readiness query (Development → UAT)",
            },
        },
        # ===== DECISION QUALITY VERIFICATION =====
        {
            "inputs": {"user_query": "Should we deploy QR check-in to production?"},
            "outputs": {
                "expected_feature_id": "FEAT-QR-002",
                "expected_decision": "not_ready",
                "should_cite_failures": True,
                "should_cite_failure_count": True,
                "should_explain_risk": True,
            },
            "metadata": {
                "category": "decision_quality",
                "difficulty": "hard",
                "description": "Decision should cite specific test failures and explain risk",
            },
        },
        {
            "inputs": {
                "user_query": "Give me a readiness assessment for maintenance scheduling."
            },
            "outputs": {
                "expected_feature_id": "FEAT-MS-001",
                "expected_decision": "ready",
                "should_cite_test_metrics": True,
                "should_provide_comprehensive_analysis": True,
            },
            "metadata": {
                "category": "comprehensive",
                "difficulty": "hard",
                "description": "Comprehensive readiness assessment with full analysis",
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

    Raises:
        ValueError: If LangSmith API key is not configured
    """
    # Load config and set environment variables for LangSmith
    config = load_config()

    if not config.langsmith_api_key:
        raise ValueError(
            "LangSmith API key not configured. "
            "Please set LANGSMITH_API_KEY in your .env file.\n"
            "Get your API key from: https://smith.langchain.com/settings"
        )

    # Set environment variables that LangSmith Client expects
    os.environ["LANGSMITH_API_KEY"] = config.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = config.langsmith_project

    client = Client()

    # Get test scenarios
    scenarios = get_test_scenarios()

    print(f"Creating dataset '{dataset_name}' with {len(scenarios)} scenarios...")

    # Check if dataset exists
    try:
        # Try to get existing dataset
        existing_datasets = list(client.list_datasets(dataset_name=dataset_name))
        if existing_datasets:
            dataset = existing_datasets[0]
            print(f"Found existing dataset: {dataset.id}")

            # Delete existing examples to refresh
            examples = list(client.list_examples(dataset_id=dataset.id))
            print(f"Deleting {len(examples)} existing examples...")
            for example in examples:
                client.delete_example(example.id)
        else:
            # Create new dataset
            dataset = client.create_dataset(
                dataset_name=dataset_name, description=description
            )
            print(f"Created new dataset: {dataset.id}")
    except Exception as e:
        # If any error, try creating new dataset
        print(f"Creating new dataset (error checking existing: {e})")
        dataset = client.create_dataset(
            dataset_name=dataset_name, description=description
        )

    # Add examples to dataset
    print(f"Adding {len(scenarios)} examples to dataset...")
    for idx, scenario in enumerate(scenarios, 1):
        client.create_example(
            inputs=scenario["inputs"],
            outputs=scenario["outputs"],
            metadata=scenario["metadata"],
            dataset_id=dataset.id,
        )
        category = scenario["metadata"]["category"]
        difficulty = scenario["metadata"]["difficulty"]
        print(f"  [{idx}/{len(scenarios)}] Added: {category} ({difficulty})")

    print("\n✅ Dataset created successfully!")
    print(f"   Name: {dataset_name}")
    print(f"   ID: {dataset.id}")
    print(f"   Examples: {len(scenarios)}")
    print("   View at: https://smith.langchain.com/")

    return dataset_name


def get_scenario_summary() -> dict[str, Any]:
    """Get summary statistics about test scenarios.

    Returns:
        Dict with scenario counts by category and difficulty
    """
    scenarios = get_test_scenarios()

    categories: dict[str, int] = {}
    difficulties: dict[str, int] = {}

    for scenario in scenarios:
        category = scenario["metadata"]["category"]
        difficulty = scenario["metadata"]["difficulty"]

        categories[category] = categories.get(category, 0) + 1
        difficulties[difficulty] = difficulties.get(difficulty, 0) + 1

    return {
        "total": len(scenarios),
        "by_category": categories,
        "by_difficulty": difficulties,
        "scenarios": [
            {
                "query": s["inputs"]["user_query"],
                "category": s["metadata"]["category"],
                "difficulty": s["metadata"]["difficulty"],
                "description": s["metadata"]["description"],
            }
            for s in scenarios
        ],
    }


if __name__ == "__main__":
    # Allow running this module directly to create dataset
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--summary":
        summary = get_scenario_summary()
        print(f"\n{'=' * 60}")
        print("TEST SCENARIO SUMMARY")
        print(f"{'=' * 60}\n")
        print(f"Total Scenarios: {summary['total']}\n")
        print("By Category:")
        for cat, count in summary["by_category"].items():
            print(f"  - {cat}: {count}")
        print("\nBy Difficulty:")
        for diff, count in summary["by_difficulty"].items():
            print(f"  - {diff}: {count}")
        print(f"\n{'=' * 60}\n")
        print("Scenario Details:")
        for idx, scenario in enumerate(summary["scenarios"], 1):
            print(f"\n{idx}. [{scenario['category']}] [{scenario['difficulty']}]")
            print(f"   Query: {scenario['query']}")
            print(f"   {scenario['description']}")
    else:
        create_evaluation_dataset()
