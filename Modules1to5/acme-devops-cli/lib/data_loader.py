"""
Data loading utilities for DevOps CLI tool.

This module provides a centralized data layer for loading JSON files,
similar to how you'd have a database abstraction layer. This promotes
consistency, reduces code duplication, and makes testing easier.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


def load_json(file_path: str | Path) -> dict[str, Any]:
    """
    Load JSON data from a file.
    
    This is the single, generic function for loading any JSON file.
    It handles all error cases consistently and provides clean separation
    of concerns - just pass a path, get JSON data back.
    
    Args:
        file_path: Path to the JSON file to load. Can be absolute path,
                  relative path, or just filename (will look in default data dir)
        
    Returns:
        Dict containing the parsed JSON data
        
    Raises:
        DataLoadError: If the file cannot be loaded or parsed
    """
    # Convert to Path object for consistent handling
    path = Path(file_path)
    
    # If it's just a filename (no directory), assume it's in the data directory
    if not path.is_absolute() and path.parent == Path('.'):
        data_dir = Path(__file__).parent.parent / "data"
        path = data_dir / path
    
    try:
        if not path.exists():
            raise DataLoadError(f"Data file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Successfully loaded {path}")
            return data
            
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in file {path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e
    except IOError as e:
        error_msg = f"IO error reading file {path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error loading file {path}: {e}"
        logger.error(error_msg)
        raise DataLoadError(error_msg) from e


# Optional: Keep a class-based approach for dependency injection in tests
class DataLoader:
    """
    Optional class-based data loader for dependency injection scenarios.
    
    This allows you to inject a custom data loader in tests or when you need
    to override the default data directory.
    """
    
    def __init__(self, data_dir: Path | None = None):
        """
        Initialize the data loader.
        
        Args:
            data_dir: Optional custom data directory path
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
    
    def load_json(self, filename: str) -> dict[str, Any]:
        """Load JSON data from the configured data directory."""
        return load_json(self.data_dir / filename)
