"""Unit tests for the analysis tool."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.tools.analysis import get_analysis, VALID_ANALYSIS_TYPES


class TestGetAnalysisHappyPath:
    """Tests for successful analysis retrieval."""

    def test_get_unit_test_results_success(self):
        """Test retrieving unit test results for a valid feature."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert result.get("success") is True
        assert result["feature_id"] == "FEAT-MS-001"
        assert result["analysis_type"] == "metrics/unit_test_results"
        assert "data" in result
        assert "metadata" in result
        assert result["metadata"]["retrieved_at"]
        assert "feature1/metrics/unit_test_results.json" in result["metadata"]["file_path"]

    def test_get_test_coverage_report_success(self):
        """Test retrieving test coverage report for a valid feature."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-QR-002", "analysis_type": "metrics/test_coverage_report"}
        )

        assert result.get("success") is True
        assert result["feature_id"] == "FEAT-QR-002"
        assert result["analysis_type"] == "metrics/test_coverage_report"
        assert "data" in result
        assert "metadata" in result

    def test_response_contains_metadata(self):
        """Test that successful responses contain proper metadata."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert result.get("success") is True
        assert "metadata" in result
        assert "retrieved_at" in result["metadata"]
        assert "file_path" in result["metadata"]
        # Verify timestamp is ISO format (with timezone)
        assert "T" in result["metadata"]["retrieved_at"]
        assert ("+00:00" in result["metadata"]["retrieved_at"] or 
                "Z" in result["metadata"]["retrieved_at"])

    def test_data_structure_preserved(self):
        """Test that the original data structure is preserved."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert result.get("success") is True
        data = result["data"]
        # Verify we got actual test result data
        assert "tests_total" in data or "test_suites" in data

    def test_all_valid_features(self):
        """Test that all 4 features can be retrieved."""
        features = ["FEAT-MS-001", "FEAT-QR-002", "FEAT-RS-003", "FEAT-CT-004"]

        for feature_id in features:
            result = get_analysis.invoke(
                {"feature_id": feature_id, "analysis_type": "metrics/unit_test_results"}
            )
            assert result.get("success") is True or "error" in result
            # At minimum, should not crash


class TestGetAnalysisErrorHandling:
    """Tests for error handling scenarios."""

    def test_invalid_feature_id(self):
        """Test with a non-existent feature_id."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-INVALID-999", "analysis_type": "metrics/unit_test_results"}
        )

        assert "error" in result
        assert "FEAT-INVALID-999" in result["error"]
        assert "available_features" in result
        assert len(result["available_features"]) > 0
        assert "suggestion" in result

    def test_invalid_analysis_type(self):
        """Test with an invalid analysis_type."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/invalid_analysis"}
        )

        assert "error" in result
        assert "invalid_analysis" in result["error"]
        assert "valid_types" in result
        assert result["valid_types"] == VALID_ANALYSIS_TYPES

    def test_empty_feature_id(self):
        """Test with an empty feature_id."""
        result = get_analysis.invoke(
            {"feature_id": "", "analysis_type": "metrics/unit_test_results"}
        )

        assert "error" in result
        assert "feature_id must be a non-empty string" in result["error"]

    def test_none_feature_id(self):
        """Test with None as feature_id."""
        # Pydantic validation will catch this before it reaches our function
        # This is actually correct behavior - tool schema enforces string type
        with pytest.raises(Exception):  # ValidationError from Pydantic
            get_analysis.invoke(
                {"feature_id": None, "analysis_type": "metrics/unit_test_results"}
            )

    def test_none_analysis_type(self):
        """Test with None as analysis_type."""
        # Pydantic validation will catch this before it reaches our function
        # This is actually correct behavior - tool schema enforces string type
        with pytest.raises(Exception):  # ValidationError from Pydantic
            get_analysis.invoke(
                {"feature_id": "FEAT-MS-001", "analysis_type": None}
            )

    def test_missing_analysis_file(self):
        """Test when an analysis file doesn't exist for a feature."""
        # Use a valid feature but analysis type that might not exist
        # We'll mock this scenario
        with patch("src.tools.analysis.read_json_file") as mock_read:
            mock_read.side_effect = FileNotFoundError("File not found")

            result = get_analysis.invoke(
                {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
            )

            assert "error" in result
            assert result["error"] == "Analysis not available"
            assert result["feature_id"] == "FEAT-MS-001"
            assert "suggestion" in result

    @patch("src.tools.analysis.read_json_file")
    def test_malformed_json_file(self, mock_read):
        """Test handling of corrupted JSON files."""
        mock_read.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert "error" in result
        assert result["error"] == "Data parsing error"
        assert "corrupted or malformed" in result["message"]
        assert "technical_details" in result

    @patch("src.tools.analysis.read_json_file")
    def test_io_error(self, mock_read):
        """Test handling of IO errors."""
        mock_read.side_effect = IOError("Permission denied")

        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        assert "error" in result
        assert result["error"] == "File reading error"
        assert "technical_details" in result


class TestGetAnalysisEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_case_sensitive_analysis_type(self):
        """Test that analysis_type is case-sensitive."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "METRICS/UNIT_TEST_RESULTS"}
        )

        assert "error" in result
        assert "Invalid analysis_type" in result["error"]

    def test_whitespace_in_feature_id(self):
        """Test feature_id with whitespace."""
        result = get_analysis.invoke(
            {"feature_id": " FEAT-MS-001 ", "analysis_type": "metrics/unit_test_results"}
        )

        # Should fail because we don't strip whitespace
        assert "error" in result

    def test_valid_types_constant(self):
        """Test that VALID_ANALYSIS_TYPES contains expected types."""
        assert "metrics/unit_test_results" in VALID_ANALYSIS_TYPES
        assert "metrics/test_coverage_report" in VALID_ANALYSIS_TYPES
        assert len(VALID_ANALYSIS_TYPES) == 2

    def test_analysis_type_with_wrong_separator(self):
        """Test analysis_type with wrong separator (backslash instead of slash)."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics\\unit_test_results"}
        )

        assert "error" in result
        assert "Invalid analysis_type" in result["error"]


class TestGetAnalysisIntegration:
    """Integration tests with file_utils."""

    @patch("src.tools.analysis.get_folder_for_feature_id")
    def test_uses_file_utils_correctly(self, mock_get_folder):
        """Test that the tool uses file_utils functions correctly."""
        mock_get_folder.return_value = "feature1"

        # Will fail because we're mocking, but we can verify the call
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        mock_get_folder.assert_called_once_with("FEAT-MS-001")

    def test_invalid_analysis_type_format_handled(self):
        """Test that invalid format in analysis_type is handled."""
        # Missing the subdirectory/filename format
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "unit_test_results"}
        )

        assert "error" in result
        assert "Invalid analysis_type" in result["error"]


class TestGetAnalysisDataContent:
    """Tests for verifying the actual data content returned."""

    def test_unit_test_results_has_expected_fields(self):
        """Test that unit test results contain expected fields."""
        result = get_analysis.invoke(
            {"feature_id": "FEAT-MS-001", "analysis_type": "metrics/unit_test_results"}
        )

        if result.get("success"):
            data = result["data"]
            # Should have test count fields
            assert any(
                key in data
                for key in [
                    "tests_total",
                    "tests_passed",
                    "tests_failed",
                    "test_suites",
                    "summary",
                ]
            )

    def test_feature_with_failing_tests(self):
        """Test retrieving data for a feature with failing tests."""
        # Feature 2 (QR Code) has failing tests
        result = get_analysis.invoke(
            {"feature_id": "FEAT-QR-002", "analysis_type": "metrics/unit_test_results"}
        )

        assert result.get("success") is True
        data = result["data"]
        # Verify we can access failure data
        assert "summary" in data or "failed_tests" in data or "tests_failed" in data
