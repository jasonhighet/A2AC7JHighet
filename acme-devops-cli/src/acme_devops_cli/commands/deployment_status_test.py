#!/usr/bin/env python3
"""
Tests for Deployment Status CLI Command

This module contains comprehensive tests for both the business logic
and CLI interface of the deployment status functionality.
"""

import pytest
import json
from io import StringIO
from unittest.mock import patch

from lib.commands.deployment_status import (
    get_deployment_status,
    print_table,
    create_parser,
    main
)
from lib.data_loader import DataLoadError


class TestDeploymentStatusBusinessLogic:
    """Test cases for the core business logic."""
    
    @pytest.fixture
    def sample_deployments_data(self):
        """Sample deployment data for testing - matches the JSON file structure."""
        return {
            "deployments": [
                {
                    "id": "deploy-001",
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v2.1.3",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z",
                    "deployedBy": "alice@company.com",
                    "commitHash": "abc123def456"
                },
                {
                    "id": "deploy-002",
                    "applicationId": "web-app",
                    "environment": "uat",
                    "version": "v2.1.4",
                    "status": "deployed",
                    "deployedAt": "2024-01-16T14:20:00Z",
                    "deployedBy": "bob@company.com",
                    "commitHash": "def456ghi789"
                },
                {
                    "id": "deploy-003",
                    "applicationId": "api-service",
                    "environment": "prod",
                    "version": "v1.8.2",
                    "status": "deployed",
                    "deployedAt": "2024-01-14T09:15:00Z",
                    "deployedBy": "charlie@company.com",
                    "commitHash": "ghi789jkl012"
                },
                {
                    "id": "deploy-004",
                    "applicationId": "api-service",
                    "environment": "staging",
                    "version": "v1.9.0",
                    "status": "in-progress",
                    "deployedAt": "2024-01-17T11:45:00Z",
                    "deployedBy": "alice@company.com",
                    "commitHash": "jkl012mno345"
                },
                {
                    "id": "deploy-005",
                    "applicationId": "worker-service",
                    "environment": "prod",
                    "version": "v3.2.1",
                    "status": "failed",
                    "deployedAt": "2024-01-16T16:30:00Z",
                    "deployedBy": "diana@company.com",
                    "commitHash": "mno345pqr678"
                },
                {
                    "id": "deploy-006",
                    "applicationId": "analytics-dashboard",
                    "environment": "uat",
                    "version": "v1.5.0",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T13:00:00Z",
                    "deployedBy": "eve@company.com",
                    "commitHash": "pqr678stu901"
                }
            ]
        }
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_no_filters(self, mock_load_json, sample_deployments_data):
        """Test getting all deployments without filters."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status()

        assert result["status"] == "success"
        assert len(result["deployments"]) == 6
        assert result["total_count"] == 6
        assert result["filters_applied"]["application"] is None
        assert result["filters_applied"]["environment"] is None
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_filter_by_application(self, mock_load_json, sample_deployments_data):
        """Test filtering deployments by application."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status(application="web-app")
            
        assert result["status"] == "success"
        assert len(result["deployments"]) == 2
        assert result["total_count"] == 2
        assert all(d["applicationId"] == "web-app" for d in result["deployments"])
        assert result["filters_applied"]["application"] == "web-app"
        assert result["filters_applied"]["environment"] is None
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_filter_by_environment(self, mock_load_json, sample_deployments_data):
        """Test filtering deployments by environment."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status(environment="prod")
            
        assert result["status"] == "success"
        assert len(result["deployments"]) == 3
        assert result["total_count"] == 3
        assert all(d["environment"] == "prod" for d in result["deployments"])
        assert result["filters_applied"]["application"] is None
        assert result["filters_applied"]["environment"] == "prod"
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_filter_by_both(self, mock_load_json, sample_deployments_data):
        """Test filtering deployments by both application and environment."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status(application="web-app", environment="prod")
            
        assert result["status"] == "success"
        assert len(result["deployments"]) == 1
        assert result["total_count"] == 1
        assert result["deployments"][0]["applicationId"] == "web-app"
        assert result["deployments"][0]["environment"] == "prod"
        assert result["filters_applied"]["application"] == "web-app"
        assert result["filters_applied"]["environment"] == "prod"
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_no_matches(self, mock_load_json, sample_deployments_data):
        """Test filtering with no matching results."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status(application="nonexistent-app")
            
        assert result["status"] == "success"
        assert len(result["deployments"]) == 0
        assert result["total_count"] == 0
        assert result["filters_applied"]["application"] == "nonexistent-app"
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_no_data_available(self, mock_load_json):
        """Test handling when no deployment data is available."""
        empty_data = {"deployments": []}
        mock_load_json.return_value = empty_data
        result = get_deployment_status()
            
        assert result["status"] == "error"
        assert result["error"] == "No deployment data available"
        assert len(result["deployments"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_data_loading_error(self, mock_load_json):
        """Test handling when data loading raises an exception."""
        mock_load_json.side_effect = DataLoadError("File not found")
        result = get_deployment_status()
            
        assert result["status"] == "error"
        assert "Failed to load deployment data" in result["error"]
        assert len(result["deployments"]) == 0
        assert result["total_count"] == 0
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_response_structure(self, mock_load_json, sample_deployments_data):
        """Test that the response has the correct structure."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status()
            
        # Check required fields are present
        required_fields = ["status", "deployments", "total_count", "filters_applied", "timestamp"]
        for field in required_fields:
            assert field in result
        
        # Check filters_applied structure
        assert "application" in result["filters_applied"]
        assert "environment" in result["filters_applied"]
        
        # Check timestamp format (basic validation)
        assert "T" in result["timestamp"]
        assert "Z" in result["timestamp"]
    
    @patch('lib.commands.deployment_status.load_json')
    def test_get_deployment_status_deployment_data_integrity(self, mock_load_json, sample_deployments_data):
        """Test that deployment data is returned intact without modification."""
        mock_load_json.return_value = sample_deployments_data
        result = get_deployment_status()
            
        # Verify that the original deployment data is preserved
        returned_deployment = result["deployments"][0]
        original_deployment = sample_deployments_data["deployments"][0]
        
        for key, value in original_deployment.items():
            assert returned_deployment[key] == value


class TestDeploymentStatusCLI:
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
        assert args.app is None
        assert args.env is None
        assert args.format == 'json'
        assert args.verbose is False
        
        # Test application filter
        args = parser.parse_args(['--app', 'web-app'])
        assert args.app == 'web-app'
        
        # Test environment filter
        args = parser.parse_args(['--env', 'prod'])
        assert args.env == 'prod'
        
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
        args = parser.parse_args(['--app', 'web-app', '--env', 'prod', '--format', 'table', '--verbose'])
        assert args.app == 'web-app'
        assert args.env == 'prod'
        assert args.format == 'table'
        assert args.verbose is True
    
    def test_argument_parsing_invalid_format(self):
        """Test handling of invalid format argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--format', 'invalid'])
    
    @patch('lib.commands.deployment_status.get_deployment_status')
    def test_main_success_json_output(self, mock_get_deployment_status):
        """Test main function with successful JSON output."""
        mock_get_deployment_status.return_value = {
            "status": "success",
            "deployments": [{"id": "test"}],
            "total_count": 1
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['deployment_status', '--format', 'json']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate JSON output
        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert parsed["status"] == "success"
        assert parsed["total_count"] == 1
    
    @patch('lib.commands.deployment_status.get_deployment_status')
    def test_main_success_table_output(self, mock_get_deployment_status):
        """Test main function with successful table output."""
        mock_get_deployment_status.return_value = {
            "status": "success",
            "deployments": [
                {
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v1.0.0",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z"
                }
            ],
            "total_count": 1
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['deployment_status', '--format', 'table']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate table formatting
        output = captured_output.getvalue()
        assert "Application" in output  # Header present
        assert "Environment" in output  # Header present
        assert "---" in output  # Separator present
        assert "web-app" in output  # Data present
        assert "Total: 1 deployments" in output  # Summary present
    
    @patch('lib.commands.deployment_status.get_deployment_status')
    def test_main_error_handling(self, mock_get_deployment_status):
        """Test main function error handling and exit codes."""
        mock_get_deployment_status.return_value = {
            "status": "error",
            "error": "Test error message",
            "deployments": [],
            "total_count": 0
        }
        
        with patch('sys.argv', ['deployment_status']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1  # Error exit code
    
    @patch('lib.commands.deployment_status.get_deployment_status')
    def test_main_with_filters(self, mock_get_deployment_status):
        """Test main function passes filters correctly."""
        mock_get_deployment_status.return_value = {
            "status": "success",
            "deployments": [],
            "total_count": 0
        }
        
        with patch('sys.argv', ['deployment_status', '--app', 'web-app', '--env', 'prod']):
            try:
                main()
            except SystemExit:
                pass
        
        # Verify the function was called with correct parameters
        mock_get_deployment_status.assert_called_once_with('web-app', 'prod')
    
    def test_print_table_success(self):
        """Test table printing with successful data."""
        result = {
            "status": "success",
            "deployments": [
                {
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v1.0.0",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z"
                },
                {
                    "applicationId": "api-service",
                    "environment": "staging",
                    "version": "v2.1.0",
                    "status": "in-progress",
                    "deployedAt": "2024-01-16T14:20:00Z"
                }
            ],
            "total_count": 2
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        # Validate table structure and content
        assert "Application" in output
        assert "Environment" in output
        assert "Version" in output
        assert "Status" in output
        assert "Deployed At" in output
        assert "---" in output  # Separator line
        assert "web-app" in output
        assert "api-service" in output
        assert "Total: 2 deployments" in output
    
    def test_print_table_error(self):
        """Test table printing with error data."""
        result = {
            "status": "error",
            "error": "Test error message",
            "deployments": [],
            "total_count": 0
        }
        
        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            print_table(result)
        
        error_output = captured_error.getvalue()
        assert "Error: Test error message" in error_output
    
    def test_print_table_no_deployments(self):
        """Test table printing with no deployments found."""
        result = {
            "status": "success",
            "deployments": [],
            "total_count": 0
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        assert "No deployments found matching the criteria." in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
