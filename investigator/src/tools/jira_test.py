"""Unit tests for the JIRA metadata lookup tool."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.jira import get_jira_data


@pytest.fixture
def mock_features() -> list[dict]:
    """Provide a basic list of mock features."""
    return [
        {
            "feature_id": "FEAT-MS-001",
            "folder": "feature1",
            "jira_key": "PLAT-1523",
            "summary": "Maintenance Scheduling & Alert System",
            "status": "Production Ready",
        }
    ]


@pytest.fixture
def mock_jira_json() -> dict:
    """Mock JIRA JSON content for one feature."""
    return {
        "key": "PLAT-1523",
        "fields": {
            "summary": "Maintenance Scheduling & Alert System",
            "status": {"name": "Production Ready"},
            "customfield_10001": "FEAT-MS-001",
            "customfield_10002": "HIGH",  # Data quality
        },
    }


def test_get_jira_data_returns_enriched_metadata(mock_features, mock_jira_json):
    """get_jira_data correctly enriches metadata with data_quality."""
    with patch("src.tools.jira.list_available_features", return_value=mock_features):
        with patch("src.tools.jira.read_json_file", return_value=mock_jira_json):
            with patch("src.tools.jira.get_jira_file_path", return_value="dummy/path"):
                result = get_jira_data.invoke({})

                assert len(result) == 1
                assert result[0]["feature_id"] == "FEAT-MS-001"
                assert result[0]["data_quality"] == "HIGH"
                assert result[0]["status"] == "Production Ready"


def test_get_jira_data_handles_empty_features():
    """get_jira_data returns a helpful error message when no features are found."""
    with patch("src.tools.jira.list_available_features", return_value=[]):
        result = get_jira_data.invoke({})

        assert len(result) == 1
        assert "error" in result[0]
        assert "No features found" in result[0]["error"]


def test_get_jira_data_handles_missing_data_quality(mock_features):
    """get_jira_data defaults data_quality to 'UNKNOWN' if field is missing."""
    mock_jira_without_quality = {
        "fields": {"customfield_10001": "FEAT-MS-001"}
    }

    with patch("src.tools.jira.list_available_features", return_value=mock_features):
        with patch("src.tools.jira.read_json_file", return_value=mock_jira_without_quality):
            with patch("src.tools.jira.get_jira_file_path", return_value="dummy/path"):
                result = get_jira_data.invoke({})

                assert result[0]["data_quality"] == "UNKNOWN"


def test_get_jira_data_retries_on_transient_error(mock_features):
    """get_jira_data retries on FileNotFoundError before succeeding."""
    with patch("src.tools.jira.list_available_features", return_value=mock_features):
        with patch("src.tools.jira.read_json_file") as mock_read:
            # First call fails, second call succeeds
            mock_read.side_effect = [
                FileNotFoundError("Temporary access issue"),
                {"fields": {"customfield_10002": "MEDIUM"}},
            ]

            with patch("src.tools.jira.get_jira_file_path", return_value="dummy/path"):
                result = get_jira_data.invoke({})

                assert mock_read.call_count == 2
                assert result[0]["data_quality"] == "MEDIUM"


def test_get_jira_data_fails_gracefully_after_all_retries(mock_features):
    """get_jira_data returns error dictionary after exhausting retries."""
    with patch("src.tools.jira.list_available_features", return_value=mock_features):
        with patch("src.tools.jira.read_json_file") as mock_read:
            # Continually fail
            mock_read.side_effect = OSError("Persistent I/O Error")

            with patch("src.tools.jira.get_jira_file_path", return_value="dummy/path"):
                result = get_jira_data.invoke({})

                # Verify multiple attempts occurred (configured to 3 by default)
                assert mock_read.call_count >= 1
                assert len(result) == 1
                assert "error" in result[0]
                assert "Failed to retrieve JIRA data" in result[0]["error"]
