"""
Unit tests for file_utils module.
"""

import json
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.utils.file_utils import (
    get_analysis_file_path,
    get_feature_folder_mapping,
    get_folder_for_feature_id,
    get_jira_file_path,
    list_available_features,
    read_json_file,
)


@pytest.fixture
def mock_incoming_data_dir(tmp_path):
    """Create a temporary incoming_data directory with mock feature folders."""
    # Create feature folders
    feature1 = tmp_path / "feature1"
    feature2 = tmp_path / "feature2"
    feature3 = tmp_path / "feature_invalid"  # No JIRA file

    feature1.mkdir()
    feature2.mkdir()
    feature3.mkdir()

    # Create JIRA files with mock data
    jira1 = feature1 / "jira"
    jira1.mkdir()
    (jira1 / "feature_issue.json").write_text(
        json.dumps(
            {
                "key": "TEST-001",
                "fields": {
                    "customfield_10001": "FEAT-TEST-001",
                    "summary": "Test Feature 1",
                    "status": {"name": "In Progress"},
                },
            }
        )
    )

    jira2 = feature2 / "jira"
    jira2.mkdir()
    (jira2 / "feature_issue.json").write_text(
        json.dumps(
            {
                "key": "TEST-002",
                "fields": {
                    "customfield_10001": "FEAT-TEST-002",
                    "summary": "Test Feature 2",
                    "status": {"name": "Done"},
                },
            }
        )
    )

    # feature3 has no JIRA file (to test skipping)

    return tmp_path


class TestGetFeatureFolderMapping:
    """Tests for get_feature_folder_mapping function."""

    def test_returns_dict_type(self, mock_incoming_data_dir):
        """Test that function returns a dictionary."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            mapping = get_feature_folder_mapping()
            assert isinstance(mapping, dict)

    def test_maps_feature_id_to_folder_name(self, mock_incoming_data_dir):
        """Test that feature IDs are correctly mapped to folder names."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            mapping = get_feature_folder_mapping()

            # Should map feature_id -> folder name
            assert "FEAT-TEST-001" in mapping
            assert mapping["FEAT-TEST-001"] == "feature1"
            assert "FEAT-TEST-002" in mapping
            assert mapping["FEAT-TEST-002"] == "feature2"

    def test_skips_folders_without_jira_files(self, mock_incoming_data_dir):
        """Test that folders without JIRA files are skipped."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            mapping = get_feature_folder_mapping()

            # feature_invalid has no JIRA file, should not be in mapping
            # Only 2 features with valid JIRA files
            assert len(mapping) == 2
            assert all(
                folder in ["feature1", "feature2"] for folder in mapping.values()
            )

    def test_skips_folders_without_feature_prefix(self, tmp_path):
        """Test that non-feature folders are ignored."""
        # Create folders without 'feature' prefix
        (tmp_path / "other_folder").mkdir()
        (tmp_path / "random_dir").mkdir()

        feature1 = tmp_path / "feature1"
        feature1.mkdir()
        jira1 = feature1 / "jira"
        jira1.mkdir()
        (jira1 / "feature_issue.json").write_text(
            json.dumps({"fields": {"customfield_10001": "FEAT-001"}})
        )

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            mapping = get_feature_folder_mapping()

            # Only feature1 should be in mapping
            assert len(mapping) == 1
            assert "FEAT-001" in mapping

    def test_returns_empty_dict_when_directory_does_not_exist(self):
        """Test graceful handling when incoming_data directory doesn't exist."""
        non_existent_path = Path("/nonexistent/path/that/does/not/exist")
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", non_existent_path):
            mapping = get_feature_folder_mapping()
            assert mapping == {}

    def test_handles_malformed_jira_json_gracefully(self, tmp_path):
        """Test that malformed JSON files are skipped without crashing."""
        feature1 = tmp_path / "feature1"
        feature1.mkdir()
        jira1 = feature1 / "jira"
        jira1.mkdir()

        # Write malformed JSON
        (jira1 / "feature_issue.json").write_text("{ invalid json }")

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            mapping = get_feature_folder_mapping()

            # Should return empty dict, not crash
            assert mapping == {}

    def test_handles_missing_customfield_gracefully(self, tmp_path):
        """Test that JIRA files without customfield_10001 are skipped."""
        feature1 = tmp_path / "feature1"
        feature1.mkdir()
        jira1 = feature1 / "jira"
        jira1.mkdir()

        # JIRA file without customfield_10001
        (jira1 / "feature_issue.json").write_text(
            json.dumps({"key": "TEST-001", "fields": {}})
        )

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            mapping = get_feature_folder_mapping()

            # Should skip this feature
            assert len(mapping) == 0


class TestGetFolderForFeatureId:
    """Tests for get_folder_for_feature_id function."""

    def test_returns_folder_name_for_valid_feature_id(self, mock_incoming_data_dir):
        """Test that valid feature IDs return folder names."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            folder = get_folder_for_feature_id("FEAT-TEST-001")
            assert folder == "feature1"

    def test_returns_none_for_invalid_feature_id(self, mock_incoming_data_dir):
        """Test that invalid feature IDs return None."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            assert get_folder_for_feature_id("FEAT-NONEXISTENT") is None
            assert get_folder_for_feature_id("") is None
            assert get_folder_for_feature_id("invalid") is None

    def test_calls_get_feature_folder_mapping(self, mock_incoming_data_dir):
        """Test that function uses get_feature_folder_mapping."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            with patch(
                "src.utils.file_utils.get_feature_folder_mapping",
                return_value={"FEAT-123": "folder123"},
            ) as mock_mapping:
                result = get_folder_for_feature_id("FEAT-123")

                mock_mapping.assert_called_once()
                assert result == "folder123"


class TestReadJsonFile:
    """Tests for read_json_file function."""

    def test_reads_and_parses_valid_json(self, tmp_path):
        """Test reading a valid JSON file."""
        json_file = tmp_path / "test.json"
        test_data = {"key": "value", "number": 42, "nested": {"field": "data"}}
        json_file.write_text(json.dumps(test_data))

        result = read_json_file(json_file)

        assert result == test_data
        assert isinstance(result, dict)

    def test_raises_file_not_found_error_for_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        non_existent_file = Path("/nonexistent/file.json")

        with pytest.raises(FileNotFoundError, match="File not found"):
            read_json_file(non_existent_file)

    def test_raises_json_decode_error_for_malformed_json(self):
        """Test that JSONDecodeError is raised for malformed JSON."""
        mock_file_content = "{ invalid json content"

        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(json.JSONDecodeError):
                    read_json_file(Path("/fake/path.json"))

    def test_opens_file_with_utf8_encoding(self, tmp_path):
        """Test that file is opened with UTF-8 encoding."""
        json_file = tmp_path / "test.json"
        test_data = {"text": "café"}  # Non-ASCII character
        json_file.write_text(json.dumps(test_data), encoding="utf-8")

        result = read_json_file(json_file)

        assert result["text"] == "café"


class TestGetJiraFilePath:
    """Tests for get_jira_file_path function."""

    def test_returns_path_object(self):
        """Test that function returns a Path object."""
        path = get_jira_file_path("feature1")
        assert isinstance(path, Path)

    def test_path_structure_is_correct(self):
        """Test that path follows expected structure."""
        path = get_jira_file_path("test_feature")

        # Path should end with: test_feature/jira/feature_issue.json
        assert path.name == "feature_issue.json"
        assert path.parent.name == "jira"
        assert path.parent.parent.name == "test_feature"

    def test_different_folder_names_produce_different_paths(self):
        """Test that different folder names produce different paths."""
        path1 = get_jira_file_path("feature1")
        path2 = get_jira_file_path("feature2")

        assert path1 != path2
        assert "feature1" in str(path1)
        assert "feature2" in str(path2)


class TestGetAnalysisFilePath:
    """Tests for get_analysis_file_path function."""

    def test_returns_path_object(self):
        """Test that function returns a Path object."""
        path = get_analysis_file_path("feature1", "metrics/unit_test_results")
        assert isinstance(path, Path)

    def test_constructs_correct_path_structure_for_metrics(self):
        """Test path structure for metrics analysis type."""
        path = get_analysis_file_path("test_feature", "metrics/test_coverage")

        assert path.name == "test_coverage.json"
        assert path.parent.name == "metrics"
        assert path.parent.parent.name == "test_feature"

    def test_constructs_correct_path_structure_for_reviews(self):
        """Test path structure for reviews analysis type."""
        path = get_analysis_file_path("test_feature", "reviews/security")

        assert path.name == "security.json"
        assert path.parent.name == "reviews"
        assert path.parent.parent.name == "test_feature"

    def test_appends_json_extension(self):
        """Test that .json extension is added to filename."""
        path = get_analysis_file_path("feature1", "metrics/performance")
        assert path.suffix == ".json"
        assert path.name == "performance.json"

    def test_raises_error_for_invalid_analysis_type_format(self):
        """Test that ValueError is raised for invalid analysis_type format."""
        with pytest.raises(ValueError, match="Invalid analysis_type format"):
            get_analysis_file_path("feature1", "invalid_format")

        with pytest.raises(ValueError, match="Invalid analysis_type format"):
            get_analysis_file_path("feature1", "too/many/slashes/here")

        with pytest.raises(ValueError, match="Invalid analysis_type format"):
            get_analysis_file_path("feature1", "")

    def test_different_analysis_types_produce_different_paths(self):
        """Test that different analysis types produce different paths."""
        path1 = get_analysis_file_path("feature1", "metrics/unit_tests")
        path2 = get_analysis_file_path("feature1", "reviews/security")

        assert path1 != path2
        assert "metrics" in str(path1)
        assert "reviews" in str(path2)


class TestListAvailableFeatures:
    """Tests for list_available_features function."""

    def test_returns_list_type(self, mock_incoming_data_dir):
        """Test that function returns a list."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            features = list_available_features()
            assert isinstance(features, list)

    def test_each_feature_is_dict_with_required_fields(self, mock_incoming_data_dir):
        """Test that each feature has all required fields."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            features = list_available_features()

            required_fields = ["feature_id", "folder", "jira_key", "summary", "status"]

            for feature in features:
                assert isinstance(feature, dict)
                for field in required_fields:
                    assert field in feature
                    assert feature[field]  # Not empty

    def test_extracts_data_from_jira_files(self, mock_incoming_data_dir):
        """Test that function extracts correct data from JIRA files."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            features = list_available_features()

            # Find feature1
            feature1 = next(f for f in features if f["folder"] == "feature1")
            assert feature1["feature_id"] == "FEAT-TEST-001"
            assert feature1["jira_key"] == "TEST-001"
            assert feature1["summary"] == "Test Feature 1"
            assert feature1["status"] == "In Progress"

    def test_skips_folders_without_jira_files(self, mock_incoming_data_dir):
        """Test that folders without JIRA files are skipped."""
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", mock_incoming_data_dir):
            features = list_available_features()

            # Only 2 features have valid JIRA files
            assert len(features) == 2
            folder_names = [f["folder"] for f in features]
            assert "feature_invalid" not in folder_names

    def test_skips_features_without_required_fields(self, tmp_path):
        """Test that features without required fields are skipped."""
        feature1 = tmp_path / "feature1"
        feature1.mkdir()
        jira1 = feature1 / "jira"
        jira1.mkdir()

        # Missing customfield_10001
        (jira1 / "feature_issue.json").write_text(
            json.dumps({"fields": {"summary": "Test"}})
        )

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            features = list_available_features()

            # Should be skipped
            assert len(features) == 0

    def test_returns_empty_list_when_directory_does_not_exist(self):
        """Test graceful handling when incoming_data directory doesn't exist."""
        non_existent_path = Path("/nonexistent/path")
        with patch("src.utils.file_utils.INCOMING_DATA_DIR", non_existent_path):
            features = list_available_features()
            assert features == []

    def test_features_are_sorted_by_folder_name(self, tmp_path):
        """Test that features are returned in sorted order by folder."""
        # Create folders in non-sorted order
        for folder_name in ["feature3", "feature1", "feature2"]:
            folder = tmp_path / folder_name
            folder.mkdir()
            jira = folder / "jira"
            jira.mkdir()
            (jira / "feature_issue.json").write_text(
                json.dumps(
                    {
                        "key": f"TEST-{folder_name}",
                        "fields": {
                            "customfield_10001": f"FEAT-{folder_name}",
                            "summary": f"Feature {folder_name}",
                            "status": {"name": "Done"},
                        },
                    }
                )
            )

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            features = list_available_features()

            folder_names = [f["folder"] for f in features]
            assert folder_names == sorted(folder_names)

    def test_handles_malformed_json_gracefully(self, tmp_path):
        """Test that malformed JSON files are skipped without crashing."""
        feature1 = tmp_path / "feature1"
        feature1.mkdir()
        jira1 = feature1 / "jira"
        jira1.mkdir()
        (jira1 / "feature_issue.json").write_text("{ malformed json")

        feature2 = tmp_path / "feature2"
        feature2.mkdir()
        jira2 = feature2 / "jira"
        jira2.mkdir()
        (jira2 / "feature_issue.json").write_text(
            json.dumps(
                {
                    "key": "TEST-002",
                    "fields": {
                        "customfield_10001": "FEAT-002",
                        "summary": "Valid Feature",
                        "status": {"name": "Done"},
                    },
                }
            )
        )

        with patch("src.utils.file_utils.INCOMING_DATA_DIR", tmp_path):
            features = list_available_features()

            # Should only return feature2 (valid JSON)
            assert len(features) == 1
            assert features[0]["folder"] == "feature2"
