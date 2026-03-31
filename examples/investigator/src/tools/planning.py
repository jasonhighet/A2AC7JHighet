"""Planning document tools for retrieving and searching planning documentation.

This module provides tools for the Investigator Agent to access planning documents
such as user stories, design docs, architecture specs, and API documentation.
"""

import logging
import subprocess
import json
from typing import List, Dict, Any, Union
from pathlib import Path
from langchain_core.tools import tool
from opentelemetry import trace

from src.utils.file_utils import get_folder_for_feature_id

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@tool
def list_planning_docs(feature_id: str) -> Union[List[str], Dict[str, Any]]:
    """List all planning documents available for a feature.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')

    Returns:
        List of document names (e.g., ['USER_STORY.md', 'DESIGN_DOC.md', ...])
        or error dict if feature not found

    Use this to:
    - See what documentation exists for a feature
    - Determine which documents to read for specific information
    - Avoid reading unnecessary large documents
    """
    with tracer.start_as_current_span("tool.list_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)

        try:
            # Map feature_id to folder
            folder = get_folder_for_feature_id(feature_id)
            if not folder:
                return {
                    "error": f"Feature not found: {feature_id}",
                    "suggestion": "Use get_jira_data() to see available features",
                }

            planning_path = Path("data/incoming") / folder / "planning"

            if not planning_path.exists():
                return {
                    "error": f"Planning directory not found for {feature_id}",
                    "feature_id": feature_id,
                    "suggestion": "This feature may not have planning documents",
                }

            # List all .md files
            docs = sorted([f.name for f in planning_path.glob("*.md")])

            if len(docs) == 0:
                return {
                    "message": f"No planning documents found for {feature_id}",
                    "feature_id": feature_id,
                }

            span.set_attribute("docs_found", len(docs))
            span.set_attribute("docs", json.dumps(docs))
            return docs

        except Exception as e:
            logger.error(f"Error listing planning docs for {feature_id}: {e}")
            span.set_attribute("error", str(e))
            return {
                "error": "Failed to list planning documents",
                "feature_id": feature_id,
                "technical_details": str(e),
            }


@tool
def read_planning_doc(feature_id: str, doc_name: str) -> Union[str, Dict[str, Any]]:
    """Read a specific planning document.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        doc_name: Document name from list_planning_docs (e.g., 'USER_STORY.md')

    Returns:
        Full document content (may be large, 10-15KB) or error dict

    WARNING: Planning documents can be large. Consider using
    search_planning_docs if you're looking for specific information.

    Use this when:
    - You need comprehensive understanding of the entire document
    - User explicitly asks for "everything" in a doc
    - You need full context to answer a question
    """
    with tracer.start_as_current_span("tool.read_planning_doc") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("doc_name", doc_name)

        try:
            # Map feature_id to folder
            folder = get_folder_for_feature_id(feature_id)
            if not folder:
                return {
                    "error": f"Feature not found: {feature_id}",
                    "suggestion": "Use get_jira_data() to see available features",
                }

            doc_path = Path("data/incoming") / folder / "planning" / doc_name

            if not doc_path.exists():
                return {
                    "error": f"Document not found: {doc_name}",
                    "feature_id": feature_id,
                    "suggestion": "Use list_planning_docs() to see available documents",
                }

            # Read the document
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()

            span.set_attribute("doc_size_bytes", len(content))
            span.set_attribute("doc_size_kb", len(content) / 1024)
            logger.info(
                f"Read planning doc {doc_name} for {feature_id} ({len(content)} bytes)"
            )
            return content

        except Exception as e:
            logger.error(f"Error reading planning doc {doc_name} for {feature_id}: {e}")
            span.set_attribute("error", str(e))
            return {
                "error": "Failed to read document",
                "feature_id": feature_id,
                "doc_name": doc_name,
                "technical_details": str(e),
            }


@tool
def search_planning_docs(
    feature_id: str, query: str
) -> Union[List[Dict[str, str]], Dict[str, Any]]:
    """Search planning documents using ripgrep.

    Args:
        feature_id: The feature ID (e.g., 'FEAT-MS-001')
        query: Search query (regex supported)

    Returns:
        List of matches with filename, line number, and matching text,
        or error dict if search fails

    Use this to:
    - Find specific information across all planning docs
    - Avoid reading entire large documents
    - Locate mentions of specific requirements, APIs, or components

    Example: search_planning_docs('FEAT-MS-001', 'authentication')

    This is PREFERRED over read_planning_doc when looking for specific information.
    """
    with tracer.start_as_current_span("tool.search_planning_docs") as span:
        span.set_attribute("feature_id", feature_id)
        span.set_attribute("query", query)

        try:
            # Map feature_id to folder
            folder = get_folder_for_feature_id(feature_id)
            if not folder:
                return {
                    "error": f"Feature not found: {feature_id}",
                    "suggestion": "Use get_jira_data() to see available features",
                }

            planning_path = Path("data/incoming") / folder / "planning"

            if not planning_path.exists():
                return {
                    "error": f"Planning directory not found for {feature_id}",
                    "feature_id": feature_id,
                    "suggestion": "This feature may not have planning documents",
                }

            # Call ripgrep with JSON output
            result = subprocess.run(
                ["rg", "--json", "--ignore-case", query, str(planning_path)],
                capture_output=True,
                text=True,
            )

            span.set_attribute("ripgrep.exit_code", result.returncode)

            # Parse ripgrep JSON output
            matches = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "match":
                            matches.append(
                                {
                                    "file": Path(data["data"]["path"]["text"]).name,
                                    "line_number": data["data"]["line_number"],
                                    "match": data["data"]["lines"]["text"].strip(),
                                }
                            )
                    except json.JSONDecodeError:
                        continue

            if len(matches) == 0:
                span.set_attribute("matches_found", 0)
                return {
                    "message": f"No matches found for '{query}'",
                    "feature_id": feature_id,
                    "query": query,
                }

            # Limit to 20 matches to avoid context overflow
            if len(matches) > 20:
                logger.info(f"Found {len(matches)} matches, returning first 20")
                matches = matches[:20]

            span.set_attribute("matches_found", len(matches))
            span.set_attribute("files_searched", len(set(m["file"] for m in matches)))
            return matches

        except FileNotFoundError:
            span.set_attribute("error", "ripgrep_not_found")
            return {
                "error": "ripgrep not found",
                "suggestion": "Install ripgrep: brew install ripgrep (macOS) or apt-get install ripgrep (Linux)",
                "technical_details": "ripgrep (rg command) is required for searching planning documents",
            }
        except Exception as e:
            logger.error(f"Error searching planning docs for {feature_id}: {e}")
            span.set_attribute("error", str(e))
            return {
                "error": "Search failed",
                "feature_id": feature_id,
                "query": query,
                "technical_details": str(e),
            }
