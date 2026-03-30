"""Unit tests for the analysis metrics lookup tool."""

from unittest.mock import MagicMock, patch

import pytest

from src.tools.analysis import get_analysis


@pytest.fixture
def mock_unit_test_json() -> dict:
    """Mock unit test results JSON."""
    return {
        "summary": {
            "total": 100,
            "passed": 100,
            "failed": 0,
            "skipped": 0,
        },
        "details": [
            {"name": "test_payment_gateway", "status": "passed"},
            {"name": "test_user_auth", "status": "passed"},
        ],
    }


def test_get_analysis_returns_metrics(mock_unit_test_json):
    """get_analysis correctly retrieves and returns JSON metrics."""
    with patch("src.tools.analysis.get_feature_folder", return_value="feature1"):
        with patch("src.tools.analysis.read_json_file", return_value=mock_unit_test_json):
            result = get_analysis.invoke({
                "feature_id": "FEAT-123",
                "analysis_type": "metrics/unit_test_results"
            })

            assert result["summary"]["total"] == 100
            assert result["summary"]["failed"] == 0


def test_get_analysis_handles_non_existent_feature():
    """get_analysis returns a clear error message for unknown features."""
    with patch("src.tools.analysis.get_feature_folder", return_value=None):
        result = get_analysis.invoke({
            "feature_id": "UNKNOWN",
            "analysis_type": "metrics/unit_test_results"
        })

        assert "error" in result
        assert "Data unavailable" in result["error"]
        assert "UNKNOWN" in result["message"]


def test_get_analysis_retries_on_transient_error(mock_unit_test_json):
    """get_analysis retries on OSError before succeeding."""
    with patch("src.tools.analysis.get_feature_folder", return_value="feature1"):
        with patch("src.tools.analysis.read_json_file") as mock_read:
            # First call fails, second call succeeds
            mock_read.side_effect = [
                OSError("Locked file"),
                mock_unit_test_json,
            ]

            result = get_analysis.invoke({
                "feature_id": "FEAT-123",
                "analysis_type": "metrics/unit_test_results"
            })

            assert mock_read.call_count == 2
            assert result["summary"]["total"] == 100


def test_get_analysis_fails_gracefully_after_all_retries():
    """get_analysis returns error dictionary after exhausting retries."""
    with patch("src.tools.analysis.get_feature_folder", return_value="feature1"):
        with patch("src.tools.analysis.read_json_file") as mock_read:
            # Continually fail
            mock_read.side_effect = PermissionError("Access denied")

            result = get_analysis.invoke({
                "feature_id": "FEAT-123",
                "analysis_type": "metrics/unit_test_results"
            })

            # Verify multiple attempts occurred
            assert mock_read.call_count >= 1
            assert "error" in result
            assert "Failed to retrieve analysis" in result["error"]
