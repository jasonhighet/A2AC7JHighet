#!/usr/bin/env python3
"""
Tests for Environment Health CLI Command

This module contains comprehensive tests for both the business logic
and CLI interface of the environment health functionality.
"""

import pytest
import json
import sys
from io import StringIO
from unittest.mock import patch

from lib.commands.environment_health import (
    check_environment_health,
    _determine_overall_status,
    print_table,
    create_parser,
    main
)
from lib.data_loader import DataLoadError


class TestEnvironmentHealthBusinessLogic:
    """Test cases for the core business logic."""
    
    @pytest.fixture
    def sample_health_data(self):
        """Sample health data for testing - matches the JSON file structure."""
        return {
            "releaseHealth": [
                {
                    "id": "health-001",
                    "applicationId": "web-app",
                    "environment": "prod",
                    "status": "healthy",
                    "uptime": 99.9,
                    "responseTime": 120,
                    "issues": 0,
                    "lastChecked": "2024-01-15T10:30:00Z"
                },
                {
                    "id": "health-002",
                    "applicationId": "web-app",
                    "environment": "uat",
                    "status": "degraded",
                    "uptime": 98.5,
                    "responseTime": 250,
                    "issues": 2,
                    "lastChecked": "2024-01-16T14:20:00Z"
                },
                {
                    "id": "health-003",
                    "applicationId": "api-service",
                    "environment": "prod",
                    "status": "healthy",
                    "uptime": 99.8,
                    "responseTime": 85,
                    "issues": 0,
                    "lastChecked": "2024-01-14T09:15:00Z"
                },
                {
                    "id": "health-004",
                    "applicationId": "api-service",
                    "environment": "staging",
                    "status": "unhealthy",
                    "uptime": 85.2,
                    "responseTime": 500,
                    "issues": 5,
                    "lastChecked": "2024-01-17T11:45:00Z"
                },
                {
                    "id": "health-005",
                    "applicationId": "worker-service",
                    "environment": "prod",
                    "status": "degraded",
                    "uptime": 95.1,
                    "responseTime": 300,
                    "issues": 3,
                    "lastChecked": "2024-01-16T16:30:00Z"
                },
                {
                    "id": "health-006",
                    "applicationId": "analytics-dashboard",
                    "environment": "uat",
                    "status": "healthy",
                    "uptime": 99.5,
                    "responseTime": 150,
                    "issues": 0,
                    "lastChecked": "2024-01-15T13:00:00Z"
                }
            ]
        }
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_no_filters(self, mock_load_json, sample_health_data):
        """Test getting all health checks without filters."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health()

        assert result["status"] == "success"
        assert len(result["health_checks"]) == 6
        assert result["total_count"] == 6
        assert result["filters_applied"]["environment"] is None
        assert result["filters_applied"]["application"] is None
        assert result["overall_status"] == "unhealthy"  # Due to one unhealthy service
        assert result["summary"]["healthy"] == 3
        assert result["summary"]["degraded"] == 2
        assert result["summary"]["unhealthy"] == 1
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_filter_by_environment(self, mock_load_json, sample_health_data):
        """Test filtering health checks by environment."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health(environment="prod")
            
        assert result["status"] == "success"
        assert len(result["health_checks"]) == 3
        assert result["total_count"] == 3
        assert all(h["environment"] == "prod" for h in result["health_checks"])
        assert result["filters_applied"]["environment"] == "prod"
        assert result["filters_applied"]["application"] is None
        assert result["overall_status"] == "degraded"  # Due to degraded worker-service
        assert result["summary"]["healthy"] == 2
        assert result["summary"]["degraded"] == 1
        assert result["summary"]["unhealthy"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_filter_by_application(self, mock_load_json, sample_health_data):
        """Test filtering health checks by application."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health(application="web-app")
            
        assert result["status"] == "success"
        assert len(result["health_checks"]) == 2
        assert result["total_count"] == 2
        assert all(h["applicationId"] == "web-app" for h in result["health_checks"])
        assert result["filters_applied"]["environment"] is None
        assert result["filters_applied"]["application"] == "web-app"
        assert result["overall_status"] == "degraded"  # Due to degraded uat environment
        assert result["summary"]["healthy"] == 1
        assert result["summary"]["degraded"] == 1
        assert result["summary"]["unhealthy"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_filter_by_both(self, mock_load_json, sample_health_data):
        """Test filtering health checks by both environment and application."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health(environment="prod", application="web-app")
            
        assert result["status"] == "success"
        assert len(result["health_checks"]) == 1
        assert result["total_count"] == 1
        assert result["health_checks"][0]["applicationId"] == "web-app"
        assert result["health_checks"][0]["environment"] == "prod"
        assert result["filters_applied"]["environment"] == "prod"
        assert result["filters_applied"]["application"] == "web-app"
        assert result["overall_status"] == "healthy"
        assert result["summary"]["healthy"] == 1
        assert result["summary"]["degraded"] == 0
        assert result["summary"]["unhealthy"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_no_matches(self, mock_load_json, sample_health_data):
        """Test filtering with no matching results."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health(application="nonexistent-app")
            
        assert result["status"] == "success"
        assert len(result["health_checks"]) == 0
        assert result["total_count"] == 0
        assert result["filters_applied"]["application"] == "nonexistent-app"
        assert result["overall_status"] == "unknown"
        assert result["summary"]["healthy"] == 0
        assert result["summary"]["degraded"] == 0
        assert result["summary"]["unhealthy"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_no_data_available(self, mock_load_json):
        """Test handling when no health data is available."""
        empty_data = {"releaseHealth": []}
        mock_load_json.return_value = empty_data
        result = check_environment_health()
            
        assert result["status"] == "error"
        assert result["error"] == "No environment health data available"
        assert len(result["health_checks"]) == 0
        assert result["total_count"] == 0
        assert result["summary"]["healthy"] == 0
        assert result["summary"]["degraded"] == 0
        assert result["summary"]["unhealthy"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_data_loading_error(self, mock_load_json):
        """Test handling when data loading raises an exception."""
        mock_load_json.side_effect = DataLoadError("File not found")
        result = check_environment_health()
            
        assert result["status"] == "error"
        assert "Failed to load environment health data" in result["error"]
        assert len(result["health_checks"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_response_structure(self, mock_load_json, sample_health_data):
        """Test that the response has the correct structure."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health()
            
        # Check required fields are present
        required_fields = ["status", "health_checks", "total_count", "summary", "overall_status", "filters_applied", "timestamp"]
        for field in required_fields:
            assert field in result
        
        # Check filters_applied structure
        assert "environment" in result["filters_applied"]
        assert "application" in result["filters_applied"]
        
        # Check summary structure
        assert "healthy" in result["summary"]
        assert "degraded" in result["summary"]
        assert "unhealthy" in result["summary"]
        
        # Check timestamp format (basic validation)
        assert "T" in result["timestamp"]
        assert "Z" in result["timestamp"]
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_sorting_by_status_priority(self, mock_load_json, sample_health_data):
        """Test that health checks are sorted by status priority (unhealthy first)."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health()
            
        # Verify sorting: unhealthy first, then degraded, then healthy
        statuses = [h["status"] for h in result["health_checks"]]
        unhealthy_indices = [i for i, status in enumerate(statuses) if status == "unhealthy"]
        degraded_indices = [i for i, status in enumerate(statuses) if status == "degraded"]
        healthy_indices = [i for i, status in enumerate(statuses) if status == "healthy"]
        
        # All unhealthy should come before degraded
        if unhealthy_indices and degraded_indices:
            assert max(unhealthy_indices) < min(degraded_indices)
        
        # All degraded should come before healthy
        if degraded_indices and healthy_indices:
            assert max(degraded_indices) < min(healthy_indices)
    
    @patch('lib.commands.environment_health.load_json')
    def test_check_environment_health_data_integrity(self, mock_load_json, sample_health_data):
        """Test that health data is returned intact without modification."""
        mock_load_json.return_value = sample_health_data
        result = check_environment_health()
            
        # Find the original unhealthy service (should be first due to sorting)
        original_unhealthy = next(h for h in sample_health_data["releaseHealth"] if h["status"] == "unhealthy")
        returned_unhealthy = result["health_checks"][0]  # Should be first due to sorting
        
        for key, value in original_unhealthy.items():
            assert returned_unhealthy[key] == value
    
    def test_determine_overall_status_unhealthy(self):
        """Test overall status determination with unhealthy services."""
        summary = {"healthy": 2, "degraded": 1, "unhealthy": 1}
        assert _determine_overall_status(summary) == "unhealthy"
    
    def test_determine_overall_status_degraded(self):
        """Test overall status determination with degraded services."""
        summary = {"healthy": 2, "degraded": 1, "unhealthy": 0}
        assert _determine_overall_status(summary) == "degraded"
    
    def test_determine_overall_status_healthy(self):
        """Test overall status determination with only healthy services."""
        summary = {"healthy": 3, "degraded": 0, "unhealthy": 0}
        assert _determine_overall_status(summary) == "healthy"
    
    def test_determine_overall_status_unknown(self):
        """Test overall status determination with no services."""
        summary = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        assert _determine_overall_status(summary) == "unknown"


class TestEnvironmentHealthCLI:
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
        assert args.env is None
        assert args.app is None
        assert args.format == 'json'
        assert args.verbose is False
        
        # Test environment filter
        args = parser.parse_args(['--env', 'prod'])
        assert args.env == 'prod'
        
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
        args = parser.parse_args(['--env', 'prod', '--app', 'web-app', '--format', 'table', '--verbose'])
        assert args.env == 'prod'
        assert args.app == 'web-app'
        assert args.format == 'table'
        assert args.verbose is True
    
    def test_argument_parsing_invalid_format(self):
        """Test handling of invalid format argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--format', 'invalid'])
    
    @patch('lib.commands.environment_health.check_environment_health')
    def test_main_success_json_output(self, mock_check_environment_health):
        """Test main function with successful JSON output."""
        mock_check_environment_health.return_value = {
            "status": "success",
            "health_checks": [{"id": "test"}],
            "total_count": 1,
            "summary": {"healthy": 1, "degraded": 0, "unhealthy": 0},
            "overall_status": "healthy"
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['environment_health', '--format', 'json']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate JSON output
        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert parsed["status"] == "success"
        assert parsed["total_count"] == 1
        assert parsed["overall_status"] == "healthy"
    
    @patch('lib.commands.environment_health.check_environment_health')
    def test_main_success_table_output(self, mock_check_environment_health):
        """Test main function with successful table output."""
        mock_check_environment_health.return_value = {
            "status": "success",
            "health_checks": [
                {
                    "applicationId": "web-app",
                    "environment": "prod",
                    "status": "healthy",
                    "uptime": 99.9,
                    "responseTime": 120,
                    "issues": 0
                }
            ],
            "total_count": 1,
            "summary": {"healthy": 1, "degraded": 0, "unhealthy": 0},
            "overall_status": "healthy"
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['environment_health', '--format', 'table']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate table formatting
        output = captured_output.getvalue()
        assert "Overall Status: HEALTHY" in output
        assert "Healthy: 1, Degraded: 0, Unhealthy: 0" in output
        assert "Application" in output  # Header present
        assert "Environment" in output  # Header present
        assert "Status" in output  # Header present
        assert "---" in output  # Separator present
        assert "web-app" in output  # Data present
        assert "Total: 1 health checks" in output  # Summary present
    
    @patch('lib.commands.environment_health.check_environment_health')
    def test_main_error_handling(self, mock_check_environment_health):
        """Test main function error handling and exit codes."""
        mock_check_environment_health.return_value = {
            "status": "error",
            "error": "Test error message",
            "health_checks": [],
            "total_count": 0,
            "summary": {"healthy": 0, "degraded": 0, "unhealthy": 0}
        }
        
        with patch('sys.argv', ['environment_health']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1  # Error exit code
    
    @patch('lib.commands.environment_health.check_environment_health')
    def test_main_with_filters(self, mock_check_environment_health):
        """Test main function passes filters correctly."""
        mock_check_environment_health.return_value = {
            "status": "success",
            "health_checks": [],
            "total_count": 0,
            "summary": {"healthy": 0, "degraded": 0, "unhealthy": 0},
            "overall_status": "unknown"
        }
        
        with patch('sys.argv', ['environment_health', '--env', 'prod', '--app', 'web-app']):
            try:
                main()
            except SystemExit:
                pass
        
        # Verify the function was called with correct parameters
        mock_check_environment_health.assert_called_once_with('prod', 'web-app')
    
    def test_print_table_success(self):
        """Test table printing with successful data."""
        result = {
            "status": "success",
            "health_checks": [
                {
                    "applicationId": "web-app",
                    "environment": "prod",
                    "status": "healthy",
                    "uptime": 99.9,
                    "responseTime": 120,
                    "issues": 0
                },
                {
                    "applicationId": "api-service",
                    "environment": "staging",
                    "status": "degraded",
                    "uptime": 95.5,
                    "responseTime": 300,
                    "issues": 2
                }
            ],
            "total_count": 2,
            "summary": {"healthy": 1, "degraded": 1, "unhealthy": 0},
            "overall_status": "degraded"
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        # Validate table structure and content
        assert "Overall Status: DEGRADED" in output
        assert "Healthy: 1, Degraded: 1, Unhealthy: 0" in output
        assert "Application" in output
        assert "Environment" in output
        assert "Status" in output
        assert "Uptime" in output
        assert "Response Time" in output
        assert "Issues" in output
        assert "---" in output  # Separator line
        assert "web-app" in output
        assert "api-service" in output
        assert "Total: 2 health checks" in output
    
    def test_print_table_error(self):
        """Test table printing with error data."""
        result = {
            "status": "error",
            "error": "Test error message",
            "health_checks": [],
            "total_count": 0
        }
        
        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            print_table(result)
        
        error_output = captured_error.getvalue()
        assert "Error: Test error message" in error_output
    
    def test_print_table_no_health_checks(self):
        """Test table printing with no health checks found."""
        result = {
            "status": "success",
            "health_checks": [],
            "total_count": 0
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        assert "No health checks found matching the criteria." in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
