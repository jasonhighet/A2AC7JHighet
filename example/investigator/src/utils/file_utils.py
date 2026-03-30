"""File utilities for reading and managing test data files.

This module provides utilities for mapping feature IDs to folder paths and reading
JSON data files from the incoming_data directory structure.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


# Base path to incoming data directory
INCOMING_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "incoming"


def get_feature_folder_mapping() -> Dict[str, str]:
    """Maps feature IDs to folder names.

    This function scans the incoming_data directory and reads each feature's
    JIRA issue file to extract the feature_id (customfield_10001) and map it
    to the corresponding folder path.

    Returns:
        Dict mapping feature_id → folder path (relative to incoming_data/)

    Example:
        {
            "FEAT-MS-001": "feature1",
            "FEAT-QR-002": "feature2",
            "FEAT-RS-003": "feature3",
            "FEAT-CT-004": "feature4"
        }
    """
    mapping = {}

    # Scan for feature folders (feature1, feature2, etc.)
    if not INCOMING_DATA_DIR.exists():
        return mapping

    for folder in sorted(INCOMING_DATA_DIR.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("feature"):
            continue

        # Try to read the JIRA feature_issue.json file
        jira_file = folder / "jira" / "feature_issue.json"
        if not jira_file.exists():
            continue

        try:
            with open(jira_file, "r", encoding="utf-8") as f:
                jira_data = json.load(f)

            # Extract feature_id from customfield_10001
            feature_id = jira_data.get("fields", {}).get("customfield_10001")
            if feature_id:
                mapping[feature_id] = folder.name

        except (json.JSONDecodeError, KeyError, IOError):
            # Skip folders with malformed or missing JIRA data
            continue

    return mapping


def get_folder_for_feature_id(feature_id: str) -> Optional[str]:
    """Get the folder name for a given feature ID.

    Args:
        feature_id: The feature ID (e.g., "FEAT-MS-001")

    Returns:
        Folder name (e.g., "feature1") or None if not found
    """
    mapping = get_feature_folder_mapping()
    return mapping.get(feature_id)


def read_json_file(file_path: Path) -> Dict[str, Any]:
    """Read and parse a JSON file.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data as a dictionary

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file is not valid JSON
        IOError: If there's an error reading the file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_jira_file_path(folder_name: str) -> Path:
    """Get the path to the JIRA feature_issue.json file for a folder.

    Args:
        folder_name: Name of the feature folder (e.g., "feature1")

    Returns:
        Path to the JIRA feature_issue.json file
    """
    return INCOMING_DATA_DIR / folder_name / "jira" / "feature_issue.json"


def get_analysis_file_path(folder_name: str, analysis_type: str) -> Path:
    """Get the path to an analysis file for a folder.

    Args:
        folder_name: Name of the feature folder (e.g., "feature1")
        analysis_type: Type of analysis (e.g., "metrics/unit_test_results")

    Returns:
        Path to the analysis file

    Example:
        >>> get_analysis_file_path("feature1", "metrics/unit_test_results")
        PosixPath('.../incoming_data/feature1/metrics/unit_test_results.json')
    """
    # Split analysis_type into subdirectory and filename
    parts = analysis_type.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid analysis_type format: '{analysis_type}'. "
            "Expected format: 'subdirectory/filename'"
        )

    subdirectory, filename = parts
    return INCOMING_DATA_DIR / folder_name / subdirectory / f"{filename}.json"


def list_available_features() -> list[Dict[str, str]]:
    """List all available features with their basic metadata.

    Returns:
        List of dictionaries containing feature metadata:
        - feature_id: The feature ID (e.g., "FEAT-MS-001")
        - folder: The folder name (e.g., "feature1")
        - jira_key: The JIRA key (e.g., "PLAT-1523")
        - summary: The feature summary
        - status: Current status

    Example:
        [
            {
                "feature_id": "FEAT-MS-001",
                "folder": "feature1",
                "jira_key": "PLAT-1523",
                "summary": "Maintenance Scheduling & Alert System",
                "status": "Production Ready"
            },
            ...
        ]
    """
    features = []

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

            feature = {
                "feature_id": fields.get("customfield_10001", ""),
                "folder": folder.name,
                "jira_key": jira_data.get("key", ""),
                "summary": fields.get("summary", ""),
                "status": fields.get("status", {}).get("name", ""),
            }

            # Only include if we have the essential fields
            if feature["feature_id"] and feature["jira_key"]:
                features.append(feature)

        except (json.JSONDecodeError, KeyError, IOError):
            # Skip folders with malformed data
            continue

    return features
