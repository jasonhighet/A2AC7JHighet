"""JIRA tool for retrieving feature metadata.

This module provides the get_jira_data tool that retrieves metadata for all features
from JIRA issue files stored in the incoming_data directory.
"""

import logging
from typing import Any, Dict, List

from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool

from src.utils.config import load_config
from src.utils.file_utils import (
    get_jira_file_path,
    list_available_features,
    read_json_file,
)

logger = logging.getLogger(__name__)


def _read_jira_files(_input: Any = None) -> List[Dict[str, Any]]:
    """Internal function that reads JIRA files.

    Args:
        _input: Unused input required by RunnableLambda interface.

    Returns:
        List of enriched feature metadata dictionaries.

    Raises:
        FileNotFoundError, PermissionError, OSError: For transient errors that should be retried.
    """
    # Get all available features using the file_utils helper
    features = list_available_features()

    if not features:
        return [
            {
                "error": "No features found",
                "message": "The incoming_data directory is empty or contains no valid feature data.",
            }
        ]

    # Enrich each feature with data_quality assessment from the full JIRA JSON
    enriched_features = []
    for feature in features:
        try:
            # Read the full JIRA file to extract more fields
            jira_file = get_jira_file_path(feature["folder"])
            logger.debug(f"Reading JIRA file: {jira_file}")

            jira_data = read_json_file(jira_file)

            # Extract data_quality from customfield_10002
            # (Example mapping: HIGH, MEDIUM, LOW)
            data_quality = jira_data.get("fields", {}).get("customfield_10002", "UNKNOWN")

            enriched_features.append(
                {
                    "folder": feature["folder"],
                    "jira_key": feature["jira_key"],
                    "feature_id": feature["feature_id"],
                    "summary": feature["summary"],
                    "status": feature["status"],
                    "data_quality": data_quality,
                }
            )
        except (FileNotFoundError, PermissionError, OSError) as e:
            # Re-raise transient errors to trigger the 'with_retry' policy
            logger.warning(f"Transient error reading JIRA file for {feature['folder']}: {e}")
            raise
        except Exception as e:
            # For non-retryable errors, include what we have without data_quality
            logger.error(f"Non-retryable error reading JIRA file for {feature['folder']}: {e}")
            enriched_features.append(
                {
                    **feature,
                    "data_quality": "UNKNOWN",
                    "error": f"Failed to read full JIRA data: {str(e)}",
                }
            )

    return enriched_features


@tool
def get_jira_data() -> List[Dict[str, Any]]:
    """Retrieves metadata for ALL features from JIRA.

    Returns an array with folder, jira_key, feature_id, summary, status,
    and data_quality for each feature.

    This tool includes automatic retry logic for transient file I/O errors.

    Use this tool to:
    - Get a list of all available features
    - Find the feature_id needed for other tools
    - Understand current feature status (Development, UAT, Production Ready)

    Returns:
        List of dictionaries containing feature metadata.
    """
    config = load_config()

    try:
        # Wrap file reading in a retryable Runnable
        retryable_reader = RunnableLambda(_read_jira_files).with_retry(
            retry_if_exception_type=(FileNotFoundError, PermissionError, OSError),
            wait_exponential_jitter=config.tool_retry_exponential_jitter,
            stop_after_attempt=config.tool_max_retry_attempts,
        )

        return retryable_reader.invoke({})

    except Exception as e:
        # Graceful degradation after retry exhaustion
        logger.error(f"Failed to retrieve JIRA data after {config.tool_max_retry_attempts} retries: {e}")
        return [
            {
                "error": "Failed to retrieve JIRA data",
                "message": str(e),
                "suggestion": "Check file permissions and paths in the incoming_data directory.",
            }
        ]
