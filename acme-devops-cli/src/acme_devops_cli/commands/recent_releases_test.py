#!/usr/bin/env python3
"""
Tests for Recent Releases CLI Command

This module contains comprehensive tests for both the business logic
and CLI interface of the recent releases functionality.
"""

import pytest
import json
from io import StringIO
from unittest.mock import patch

from lib.commands.recent_releases import (
    list_recent_releases,
    print_table,
    create_parser,
    main
)
from lib.data_loader import DataLoadError


class TestRecentReleasesBusinessLogic:
    """Test cases for the core business logic."""
    
    @pytest.fixture
    def sample_releases_data(self):
        """Sample releases data for testing - matches the JSON file structure."""
        return {
            "releases": [
                {
                    "id": "rel-001",
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-17T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and performance improvements",
                    "commitHash": "abc123def456"
                },
                {
                    "id": "rel-002",
                    "applicationId": "api-service",
                    "version": "v1.8.2",
                    "releaseDate": "2024-01-16T07:00:00Z",
                    "author": "charlie@company.com",
                    "releaseNotes": "Security updates and new features",
                    "commitHash": "ghi789jkl012"
                },
                {
                    "id": "rel-003",
                    "applicationId": "web-app",
                    "version": "v2.1.2",
                    "releaseDate": "2024-01-15T10:30:00Z",
                    "author": "bob@company.com",
                    "releaseNotes": "Minor bug fixes",
                    "commitHash": "def456ghi789"
                },
                {
                    "id": "rel-004",
                    "applicationId": "worker-service",
                    "version": "v3.2.1",
                    "releaseDate": "2024-01-14T14:20:00Z",
                    "author": "diana@company.com",
                    "releaseNotes": "Performance optimizations",
                    "commitHash": "mno345pqr678"
                },
                {
                    "id": "rel-005",
                    "applicationId": "analytics-dashboard",
                    "version": "v1.5.0",
                    "releaseDate": "2024-01-13T09:15:00Z",
                    "author": "eve@company.com",
                    "releaseNotes": "New dashboard features",
                    "commitHash": "pqr678stu901"
                },
                {
                    "id": "rel-006",
                    "applicationId": "api-service",
                    "version": "v1.8.1",
                    "releaseDate": "2024-01-12T11:45:00Z",
                    "author": "frank@company.com",
                    "releaseNotes": "Hotfix for critical issue",
                    "commitHash": "jkl012mno345"
                },
                {
                    "id": "rel-007",
                    "applicationId": "web-app",
                    "version": "v2.1.1",
                    "releaseDate": "2024-01-11T16:30:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "UI improvements",
                    "commitHash": "stu901vwx234"
                },
                {
                    "id": "rel-008",
                    "applicationId": "worker-service",
                    "version": "v3.2.0",
                    "releaseDate": "2024-01-10T13:00:00Z",
                    "author": "george@company.com",
                    "releaseNotes": "Major feature release",
                    "commitHash": "vwx234yz567"
                }
            ]
        }
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_default_limit(self, mock_load_json, sample_releases_data):
        """Test getting recent releases with default limit."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases()

        assert result["status"] == "success"
        assert len(result["releases"]) == 8  # All releases since we have only 8
        assert result["total_count"] == 8
        assert result["total_available"] == 8
        assert result["filters_applied"]["limit"] == 10
        assert result["filters_applied"]["application"] is None
        
        # Verify sorting by release date (most recent first)
        release_dates = [r["releaseDate"] for r in result["releases"]]
        assert release_dates == sorted(release_dates, reverse=True)
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_custom_limit(self, mock_load_json, sample_releases_data):
        """Test getting recent releases with custom limit."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(limit=3)

        assert result["status"] == "success"
        assert len(result["releases"]) == 3
        assert result["total_count"] == 3
        assert result["total_available"] == 8
        assert result["filters_applied"]["limit"] == 3
        
        # Should get the 3 most recent releases
        expected_versions = ["v2.1.3", "v1.8.2", "v2.1.2"]  # Based on dates
        actual_versions = [r["version"] for r in result["releases"]]
        assert actual_versions == expected_versions
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_filter_by_application(self, mock_load_json, sample_releases_data):
        """Test filtering releases by application."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(application="web-app")
            
        assert result["status"] == "success"
        assert len(result["releases"]) == 3  # 3 web-app releases
        assert result["total_count"] == 3
        assert result["total_available"] == 3
        assert all(r["applicationId"] == "web-app" for r in result["releases"])
        assert result["filters_applied"]["application"] == "web-app"
        assert result["filters_applied"]["limit"] == 10
        
        # Verify sorting by release date (most recent first)
        expected_versions = ["v2.1.3", "v2.1.2", "v2.1.1"]  # Based on dates
        actual_versions = [r["version"] for r in result["releases"]]
        assert actual_versions == expected_versions
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_filter_by_application_and_limit(self, mock_load_json, sample_releases_data):
        """Test filtering releases by application with custom limit."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(limit=2, application="api-service")
            
        assert result["status"] == "success"
        assert len(result["releases"]) == 2
        assert result["total_count"] == 2
        assert result["total_available"] == 2  # Only 2 api-service releases total
        assert all(r["applicationId"] == "api-service" for r in result["releases"])
        assert result["filters_applied"]["application"] == "api-service"
        assert result["filters_applied"]["limit"] == 2
        
        # Should get the 2 most recent api-service releases
        expected_versions = ["v1.8.2", "v1.8.1"]  # Based on dates
        actual_versions = [r["version"] for r in result["releases"]]
        assert actual_versions == expected_versions
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_no_matches(self, mock_load_json, sample_releases_data):
        """Test filtering with no matching results."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(application="nonexistent-app")
            
        assert result["status"] == "success"
        assert len(result["releases"]) == 0
        assert result["total_count"] == 0
        assert result["total_available"] == 0
        assert result["filters_applied"]["application"] == "nonexistent-app"
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_invalid_limit(self, mock_load_json):
        """Test handling of invalid limit parameter."""
        result = list_recent_releases(limit=0)
            
        assert result["status"] == "error"
        assert "Limit must be a positive integer" in result["error"]
        assert len(result["releases"]) == 0
        assert result["total_count"] == 0
        
        result = list_recent_releases(limit=-5)
            
        assert result["status"] == "error"
        assert "Limit must be a positive integer" in result["error"]
        assert len(result["releases"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_no_data_available(self, mock_load_json):
        """Test handling when no releases data is available."""
        empty_data = {"releases": []}
        mock_load_json.return_value = empty_data
        result = list_recent_releases()
            
        assert result["status"] == "error"
        assert result["error"] == "No releases data available"
        assert len(result["releases"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_data_loading_error(self, mock_load_json):
        """Test handling when data loading raises an exception."""
        mock_load_json.side_effect = DataLoadError("File not found")
        result = list_recent_releases()
            
        assert result["status"] == "error"
        assert "Failed to load releases data" in result["error"]
        assert len(result["releases"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_response_structure(self, mock_load_json, sample_releases_data):
        """Test that the response has the correct structure."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases()
            
        # Check required fields are present
        required_fields = ["status", "releases", "total_count", "total_available", "filters_applied", "timestamp"]
        for field in required_fields:
            assert field in result
        
        # Check filters_applied structure
        assert "limit" in result["filters_applied"]
        assert "application" in result["filters_applied"]
        
        # Check timestamp format (basic validation)
        assert "T" in result["timestamp"]
        assert "Z" in result["timestamp"]
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_date_sorting_with_invalid_dates(self, mock_load_json):
        """Test handling of invalid date formats in sorting."""
        # Create data with invalid date format
        invalid_date_data = {
            "releases": [
                {
                    "id": "rel-001",
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "invalid-date",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes",
                    "commitHash": "abc123def456"
                },
                {
                    "id": "rel-002",
                    "applicationId": "api-service",
                    "version": "v1.8.2",
                    "releaseDate": "2024-01-16T07:00:00Z",
                    "author": "charlie@company.com",
                    "releaseNotes": "Security updates",
                    "commitHash": "ghi789jkl012"
                }
            ]
        }
        
        mock_load_json.return_value = invalid_date_data
        result = list_recent_releases()
            
        # Should still succeed even with invalid dates
        assert result["status"] == "success"
        assert len(result["releases"]) == 2
        assert result["total_count"] == 2
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_data_integrity(self, mock_load_json, sample_releases_data):
        """Test that release data is returned intact without modification."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(limit=1)
            
        # Verify that the original release data is preserved
        returned_release = result["releases"][0]
        # Should be the most recent release (v2.1.3)
        original_release = next(r for r in sample_releases_data["releases"] if r["version"] == "v2.1.3")
        
        for key, value in original_release.items():
            assert returned_release[key] == value
    
    @patch('lib.commands.recent_releases.load_json')
    def test_list_recent_releases_limit_larger_than_available(self, mock_load_json, sample_releases_data):
        """Test limit larger than available releases."""
        mock_load_json.return_value = sample_releases_data
        result = list_recent_releases(limit=20)  # More than the 8 available
            
        assert result["status"] == "success"
        assert len(result["releases"]) == 8  # All available releases
        assert result["total_count"] == 8
        assert result["total_available"] == 8
        assert result["filters_applied"]["limit"] == 20


class TestRecentReleasesCLI:
    """Test cases for the CLI interface."""
    
    def test_create_parser(self):
        """Test argument parser creation and configuration."""
        parser = create_parser()
        
        # Test parser configuration
        assert parser.description
        assert parser.epilog
        assert "Examples:" in parser.epilog
        
        # Test that parser can be created without errors
        assert parser is not None
    
    def test_argument_parsing_valid_combinations(self):
        """Test parsing of valid argument combinations."""
        parser = create_parser()
        
        # Test no arguments (defaults)
        args = parser.parse_args([])
        assert args.limit == 10
        assert args.app is None
        assert args.format == 'json'
        assert args.verbose is False
        
        # Test limit option
        args = parser.parse_args(['--limit', '5'])
        assert args.limit == 5
        
        args = parser.parse_args(['-l', '15'])
        assert args.limit == 15
        
        # Test application filter
        args = parser.parse_args(['--app', 'web-app'])
        assert args.app == 'web-app'
        
        # Test format options
        args = parser.parse_args(['--format', 'table'])
        assert args.format == 'table'
        
        args = parser.parse_args(['--format', 'json'])
        assert args.format == 'json'
        
        # Test verbose flag
        args = parser.parse_args(['--verbose'])
        assert args.verbose is True
        
        args = parser.parse_args(['-v'])
        assert args.verbose is True
        
        # Test combination of arguments
        args = parser.parse_args(['--limit', '3', '--app', 'api-service', '--format', 'table', '--verbose'])
        assert args.limit == 3
        assert args.app == 'api-service'
        assert args.format == 'table'
        assert args.verbose is True
    
    def test_argument_parsing_invalid_limit(self):
        """Test handling of invalid limit argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--limit', 'invalid'])
        
        # Note: argparse allows negative integers, validation happens in business logic
        args = parser.parse_args(['--limit', '-5'])
        assert args.limit == -5
    
    def test_argument_parsing_invalid_format(self):
        """Test handling of invalid format argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--format', 'invalid'])
    
    @patch('lib.commands.recent_releases.list_recent_releases')
    def test_main_success_json_output(self, mock_list_recent_releases):
        """Test main function with successful JSON output."""
        mock_list_recent_releases.return_value = {
            "status": "success",
            "releases": [{"id": "test"}],
            "total_count": 1,
            "total_available": 1
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['recent_releases', '--format', 'json']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate JSON output
        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert parsed["status"] == "success"
        assert parsed["total_count"] == 1
    
    @patch('lib.commands.recent_releases.list_recent_releases')
    def test_main_success_table_output(self, mock_list_recent_releases):
        """Test main function with successful table output."""
        mock_list_recent_releases.return_value = {
            "status": "success",
            "releases": [
                {
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-17T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and improvements"
                }
            ],
            "total_count": 1,
            "total_available": 1
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['recent_releases', '--format', 'table']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate table formatting
        output = captured_output.getvalue()
        assert "Application" in output  # Header present
        assert "Version" in output  # Header present
        assert "Release Date" in output  # Header present
        assert "Author" in output  # Header present
        assert "Notes" in output  # Header present
        assert "---" in output  # Separator present
        assert "web-app" in output  # Data present
        assert "v2.1.3" in output  # Data present
        assert "Total: 1 releases" in output  # Summary present
    
    @patch('lib.commands.recent_releases.list_recent_releases')
    def test_main_success_table_output_with_limit_info(self, mock_list_recent_releases):
        """Test main function with table output showing limit information."""
        mock_list_recent_releases.return_value = {
            "status": "success",
            "releases": [
                {
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-17T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes"
                }
            ],
            "total_count": 1,
            "total_available": 5  # More available than shown
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['recent_releases', '--format', 'table']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate table formatting with limit info
        output = captured_output.getvalue()
        assert "Showing 1 of 5 releases" in output  # Limit info present
    
    @patch('lib.commands.recent_releases.list_recent_releases')
    def test_main_error_handling(self, mock_list_recent_releases):
        """Test main function error handling and exit codes."""
        mock_list_recent_releases.return_value = {
            "status": "error",
            "error": "Test error message",
            "releases": [],
            "total_count": 0
        }
        
        with patch('sys.argv', ['recent_releases']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1  # Error exit code
    
    @patch('lib.commands.recent_releases.list_recent_releases')
    def test_main_with_parameters(self, mock_list_recent_releases):
        """Test main function passes parameters correctly."""
        mock_list_recent_releases.return_value = {
            "status": "success",
            "releases": [],
            "total_count": 0,
            "total_available": 0
        }
        
        with patch('sys.argv', ['recent_releases', '--limit', '5', '--app', 'web-app']):
            try:
                main()
            except SystemExit:
                pass
        
        # Verify the function was called with correct parameters
        mock_list_recent_releases.assert_called_once_with(5, 'web-app')
    
    def test_print_table_success(self):
        """Test table printing with successful data."""
        result = {
            "status": "success",
            "releases": [
                {
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-17T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and performance improvements"
                },
                {
                    "applicationId": "api-service",
                    "version": "v1.8.2",
                    "releaseDate": "2024-01-16T07:00:00Z",
                    "author": "charlie@company.com",
                    "releaseNotes": "Security updates and new features"
                }
            ],
            "total_count": 2,
            "total_available": 2
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        # Validate table structure and content
        assert "Application" in output
        assert "Version" in output
        assert "Release Date" in output
        assert "Author" in output
        assert "Notes" in output
        assert "---" in output  # Separator line
        assert "web-app" in output
        assert "api-service" in output
        assert "v2.1.3" in output
        assert "v1.8.2" in output
        # Note: Author field is truncated in table format, so check for partial match
        assert "alice@company." in output  # Truncated version
        assert "charlie@compan" in output  # Truncated version
        assert "Total: 2 releases" in output
    
    def test_print_table_success_with_limit_info(self):
        """Test table printing with limit information."""
        result = {
            "status": "success",
            "releases": [
                {
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-17T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes"
                }
            ],
            "total_count": 1,
            "total_available": 10  # More available than shown
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        assert "Showing 1 of 10 releases" in output
    
    def test_print_table_error(self):
        """Test table printing with error data."""
        result = {
            "status": "error",
            "error": "Test error message",
            "releases": [],
            "total_count": 0
        }
        
        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            print_table(result)
        
        error_output = captured_error.getvalue()
        assert "Error: Test error message" in error_output
    
    def test_print_table_no_releases(self):
        """Test table printing with no releases found."""
        result = {
            "status": "success",
            "releases": [],
            "total_count": 0
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        assert "No releases found matching the criteria." in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
