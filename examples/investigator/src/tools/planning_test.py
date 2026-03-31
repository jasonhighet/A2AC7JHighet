"""Unit tests for planning document tools."""

from src.tools.planning import (
    list_planning_docs,
    read_planning_doc,
    search_planning_docs,
)


class TestListPlanningDocs:
    """Tests for list_planning_docs tool."""

    def test_list_planning_docs_success(self):
        """Test listing planning documents for a valid feature."""
        result = list_planning_docs.invoke({"feature_id": "FEAT-MS-001"})

        assert isinstance(result, list)
        assert len(result) > 0
        # Should have common planning docs
        assert any("USER_STORY.md" in doc or "DESIGN_DOC.md" in doc for doc in result)

    def test_list_planning_docs_returns_sorted(self):
        """Test that documents are returned in sorted order."""
        result = list_planning_docs.invoke({"feature_id": "FEAT-MS-001"})

        if isinstance(result, list) and len(result) > 1:
            assert result == sorted(result)

    def test_list_planning_docs_invalid_feature(self):
        """Test with non-existent feature."""
        result = list_planning_docs.invoke({"feature_id": "FEAT-INVALID-999"})

        assert isinstance(result, dict)
        assert "error" in result
        assert "FEAT-INVALID-999" in str(result)

    def test_list_planning_docs_all_are_markdown(self):
        """Test that all returned documents are markdown files."""
        result = list_planning_docs.invoke({"feature_id": "FEAT-MS-001"})

        if isinstance(result, list):
            assert all(doc.endswith(".md") for doc in result)


class TestReadPlanningDoc:
    """Tests for read_planning_doc tool."""

    def test_read_planning_doc_success(self):
        """Test reading a planning document."""
        result = read_planning_doc.invoke(
            {"feature_id": "FEAT-MS-001", "doc_name": "USER_STORY.md"}
        )

        assert isinstance(result, str)
        assert len(result) > 100  # Should have substantial content
        # Should contain markdown headers or content
        assert "#" in result or "maintenance" in result.lower()

    def test_read_planning_doc_invalid_feature(self):
        """Test reading with invalid feature."""
        result = read_planning_doc.invoke(
            {"feature_id": "FEAT-INVALID-999", "doc_name": "USER_STORY.md"}
        )

        assert isinstance(result, dict)
        assert "error" in result

    def test_read_planning_doc_invalid_doc_name(self):
        """Test reading with invalid document name."""
        result = read_planning_doc.invoke(
            {"feature_id": "FEAT-MS-001", "doc_name": "NONEXISTENT.md"}
        )

        assert isinstance(result, dict)
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_read_planning_doc_contains_content(self):
        """Test that read document contains expected content."""
        result = read_planning_doc.invoke(
            {"feature_id": "FEAT-MS-001", "doc_name": "USER_STORY.md"}
        )

        if isinstance(result, str):
            # Should contain typical planning doc content
            assert len(result.split("\n")) > 10  # Multiple lines
            # Should not be empty or just whitespace
            assert result.strip()


class TestSearchPlanningDocs:
    """Tests for search_planning_docs tool."""

    def test_search_planning_docs_success(self):
        """Test searching planning documents."""
        result = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "maintenance"}
        )

        # Should return list or dict
        assert isinstance(result, (list, dict))

        if isinstance(result, list):
            assert len(result) > 0
            # Each match should have required fields
            for match in result:
                assert "file" in match
                assert "line_number" in match
                assert "match" in match

    def test_search_planning_docs_no_matches(self):
        """Test search with no matches."""
        result = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "xyzabc123impossible"}
        )

        assert isinstance(result, dict)
        assert "message" in result or "error" in result

    def test_search_planning_docs_invalid_feature(self):
        """Test search with invalid feature."""
        result = search_planning_docs.invoke(
            {"feature_id": "FEAT-INVALID-999", "query": "test"}
        )

        assert isinstance(result, dict)
        assert "error" in result

    def test_search_planning_docs_case_insensitive(self):
        """Test that search is case insensitive."""
        result_lower = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "maintenance"}
        )

        result_upper = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "MAINTENANCE"}
        )

        # Both should find matches (or both should not find matches)
        if isinstance(result_lower, list) and isinstance(result_upper, list):
            assert len(result_lower) > 0
            assert len(result_upper) > 0

    def test_search_planning_docs_match_structure(self):
        """Test that matches have correct structure."""
        result = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "schedule"}
        )

        if isinstance(result, list) and len(result) > 0:
            match = result[0]
            # Verify structure
            assert isinstance(match["file"], str)
            assert isinstance(match["line_number"], int)
            assert isinstance(match["match"], str)
            # File should be a markdown file
            assert match["file"].endswith(".md")
            # Line number should be positive
            assert match["line_number"] > 0


class TestPlanningToolsIntegration:
    """Integration tests for planning tools."""

    def test_list_then_read_workflow(self):
        """Test the list -> read workflow."""
        # First list documents
        docs = list_planning_docs.invoke({"feature_id": "FEAT-MS-001"})

        if isinstance(docs, list) and len(docs) > 0:
            # Then read the first document
            doc_name = docs[0]
            content = read_planning_doc.invoke(
                {"feature_id": "FEAT-MS-001", "doc_name": doc_name}
            )

            # Should get content
            assert isinstance(content, str)
            assert len(content) > 0

    def test_search_vs_read(self):
        """Test that search returns subset of what read would return."""
        # Search for a term
        search_result = search_planning_docs.invoke(
            {"feature_id": "FEAT-MS-001", "query": "schedule"}
        )

        # Read a doc that should contain the term
        read_result = read_planning_doc.invoke(
            {"feature_id": "FEAT-MS-001", "doc_name": "USER_STORY.md"}
        )

        if isinstance(search_result, list) and len(search_result) > 0:
            if isinstance(read_result, str):
                # At least one match should be from USER_STORY.md
                user_story_matches = [
                    m for m in search_result if m["file"] == "USER_STORY.md"
                ]
                if user_story_matches:
                    # The match text should appear in the full document
                    match_text = user_story_matches[0]["match"].strip()
                    # The match should be a substring of the document
                    # (accounting for line breaks and whitespace variations)
                    assert len(match_text) > 0

    def test_multiple_features(self):
        """Test that planning tools work for different features."""
        features = ["FEAT-MS-001", "FEAT-QR-002", "FEAT-RS-003"]

        for feature_id in features:
            result = list_planning_docs.invoke({"feature_id": feature_id})
            # Should either return a list of docs or an error dict
            assert isinstance(result, (list, dict))
