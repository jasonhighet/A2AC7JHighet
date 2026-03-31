"""Unit tests for the planning document tools."""

from unittest.mock import MagicMock, patch
from pathlib import Path
import json

import pytest

from src.tools.planning import list_planning_docs, read_planning_doc, search_planning_docs


@pytest.fixture
def mock_docs() -> list:
    """Mock list of planning documents."""
    return ["USER_STORY.md", "DESIGN_DOC.md", "ARCHITECTURE.md"]


def test_list_planning_docs_success(mock_docs):
    """list_planning_docs returns sorted markdown files."""
    with patch("src.tools.planning.get_feature_folder", return_value="feature1"):
        with patch("pathlib.Path.glob") as mock_glob:
            # Create mock file objects with name attribute
            mock_files = [MagicMock(spec=Path, name=name) for name in mock_docs]
            for i, f in enumerate(mock_files):
                f.name = mock_docs[i]
            mock_glob.return_value = mock_files

            result = list_planning_docs.invoke({"feature_id": "FEAT-123"})
            
            assert len(result) == 3
            assert "USER_STORY.md" in result
            assert "DESIGN_DOC.md" in result


def test_list_planning_docs_fails_on_missing_dir():
    """list_planning_docs returns a clear error message if planning dir is missing."""
    with patch("src.tools.planning.get_feature_folder", return_value="feature1"):
        with patch("pathlib.Path.exists", return_value=False):
            result = list_planning_docs.invoke({"feature_id": "FEAT-123"})
            
            assert "Planning documentation not found" in result[0]


def test_read_planning_doc_success():
    """read_planning_doc returns the file content."""
    content = "# Design Document\nThis is a test."
    with patch("src.tools.planning.get_feature_folder", return_value="feature1"):
        with patch("pathlib.Path.exists", return_value=True):
            # Use mock_open for reading the file
            with patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=MagicMock(read=MagicMock(return_value=content)))))):
                result = read_planning_doc.invoke({
                    "feature_id": "FEAT-123",
                    "doc_name": "DESIGN_DOC.md"
                })
                
                assert content in result
                assert "# Design Document" in result


def test_search_planning_docs_success():
    """search_planning_docs correctly parses ripgrep JSON output."""
    mock_rg_output = (
        '{"type":"match","data":{"path":{"text":"doc.md"},"line_number":10,"lines":{"text":"Requirement 1.2"}}}\n'
        '{"type":"match","data":{"path":{"text":"doc.md"},"line_number":20,"lines":{"text":"Requirement 2.1"}}}\n'
        '{"type":"summary","data":{}}'
    )
    
    with patch("src.tools.planning.get_feature_folder", return_value="feature1"):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout=mock_rg_output,
                    stderr=""
                )
                
                result = search_planning_docs.invoke({
                    "feature_id": "FEAT-123",
                    "query": "requirement"
                })
                
                assert len(result) == 2
                assert result[0]["file"] == "doc.md"
                assert result[0]["line"] == 10
                assert result[0]["text"] == "Requirement 1.2"


def test_search_planning_docs_no_matches():
    """search_planning_docs returns empty list message when no matches found."""
    with patch("src.tools.planning.get_feature_folder", return_value="feature1"):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="",  # rg returns empty stdout on no match
                    stderr=""
                )
                
                result = search_planning_docs.invoke({
                    "feature_id": "FEAT-123",
                    "query": "absent"
                })
                
                assert "No matches found" in result[0]["message"]
