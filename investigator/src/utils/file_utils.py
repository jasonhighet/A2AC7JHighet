"""File utilities for reading and managing incoming feature data.

This module provides utilities for mapping feature IDs to folder paths and reading
JSON data files from the incoming_data directory structure.

All paths use pathlib.Path for full Windows compatibility.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# The incoming_data directory lives alongside the investigator package root.
# Resolved relative to this file: investigator/src/utils/file_utils.py → investigator/ → ../incoming_data
INCOMING_DATA_DIR = Path(__file__).parent.parent.parent.parent / "incoming_data"


def get_feature_folder_mapping() -> Dict[str, str]:
    """Map feature IDs to folder names by scanning incoming_data.

    Reads each feature folder's JIRA issue file to extract the feature_id
    (customfield_10001) and maps it to the corresponding folder name.

    Returns:
        Dict mapping feature_id → folder name (e.g., {"FEAT-MS-001": "feature1"})
    """
    mapping: Dict[str, str] = {}

    if not INCOMING_DATA_DIR.exists():
        return mapping

    for folder in sorted(INCOMING_DATA_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("feature"):
            continue

        jira_file = folder / "jira" / "feature_issue.json"
        if not jira_file.exists():
            continue

        try:
            with open(jira_file, "r", encoding="utf-8") as f:
                jira_data = json.load(f)

            feature_id = jira_data.get("fields", {}).get("customfield_10001")
            if feature_id:
                mapping[feature_id] = folder.name

        except (json.JSONDecodeError, KeyError, OSError):
            # Skip folders with malformed or missing JIRA data
            continue

    return mapping


def get_feature_folder(feature_id: str) -> Optional[str]:
    """Get the folder name for a given feature ID.

    Args:
        feature_id: The feature ID (e.g., "FEAT-MS-001")

    Returns:
        Folder name (e.g., "feature1") or None if not found.
    """
    return get_feature_folder_mapping().get(feature_id)


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
        OSError: If there is an error reading the file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_jira_file_path(folder_name: str) -> Path:
    """Return the path to the JIRA feature_issue.json for a given folder.

    Args:
        folder_name: Name of the feature folder (e.g., "feature1")

    Returns:
        Path to the JIRA feature_issue.json file.
    """
    return INCOMING_DATA_DIR / folder_name / "jira" / "feature_issue.json"


def get_analysis_file_path(folder_name: str, analysis_type: str) -> Path:
    """Return the path to an analysis file for a given folder.

    Args:
        folder_name: Name of the feature folder (e.g., "feature1")
        analysis_type: Type of analysis (e.g., "metrics/unit_test_results")

    Returns:
        Path to the analysis JSON file.

    Raises:
        ValueError: If analysis_type is not in 'subdirectory/filename' format.

    Example:
        >>> get_analysis_file_path("feature1", "metrics/unit_test_results")
        PosixPath('.../incoming_data/feature1/metrics/unit_test_results.json')
    """
    parts = analysis_type.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid analysis_type format: '{analysis_type}'. "
            "Expected format: 'subdirectory/filename'"
        )

    subdirectory, filename = parts
    return INCOMING_DATA_DIR / folder_name / subdirectory / f"{filename}.json"


def list_available_features() -> List[Dict[str, str]]:
    """List all available features with their basic metadata.

    Scans the incoming_data directory and reads each JIRA issue file to
    extract essential feature metadata.

    Returns:
        List of dicts, each containing:
        - feature_id: The feature ID (e.g., "FEAT-MS-001")
        - folder: The folder name (e.g., "feature1")
        - jira_key: The JIRA key (e.g., "PLAT-1523")
        - summary: The feature summary
        - status: Current status name
    """
    features: List[Dict[str, str]] = []

    if not INCOMING_DATA_DIR.exists():
        return features

    for folder in sorted(INCOMING_DATA_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("feature"):
            continue

        jira_file = folder / "jira" / "feature_issue.json"
        if not jira_file.exists():
            continue

        try:
            jira_data = read_json_file(jira_file)
            fields = jira_data.get("fields", {})

            feature: Dict[str, str] = {
                "feature_id": fields.get("customfield_10001", ""),
                "folder": folder.name,
                "jira_key": jira_data.get("key", ""),
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", ""),
            }

            # Only include features that have the essential identifiers
            if feature["feature_id"] and feature["jira_key"]:
                features.append(feature)

        except (json.JSONDecodeError, KeyError, OSError):
            continue

    return features
