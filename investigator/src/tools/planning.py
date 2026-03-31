"""Planning document tools for retrieving and searching feature documentation.

This module provides tools for listing, reading, and searching planning documents
(markdown files) from the feature folders in incoming_data.
"""

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from opentelemetry import trace
from langchain_core.tools import tool

from src.utils.file_utils import get_feature_folder, INCOMING_DATA_DIR

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def _get_planning_path(feature_id: str) -> Path:
    """Get the path to the planning documentation for a feature.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')

    Returns:
        Path to the planning directory.

    Raises:
        FileNotFoundError: If the feature or planning directory doesn't exist.
    """
    folder_name = get_feature_folder(feature_id)
    if not folder_name:
        raise FileNotFoundError(f"Feature ID '{feature_id}' not found in incoming_data.")

    planning_path = INCOMING_DATA_DIR / folder_name / "planning"
    if not planning_path.exists() or not planning_path.is_dir():
        raise FileNotFoundError(f"Planning documentation not found for {feature_id}")

    return planning_path


@tool
def list_planning_docs(feature_id: str) -> List[str]:
    """List all available planning documents (markdown files) for a feature.

    Use this first to see which documents are available before reading them.

    Args:
        feature_id: The unique ID of the feature (e.g., 'FEAT-MS-001').

    Returns:
        List of filenames (e.g., ['USER_STORY.md', 'DESIGN_DOC.md']).
    """
    with tracer.start_as_current_span("list_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)
        try:
            planning_path = _get_planning_path(feature_id)
            docs = [f.name for f in planning_path.glob("*.md")]
            span.set_attribute("doc_count", len(docs))
            return sorted(docs)
        except FileNotFoundError as e:
            span.record_exception(e)
            return [str(e)]
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Error listing planning docs for {feature_id}: {e}")
            return [f"Error listing documents: {str(e)}"]


@tool
def read_planning_doc(feature_id: str, doc_name: str) -> str:
    """Read the full content of a specific planning document.

    WARNING: Planning documents can be LARGE (10-15KB). Reading multiple
    full documents will quickly fill your context window.

    Args:
        feature_id: The unique ID of the feature (e.g., 'FEAT-MS-001').
        doc_name: The filename of the document to read (e.g., 'DESIGN_DOC.md').

    Returns:
        The content of the document as a string.
    """
    with tracer.start_as_current_span("read_planning_doc") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("doc_name", doc_name)
        try:
            planning_path = _get_planning_path(feature_id)
            doc_path = planning_path / doc_name
            
            if not doc_path.exists():
                return f"Error: Document '{doc_name}' not found for feature {feature_id}"

            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
                span.set_attribute("content_length", len(content))
                return content
                
        except FileNotFoundError as e:
            span.record_exception(e)
            return str(e)
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Error reading planning doc {doc_name} for {feature_id}: {e}")
            return f"Error reading document: {str(e)}"


@tool
def search_planning_docs(feature_id: str, query: str) -> List[Dict[str, Any]]:
    """Search for specific information across all planning documents for a feature.

    Utilises ripgrep (rg) for fast searching. This is PREFERRED over reading
    entire documents when you are looking for specific requirements or details.

    Args:
        feature_id: The unique ID of the feature (e.g., 'FEAT-MS-001').
        query: The search term or regex to look for.

    Returns:
        List of match results, each containing filename, line number, and text.
    """
    with tracer.start_as_current_span("search_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("query", query)
        try:
            planning_path = _get_planning_path(feature_id)
            
            # Path resolution for ripgrep
            rg_path = "rg"  # Default to PATH
            
            # Fallback for common VS Code ripgrep location on Windows
            import shutil
            if not shutil.which("rg"):
                vscode_rg = r"C:\Users\jason\AppData\Local\Programs\Microsoft VS Code\cfbea10c5f\resources\app\node_modules\@vscode\ripgrep\bin\rg.exe"
                if Path(vscode_rg).exists():
                    rg_path = vscode_rg
                    logger.info(f"Using fallback ripgrep at: {rg_path}")
                else:
                    return [{"error": "ripgrep not found", "message": "Please install 'rg' and add it to your PATH."}]

            # Call ripgrep with JSON output for structured parsing
            result = subprocess.run(
                [rg_path, "--json", "-i", query, str(planning_path)],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 2:
                return [{"error": "Search failed", "message": result.stderr.strip()}]
                
            if not result.stdout:
                return [{"message": f"No matches found for '{query}' in planning docs."}]

            matches = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if data.get("type") == "match":
                        match_data = data["data"]
                        matches.append({
                            "file": Path(match_data["path"]["text"]).name,
                            "line": match_data["line_number"],
                            "text": match_data["lines"]["text"].strip()
                        })
                except (json.JSONDecodeError, KeyError):
                    continue

            span.set_attribute("match_count", len(matches))
            return matches if matches else [{"message": f"No matches found for '{query}'"}]

        except FileNotFoundError as e:
            span.record_exception(e)
            return [{"error": "Data unavailable", "message": str(e)}]
        except Exception as e:
            span.record_exception(e)
            logger.error(f"Error searching planning docs for {feature_id} with query '{query}': {e}")
            return [{"error": "Search error", "message": str(e)}]
