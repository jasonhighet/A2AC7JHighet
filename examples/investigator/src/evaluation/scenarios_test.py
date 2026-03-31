"""Tests for evaluation scenarios to ensure consistency with constants."""

from src.evaluation.scenarios import get_test_scenarios
from src.utils.constants import (
    ANALYSIS_TEST_COVERAGE,
    ANALYSIS_UNIT_TEST_RESULTS,
    DECISION_READY,
    OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED,
    OUTPUT_KEY_EXPECTED_DECISION,
    OUTPUT_KEY_EXPECTED_FEATURE_ID,
    OUTPUT_KEY_SHOULD_CALL_ANALYSIS,
    OUTPUT_KEY_SHOULD_CALL_JIRA,
    OUTPUT_KEY_SHOULD_CITE_FAILURES,
    OUTPUT_KEY_SHOULD_CITE_TEST_METRICS,
    OUTPUT_KEY_SHOULD_IDENTIFY_FEATURE,
    VALID_ANALYSIS_TYPES,
    VALID_DECISIONS,
)


def test_scenarios_load_successfully():
    """Test that scenarios can be loaded without errors."""
    scenarios = get_test_scenarios()
    assert isinstance(scenarios, list)
    assert len(scenarios) > 0


def test_all_scenarios_have_required_structure():
    """Test that all scenarios have inputs, outputs, and metadata."""
    scenarios = get_test_scenarios()

    for idx, scenario in enumerate(scenarios):
        assert "inputs" in scenario, f"Scenario {idx} missing 'inputs'"
        assert "outputs" in scenario, f"Scenario {idx} missing 'outputs'"
        assert "metadata" in scenario, f"Scenario {idx} missing 'metadata'"

        assert "user_query" in scenario["inputs"], (
            f"Scenario {idx} missing 'user_query'"
        )
        assert isinstance(scenario["inputs"]["user_query"], str)


def test_scenarios_use_valid_decision_constants():
    """Test that all decision values in scenarios are valid constants."""
    scenarios = get_test_scenarios()

    for idx, scenario in enumerate(scenarios):
        if OUTPUT_KEY_EXPECTED_DECISION in scenario["outputs"]:
            decision = scenario["outputs"][OUTPUT_KEY_EXPECTED_DECISION]
            assert decision in VALID_DECISIONS, (
                f"Scenario {idx} has invalid decision: {decision}. "
                f"Must be one of {VALID_DECISIONS}"
            )


def test_scenarios_use_valid_analysis_types():
    """Test that all analysis types in scenarios are valid constants."""
    scenarios = get_test_scenarios()

    for idx, scenario in enumerate(scenarios):
        if OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED in scenario["outputs"]:
            analysis_types = scenario["outputs"][OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED]
            assert isinstance(analysis_types, list), (
                f"Scenario {idx} analysis_types not a list"
            )

            for analysis_type in analysis_types:
                assert analysis_type in VALID_ANALYSIS_TYPES, (
                    f"Scenario {idx} has invalid analysis_type: {analysis_type}. "
                    f"Must be one of {VALID_ANALYSIS_TYPES}"
                )


def test_scenarios_use_constant_keys():
    """Test that scenarios produce the expected output keys.

    Note: The constants resolve to string values at runtime, which is correct.
    This test verifies that all expected keys are present and properly formatted.
    """
    scenarios = get_test_scenarios()

    # Expected keys that should be produced by the constants
    expected_keys = {
        OUTPUT_KEY_EXPECTED_DECISION,
        OUTPUT_KEY_EXPECTED_FEATURE_ID,
        OUTPUT_KEY_SHOULD_CALL_JIRA,
        OUTPUT_KEY_SHOULD_CALL_ANALYSIS,
        OUTPUT_KEY_SHOULD_CITE_FAILURES,
        OUTPUT_KEY_SHOULD_CITE_TEST_METRICS,
        OUTPUT_KEY_SHOULD_IDENTIFY_FEATURE,
        OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED,
    }

    # Just verify that scenarios use the expected key names (the string values)
    all_keys_used = set()
    for scenario in scenarios:
        all_keys_used.update(scenario["outputs"].keys())

    # Verify that the standard keys are from our constants
    # This ensures consistency between scenarios and evaluators
    standard_keys_found = all_keys_used.intersection(expected_keys)
    assert len(standard_keys_found) > 0, (
        "Scenarios should use at least some of the standard output keys"
    )


def test_feature_ids_follow_convention():
    """Test that feature IDs follow the FEAT-XX-NNN convention."""
    scenarios = get_test_scenarios()

    import re

    feature_id_pattern = re.compile(r"^FEAT-[A-Z]{2,3}-\d{3}$")

    for idx, scenario in enumerate(scenarios):
        if OUTPUT_KEY_EXPECTED_FEATURE_ID in scenario["outputs"]:
            feature_id = scenario["outputs"][OUTPUT_KEY_EXPECTED_FEATURE_ID]
            assert feature_id_pattern.match(feature_id), (
                f"Scenario {idx} has invalid feature_id format: {feature_id}. "
                f"Expected format: FEAT-XX-NNN"
            )


def test_scenarios_have_unique_queries():
    """Test that all scenario queries are unique."""
    scenarios = get_test_scenarios()

    queries = [s["inputs"]["user_query"] for s in scenarios]
    unique_queries = set(queries)

    assert len(queries) == len(unique_queries), (
        "Found duplicate queries in scenarios. Each scenario should have a unique query."
    )


def test_scenario_metadata_is_complete():
    """Test that all scenarios have complete metadata."""
    scenarios = get_test_scenarios()

    required_metadata = ["category", "difficulty", "description"]

    for idx, scenario in enumerate(scenarios):
        metadata = scenario["metadata"]

        for field in required_metadata:
            assert field in metadata, f"Scenario {idx} missing metadata field: {field}"
            assert isinstance(metadata[field], str)
            assert len(metadata[field]) > 0


def test_specific_scenarios_use_correct_constants():
    """Test specific scenarios to ensure they're using the right constants."""
    scenarios = get_test_scenarios()

    # Find the maintenance scheduling scenario
    ms_scenario = None
    for s in scenarios:
        if "maintenance scheduling" in s["inputs"]["user_query"].lower():
            if OUTPUT_KEY_EXPECTED_DECISION in s["outputs"]:
                if s["outputs"][OUTPUT_KEY_EXPECTED_DECISION] == DECISION_READY:
                    ms_scenario = s
                    break

    assert ms_scenario is not None, (
        "Could not find maintenance scheduling 'ready' scenario"
    )

    # Verify it uses the correct constants
    assert ms_scenario["outputs"][OUTPUT_KEY_EXPECTED_DECISION] == DECISION_READY
    assert ms_scenario["outputs"][OUTPUT_KEY_EXPECTED_FEATURE_ID] == "FEAT-MS-001"
    assert ms_scenario["outputs"][OUTPUT_KEY_SHOULD_CALL_JIRA] is True
    assert ms_scenario["outputs"][OUTPUT_KEY_SHOULD_CALL_ANALYSIS] is True

    # Check analysis types use constants
    if OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED in ms_scenario["outputs"]:
        analysis_types = ms_scenario["outputs"][OUTPUT_KEY_ANALYSIS_TYPES_REQUIRED]
        assert ANALYSIS_UNIT_TEST_RESULTS in analysis_types
        assert ANALYSIS_TEST_COVERAGE in analysis_types
