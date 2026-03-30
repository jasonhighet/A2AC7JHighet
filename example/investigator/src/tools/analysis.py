"""Analysis tool for retrieving feature testing metrics and analysis data.

This module provides the get_analysis tool for the Investigator Agent to retrieve
testing metrics and other analysis data for features.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone
import json
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda

from src.utils.file_utils import (
    get_folder_for_feature_id,
    get_analysis_file_path,
    read_json_file,
    get_feature_folder_mapping,
)
from src.utils.config import load_config

logger = logging.getLogger(__name__)


# Supported analysis types for Phase 1 (Step 3.2)
VALID_ANALYSIS_TYPES = [
    "metrics/unit_test_results",
    "metrics/test_coverage_report",
]


@tool
def get_analysis(feature_id: str, analysis_type: str) -> Dict[str, Any]:
    """Retrieves analysis data for a specific feature.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        analysis_type: Type of analysis, one of:
            - 'metrics/unit_test_results'
            - 'metrics/test_coverage_report'

    Returns:
        Analysis data from the specified file, or error information.

    Use this to assess feature quality and readiness:
    - Check unit test results for failures
    - Review test coverage
    """
    # Validate analysis_type
    if analysis_type not in VALID_ANALYSIS_TYPES:
        return {
            "error": f"Invalid analysis_type: '{analysis_type}'",
            "valid_types": VALID_ANALYSIS_TYPES,
            "suggestion": "Please use one of the supported analysis types",
        }

    # Handle empty or None feature_id
    if not feature_id or not isinstance(feature_id, str):
        return {
            "error": "Invalid feature_id: feature_id must be a non-empty string",
            "suggestion": "Use get_jira_data() to see all available features",
        }

    # Map feature_id to folder
    folder_name = get_folder_for_feature_id(feature_id)
    if not folder_name:
        available_features = list(get_feature_folder_mapping().keys())
        return {
            "error": f"Invalid feature_id: '{feature_id}' not found",
            "available_features": available_features,
            "suggestion": "Use get_jira_data() to see all available features",
        }

    # Get the analysis file path
    try:
        file_path = get_analysis_file_path(folder_name, analysis_type)
    except ValueError as e:
        return {
            "error": "Invalid analysis_type format",
            "message": str(e),
            "valid_types": VALID_ANALYSIS_TYPES,
        }

    # Load config for retry settings
    config = load_config()

    # Internal function for retryable file reading
    def _read_analysis_file(_input: Any = None):
        """Internal function that reads analysis file with retry logic.

        Args:
            _input: Unused input required by RunnableLambda interface
        """
        logger.debug(f"Reading analysis file: {file_path}")
        return read_json_file(file_path)

    # Try to read the analysis file with retry logic
    try:
        # Wrap file reading in a retryable Runnable
        retryable_reader = RunnableLambda(_read_analysis_file).with_retry(
            retry_if_exception_type=(
                FileNotFoundError,
                PermissionError,
                OSError,
                json.JSONDecodeError,
            ),
            wait_exponential_jitter=config.tool_retry_exponential_jitter,
            stop_after_attempt=config.tool_max_retry_attempts,
        )

        # Invoke with empty dict (no input needed)
        data = retryable_reader.invoke({})

        # Success - return data with metadata
        return {
            "success": True,
            "feature_id": feature_id,
            "analysis_type": analysis_type,
            "data": data,
            "metadata": {
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "file_path": str(file_path.relative_to(file_path.parent.parent.parent)),
            },
        }

    except FileNotFoundError:
        return {
            "error": "Analysis not available",
            "feature_id": feature_id,
            "analysis_type": analysis_type,
            "message": f"No {analysis_type.split('/')[-1].replace('_', ' ')} available for this feature",
            "suggestion": "This feature may not have this analysis type, or the file may be missing",
        }

    except json.JSONDecodeError as e:
        logger.error(
            f"JSON parsing error after retries for {feature_id}/{analysis_type}: {e}"
        )
        return {
            "error": "Data parsing error",
            "feature_id": feature_id,
            "analysis_type": analysis_type,
            "message": "Analysis file is corrupted or malformed",
            "technical_details": f"JSONDecodeError after {config.tool_max_retry_attempts} retries: {str(e)}",
        }

    except IOError as e:
        logger.error(
            f"File reading error after retries for {feature_id}/{analysis_type}: {e}"
        )
        return {
            "error": "File reading error",
            "feature_id": feature_id,
            "analysis_type": analysis_type,
            "message": "Unable to read analysis file",
            "technical_details": f"IOError after {config.tool_max_retry_attempts} retries: {str(e)}",
        }
