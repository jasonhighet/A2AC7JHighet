"""Unit tests for JIRA tool.

Tests verify that the get_jira_data tool correctly retrieves and formats
feature metadata from JIRA issue files.
"""

import json
from unittest.mock import patch

from src.tools.jira import get_jira_data


class TestGetJiraData:
    """Test suite for get_jira_data tool."""

    def test_get_jira_data_returns_all_features(self):
        """Test that get_jira_data returns all 4 features from test data."""
        result = get_jira_data.invoke({})

        # Should have 4 features
        assert isinstance(result, list)
        assert len(result) == 4

        # Verify each result has required fields
        for feature in result:
            assert "folder" in feature
            assert "jira_key" in feature
            assert "feature_id" in feature
            assert "summary" in feature
            assert "status" in feature
            assert "data_quality" in feature

            # Verify types
            assert isinstance(feature["folder"], str)
            assert isinstance(feature["jira_key"], str)
            assert isinstance(feature["feature_id"], str)
            assert isinstance(feature["summary"], str)
            assert isinstance(feature["status"], str)
            assert isinstance(feature["data_quality"], str)

    def test_get_jira_data_correct_feature_ids(self):
        """Test that feature_ids are correctly extracted."""
        result = get_jira_data.invoke({})

        feature_ids = [f["feature_id"] for f in result]

        # Verify we have the expected feature IDs
        assert "FEAT-MS-001" in feature_ids  # Maintenance Scheduling
        assert "FEAT-QR-002" in feature_ids  # QR Code Check-in

    def test_get_jira_data_correct_statuses(self):
        """Test that statuses are correctly extracted."""
        result = get_jira_data.invoke({})

        # Find specific features and verify their status
        ms_feature = next((f for f in result if f["feature_id"] == "FEAT-MS-001"), None)
        assert ms_feature is not None
        assert ms_feature["status"] == "Production Ready"

        qr_feature = next((f for f in result if f["feature_id"] == "FEAT-QR-002"), None)
        assert qr_feature is not None
        assert qr_feature["status"] == "Development"

    def test_get_jira_data_includes_data_quality(self):
        """Test that data_quality field is included and valid."""
        result = get_jira_data.invoke({})

        for feature in result:
            assert "data_quality" in feature
            # Should be one of the expected values
            assert feature["data_quality"] in ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]

    def test_get_jira_data_folder_mapping(self):
        """Test that folder names are correctly mapped to feature IDs."""
        result = get_jira_data.invoke({})

        # Verify folder names are valid
        folders = [f["folder"] for f in result]
        assert "feature1" in folders
        assert "feature2" in folders

        # Verify folder names start with 'feature'
        for folder in folders:
            assert folder.startswith("feature")

    def test_get_jira_data_summaries_not_empty(self):
        """Test that summaries are not empty."""
        result = get_jira_data.invoke({})

        for feature in result:
            assert feature["summary"] != ""
            assert len(feature["summary"]) > 0

    def test_get_jira_data_jira_keys_format(self):
        """Test that JIRA keys follow the expected format."""
        result = get_jira_data.invoke({})

        for feature in result:
            # JIRA keys should follow pattern: PROJECT-####
            assert "-" in feature["jira_key"], "JIRA key should contain a hyphen"
            parts = feature["jira_key"].split("-")
            assert len(parts) == 2, "JIRA key should have format: PROJECT-NUMBER"
            # Project code should be uppercase letters
            assert parts[0].isupper(), "Project code should be uppercase"
            assert parts[0].isalpha(), "Project code should be letters only"
            # Number should be numeric
            assert parts[1].isdigit(), "Issue number should be numeric"

    @patch("src.tools.jira.list_available_features")
    def test_get_jira_data_handles_empty_directory(self, mock_list_features):
        """Test that tool handles empty data/incoming directory gracefully."""
        mock_list_features.return_value = []

        result = get_jira_data.invoke({})

        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["error"] == "No features found"

    @patch("src.tools.jira.list_available_features")
    def test_get_jira_data_handles_exception(self, mock_list_features):
        """Test that tool handles exceptions gracefully."""
        mock_list_features.side_effect = Exception("Test error")

        result = get_jira_data.invoke({})

        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]
        assert result[0]["error"] == "Failed to retrieve JIRA data"
        assert "Test error" in result[0]["message"]

    @patch("src.tools.jira.read_json_file")
    @patch("src.tools.jira.list_available_features")
    def test_get_jira_data_handles_malformed_json_gracefully(
        self, mock_list_features, mock_read_json
    ):
        """Test that tool handles malformed JSON files gracefully."""
        # Mock list_available_features to return one feature
        mock_list_features.return_value = [
            {
                "feature_id": "FEAT-TEST-001",
                "folder": "feature_test",
                "jira_key": "PLAT-9999",
                "summary": "Test Feature",
                "status": "Development",
            }
        ]

        # Mock read_json_file to raise JSONDecodeError
        mock_read_json.side_effect = json.JSONDecodeError("Expecting value", "", 0)

        result = get_jira_data.invoke({})

        # Should still return the feature, but with UNKNOWN data_quality and error
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["feature_id"] == "FEAT-TEST-001"
        assert result[0]["data_quality"] == "UNKNOWN"
        assert "error" in result[0]

    def test_get_jira_data_tool_metadata(self):
        """Test that the tool has proper metadata."""
        assert get_jira_data.name == "get_jira_data"
        assert get_jira_data.description is not None
        assert len(get_jira_data.description) > 0
        assert (
            "JIRA" in get_jira_data.description
            or "feature" in get_jira_data.description.lower()
        )

    def test_get_jira_data_is_callable(self):
        """Test that the tool can be invoked."""
        # Tool should be callable via invoke method
        result = get_jira_data.invoke({})
        assert result is not None
        assert isinstance(result, list)

    def test_get_jira_data_consistency(self):
        """Test that calling the tool multiple times returns consistent results."""
        result1 = get_jira_data.invoke({})
        result2 = get_jira_data.invoke({})

        # Results should be identical
        assert len(result1) == len(result2)

        # Sort by feature_id for comparison
        sorted_result1 = sorted(result1, key=lambda x: x.get("feature_id", ""))
        sorted_result2 = sorted(result2, key=lambda x: x.get("feature_id", ""))

        for f1, f2 in zip(sorted_result1, sorted_result2):
            assert f1["feature_id"] == f2["feature_id"]
            assert f1["jira_key"] == f2["jira_key"]
            assert f1["summary"] == f2["summary"]
            assert f1["status"] == f2["status"]

    def test_get_jira_data_feature_ids_unique(self):
        """Test that all feature IDs are unique."""
        result = get_jira_data.invoke({})

        feature_ids = [f["feature_id"] for f in result]
        unique_feature_ids = set(feature_ids)

        assert len(feature_ids) == len(unique_feature_ids), (
            "Feature IDs should be unique"
        )

    def test_get_jira_data_jira_keys_unique(self):
        """Test that all JIRA keys are unique."""
        result = get_jira_data.invoke({})

        jira_keys = [f["jira_key"] for f in result]
        unique_jira_keys = set(jira_keys)

        assert len(jira_keys) == len(unique_jira_keys), "JIRA keys should be unique"

    def test_get_jira_data_retries_on_file_error(self):
        """Test that JIRA tool retries on transient file errors (Step 5.3)."""

        call_count = 0

        def mock_list_features_with_retry():
            """Mock that fails twice then succeeds."""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise FileNotFoundError("Temporary file error")
            # On third attempt, return valid data
            return [
                {
                    "folder": "feature1",
                    "jira_key": "TEST-001",
                    "feature_id": "FEAT-TEST-001",
                    "summary": "Test Feature",
                    "status": "Development",
                }
            ]

        # Patch the internal function that reads files
        with patch(
            "src.tools.jira.list_available_features",
            side_effect=mock_list_features_with_retry,
        ):
            # Mock read_json_file to return valid JIRA data
            with patch("src.tools.jira.read_json_file") as mock_read_json:
                mock_read_json.return_value = {"fields": {"customfield_10002": "HIGH"}}

                result = get_jira_data.invoke({})

        # Verify retry happened (3 calls total)
        assert call_count == 3, f"Expected 3 retry attempts, got {call_count}"

        # Verify success after retries
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["feature_id"] == "FEAT-TEST-001"

    def test_get_jira_data_fails_gracefully_after_max_retries(self):
        """Test that JIRA tool fails gracefully after exhausting retries (Step 5.3)."""

        def mock_list_features_always_fails():
            """Mock that always raises an error."""
            raise PermissionError("Persistent permission error")

        # Patch to always fail
        with patch(
            "src.tools.jira.list_available_features",
            side_effect=mock_list_features_always_fails,
        ):
            result = get_jira_data.invoke({})

        # Verify graceful error handling
        assert isinstance(result, list)
        assert len(result) == 1
        assert "error" in result[0]
        assert "Failed to retrieve JIRA data" in result[0]["error"]
        assert "retry" in result[0]["details"].lower()
