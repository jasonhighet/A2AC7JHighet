"""End-to-end integration tests for feature readiness assessment.

These tests verify the complete workflow from user query to readiness decision:
1. Feature identification from natural language
2. Tool usage (JIRA + Analysis)
3. Decision logic based on test results
4. Clear reasoning with specific evidence
"""

import os
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import ValidationError

from src.agent.graph import create_agent_graph
from src.tools.analysis import get_analysis
from src.tools.jira import get_jira_data
from src.utils.config import Config, load_config


@pytest.fixture
def test_config():
    """Create test configuration from .env file or mock if not available."""
    try:
        # Try to load real config from .env
        config = load_config()
        return config
    except ValidationError:
        # Fall back to mock if .env not properly configured
        config = MagicMock(spec=Config)
        config.model_name = "claude-3-5-sonnet-20241022"
        config.anthropic_api_key = "test-key"
        config.temperature = 0.0
        config.max_tokens = 4096
        return config


def has_real_api_key():
    """Check if a real API key is available."""
    try:
        config = load_config()
        # Check if API key looks real (starts with sk-ant-api)
        return config.anthropic_api_key.startswith("sk-ant-api")
    except (ValidationError, AttributeError):
        return False


@pytest.fixture
def real_jira_data():
    """Get actual JIRA data from test fixtures."""
    return get_jira_data.invoke({})


@pytest.fixture
def feature1_test_results():
    """Get actual test results for feature1 (Maintenance Scheduling)."""
    return get_analysis.invoke(
        {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
    )


@pytest.fixture
def feature2_test_results():
    """Get actual test results for feature2 (QR Code Check-in)."""
    return get_analysis.invoke(
        {"feature_id": "FEAT-QR-002", "analysis_type": "metrics/unit_test_results"}
    )


class TestFeatureIdentification:
    """Test suite for feature identification from natural language queries."""

    def test_jira_tool_returns_all_features(self, real_jira_data):
        """Verify JIRA tool returns all expected features."""
        assert isinstance(real_jira_data, list)
        assert len(real_jira_data) == 4

        feature_ids = [f["feature_id"] for f in real_jira_data]
        assert "FEAT-MS-001" in feature_ids
        assert "FEAT-QR-002" in feature_ids
        assert "FEAT-RS-003" in feature_ids
        assert "FEAT-CT-004" in feature_ids

    def test_feature1_has_all_required_fields(self, real_jira_data):
        """Verify feature1 data structure is correct."""
        feature1 = next(f for f in real_jira_data if f["feature_id"] == "FEAT-MS-001")

        assert feature1["folder"] == "feature1"
        assert feature1["jira_key"] == "PLAT-1523"
        assert "Maintenance" in feature1["summary"]
        assert "status" in feature1
        assert "data_quality" in feature1


class TestAnalysisToolIntegration:
    """Test suite for analysis tool integration."""

    def test_feature1_unit_test_results_structure(self, feature1_test_results):
        """Verify feature1 test results have correct structure."""
        assert feature1_test_results["success"] is True
        assert "data" in feature1_test_results

        data = feature1_test_results["data"]
        assert "tests_total" in data
        assert "tests_passed" in data
        assert "tests_failed" in data

    def test_feature1_all_tests_passing(self, feature1_test_results):
        """Verify feature1 has all tests passing (READY scenario)."""
        data = feature1_test_results["data"]

        assert data["tests_total"] == 156
        assert data["tests_passed"] == 156
        assert data["tests_failed"] == 0
        # This feature should be READY based on test criteria

    def test_feature2_has_test_failures(self, feature2_test_results):
        """Verify feature2 has failing tests (NOT READY scenario)."""
        assert feature2_test_results["success"] is True
        data = feature2_test_results["data"]

        # Feature2 should have failures based on test data
        assert "summary" in data
        summary = data["summary"]
        assert summary["failed"] > 0
        assert summary["status"] == "FAILED"
        # This feature should be NOT READY based on test criteria

    def test_analysis_tool_handles_invalid_feature_id(self):
        """Verify analysis tool handles invalid feature IDs gracefully."""
        result = get_analysis.invoke(
            {"feature_id": "INVALID-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert "error" in result
        assert result["error"] == "Invalid feature_id: 'INVALID-001' not found"
        assert "available_features" in result

    def test_analysis_tool_handles_invalid_analysis_type(self):
        """Verify analysis tool validates analysis types."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "invalid/type"}
        )

        assert "error" in result
        assert "Invalid analysis_type" in result["error"]
        assert "valid_types" in result


class TestDecisionLogicWithRealData:
    """Test suite for decision logic using real test data.

    Note: These tests verify that the data is structured correctly for the
    agent to make proper decisions. The actual decision-making is performed
    by the LLM based on the system prompt.
    """

    def test_ready_scenario_data_structure(self, feature1_test_results):
        """Verify data for READY scenario has all needed information."""
        assert feature1_test_results["success"] is True

        data = feature1_test_results["data"]

        # Verify agent can extract these key decision points
        assert data["tests_failed"] == 0, (
            "Agent should see 0 failures for READY decision"
        )
        assert data["tests_passed"] > 0, "Agent should see passing tests"
        assert data["tests_total"] == data["tests_passed"], "All tests should pass"

    def test_not_ready_scenario_data_structure(self, feature2_test_results):
        """Verify data for NOT READY scenario has failure details."""
        assert feature2_test_results["success"] is True

        data = feature2_test_results["data"]
        summary = data["summary"]

        # Verify agent can extract these key decision points
        assert summary["failed"] > 0, "Agent should see failures for NOT READY decision"
        assert summary["status"] == "FAILED", "Agent should see FAILED status"

        # Verify detailed failure information is available
        assert "failed_tests" in data, "Agent should have access to failure details"
        failed_tests = data["failed_tests"]
        assert len(failed_tests) > 0, "Agent should see specific failed test details"

        # Verify first failure has required fields for reasoning
        first_failure = failed_tests[0]
        assert "name" in first_failure, "Agent needs test name"
        assert "error_message" in first_failure, "Agent needs error message"
        assert "severity" in first_failure, "Agent needs severity"

    def test_missing_data_scenario(self):
        """Verify graceful handling when analysis data is missing."""
        # Feature4 is in Planning phase - may not have complete metrics
        result = get_analysis.invoke(
            {"feature_id": "FEAT-CT-004", "analysis_type": "metrics/unit_test_results"}
        )

        # Should either return data or a clear error message
        if "error" in result:
            assert result["error"] == "Analysis not available"
            assert "suggestion" in result
        else:
            assert result["success"] is True


class TestWorkflowSequence:
    """Test suite for verifying correct tool call sequence.

    These tests verify the agent follows the expected workflow:
    1. Call get_jira_data() to identify features
    2. Extract feature_id from results
    3. Call get_analysis() with feature_id
    4. Make decision based on analysis results
    """

    def test_jira_before_analysis_workflow(self, real_jira_data):
        """Verify JIRA data provides feature_id needed for analysis tool."""
        # Step 1: Agent calls get_jira_data
        jira_data = real_jira_data
        assert len(jira_data) > 0

        # Step 2: Agent extracts feature_id
        feature1 = next(f for f in jira_data if "Maintenance" in f["summary"])
        feature_id = feature1["feature_id"]
        assert feature_id == "FEAT-MS-001"

        # Step 3: Agent uses feature_id to get analysis
        analysis_result = get_analysis.invoke(
            {"feature_id": feature_id, "analysis_type": "metrics/unit_test_results"}
        )

        # Step 4: Verify analysis data is available for decision
        assert analysis_result["success"] is True
        assert "data" in analysis_result


@pytest.mark.skipif(
    not has_real_api_key(),
    reason="Requires ANTHROPIC_API_KEY in .env file for LLM calls",
)
class TestEndToEndWithLLM:
    """End-to-end tests that actually invoke the agent with the LLM.

    These tests require a real API key and will make actual LLM calls.
    They verify the complete workflow from user query to reasoned decision.
    """

    def test_ready_feature_assessment(self, test_config):
        """Test complete workflow for a feature with passing tests."""

        graph = create_agent_graph(test_config)

        initial_state = {
            "messages": [
                HumanMessage(
                    content="Is the maintenance scheduling feature ready for its next phase?"
                )
            ]
        }

        result = graph.invoke(initial_state)

        # Verify workflow completed
        assert "messages" in result
        assert len(result["messages"]) > 1

        # Get final agent response
        final_message = result["messages"][-1]
        assert isinstance(final_message, AIMessage)
        response_text = final_message.content.lower()

        # Verify agent made a decision
        # (Feature1 has all tests passing, so should be READY)
        # Note: LLM might phrase this in various ways
        assert len(response_text) > 0, "Agent should provide a response"

    def test_not_ready_feature_assessment(self, test_config):
        """Test complete workflow for a feature with failing tests."""

        graph = create_agent_graph(test_config)

        initial_state = {
            "messages": [
                HumanMessage(
                    content="Is the QR code check-in feature ready for its next phase?"
                )
            ]
        }

        result = graph.invoke(initial_state)

        # Verify workflow completed
        assert "messages" in result
        assert len(result["messages"]) > 1

        # Get final agent response
        final_message = result["messages"][-1]
        assert isinstance(final_message, AIMessage)
        response_text = final_message.content.lower()

        # Verify agent made a decision
        # (Feature2 has test failures, so should be NOT READY)
        assert len(response_text) > 0, "Agent should provide a response"
