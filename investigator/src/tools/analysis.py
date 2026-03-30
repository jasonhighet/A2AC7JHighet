"""Analysis tool for retrieving specific feature metrics.

This module provides the get_analysis tool that retrieves detailed test metrics
for a specific feature from the incoming_data directory.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

from src.utils.config import load_config
from src.utils.file_utils import (
    get_analysis_file_path,
    get_feature_folder,
    read_json_file,
)

logger = logging.getLogger(__name__)


def _read_analysis_file(inputs: Dict[str, str]) -> Dict[str, Any]:
    """Internal function that reads an analysis JSON file.

    Args:
        inputs: Dictionary containing 'feature_id' and 'analysis_type'.

    Returns:
        The content of the analysis file.

    Raises:
        FileNotFoundError: If the feature or analysis file doesn't exist.
        PermissionError, OSError: For transient errors that should be retried.
    """
    feature_id = inputs.get("feature_id")
    analysis_type = inputs.get("analysis_type")

    if not feature_id or not analysis_type:
        raise ValueError("Both feature_id and analysis_type must be provided.")

    # Resolve feature_id to its local folder
    folder_name = get_feature_folder(feature_id)
    if not folder_name:
        raise FileNotFoundError(f"Feature ID '{feature_id}' not found in incoming_data.")

    # Get the system-agnostic Path to the analysis file
    file_path = get_analysis_file_path(folder_name, analysis_type)
    
    logger.debug(f"Reading analysis file: {file_path}")
    
    try:
        return read_json_file(file_path)
    except (FileNotFoundError, PermissionError, OSError) as e:
        logger.warning(f"Transient error reading analysis file {file_path}: {e}")
        raise


@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves specific analysis data for a feature.

    Supported analysis types:
    - 'metrics/unit_test_results': Unit test results with pass/fail counts
    - 'metrics/test_coverage_report': Code coverage analysis

    This tool requires a feature_id (e.g., 'FEAT-MS-001') which you can
    retrieve using get_jira_data().

    Args:
        feature_id: The unique ID of the feature to analyse.
        analysis_type: The type of metrics to retrieve.

    Returns:
        Structured JSON data from the analysis file or an error message.
    """
    config = load_config()

    try:
        # Wrap the file reading in a retryable Runnable
        retryable_reader = RunnableLambda(_read_analysis_file).with_retry(
            retry_if_exception_type=(FileNotFoundError, PermissionError, OSError),
            wait_exponential_jitter=config.tool_retry_exponential_jitter,
            stop_after_attempt=config.tool_max_retry_attempts,
        )

        return retryable_reader.invoke({
            "feature_id": feature_id,
            "analysis_type": analysis_type
        })

    except FileNotFoundError as e:
        # For non-existent files, return a clear message instead of technical error
        return {
            "error": "Data unavailable",
            "message": str(e),
            "suggestion": "Verify the feature_id and analysis_type are correct."
        }
    except Exception as e:
        # Graceful degradation after retry exhaustion
        logger.error(f"Failed to retrieve analysis for {feature_id} after retries: {e}")
        return {
            "error": "Failed to retrieve analysis",
            "message": str(e),
            "suggestion": "Check file system permissions and structure."
        }
