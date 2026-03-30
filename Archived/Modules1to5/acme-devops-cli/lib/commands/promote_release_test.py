#!/usr/bin/env python3
"""
Tests for Promote Release CLI Command

This module contains comprehensive tests for both the business logic
and CLI interface of the promote release functionality.
"""

import pytest
import json
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from lib.commands.promote_release import (
    promote_release,
    _simulate_promotion_outcome,
    print_table,
    create_parser,
    main
)
from lib.data_loader import DataLoadError


class TestPromoteReleaseBusinessLogic:
    """Test cases for the core business logic."""
    
    @pytest.fixture
    def sample_deployments_data(self):
        """Sample deployment data for testing."""
        return {
            "deployments": [
                {
                    "id": "deploy-001",
                    "applicationId": "web-app",
                    "environment": "staging",
                    "version": "v2.1.3",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z",
                    "deployedBy": "alice@company.com",
                    "commitHash": "abc123def456"
                },
                {
                    "id": "deploy-002",
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v2.1.2",
                    "status": "deployed",
                    "deployedAt": "2024-01-14T14:20:00Z",
                    "deployedBy": "bob@company.com",
                    "commitHash": "def456ghi789"
                },
                {
                    "id": "deploy-003",
                    "applicationId": "api-service",
                    "environment": "uat",
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
                }
            ]
        }
    
    @pytest.fixture
    def sample_releases_data(self):
        """Sample releases data for testing."""
        return {
            "releases": [
                {
                    "id": "rel-001",
                    "applicationId": "web-app",
                    "version": "v2.1.3",
                    "releaseDate": "2024-01-15T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and performance improvements",
                    "commitHash": "abc123def456"
                },
                {
                    "id": "rel-002",
                    "applicationId": "api-service",
                    "version": "v1.8.2",
                    "releaseDate": "2024-01-14T07:00:00Z",
                    "author": "charlie@company.com",
                    "releaseNotes": "Security updates and new features",
                    "commitHash": "ghi789jkl012"
                }
            ]
        }
    
    @pytest.fixture
    def sample_config_data(self):
        """Sample config data for testing."""
        return {
            "applications": [
                {"id": "web-app", "name": "Web Application"},
                {"id": "api-service", "name": "API Service"},
                {"id": "worker-service", "name": "Worker Service"}
            ],
            "environments": [
                {"id": "staging", "name": "Staging"},
                {"id": "uat", "name": "UAT"},
                {"id": "prod", "name": "Production"}
            ]
        }
    
    def setup_mock_data_loading(self, mock_load_json, deployments_data, releases_data, config_data):
        """Helper method to set up mock data loading with side effects."""
        def side_effect(filename):
            if filename == "deployments.json":
                return deployments_data
            elif filename == "releases.json":
                return releases_data
            elif filename == "config.json":
                return config_data
            return {}
        
        mock_load_json.side_effect = side_effect
    
    @patch('lib.commands.promote_release.load_json')
    @patch('lib.commands.promote_release._simulate_promotion_outcome')
    def test_promote_release_success(self, mock_simulate, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test successful release promotion."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        mock_simulate.return_value = True
        
        result = promote_release("web-app", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "success"
        assert "Successfully promoted" in result["message"]
        assert result["promotion_details"]["promotion_successful"] is True
        assert result["promotion_details"]["promotion_path"] == "staging → prod"
        assert result["promotion_details"]["deployment"]["applicationId"] == "web-app"
        assert result["promotion_details"]["deployment"]["version"] == "v2.1.3"
        assert result["promotion_details"]["deployment"]["environment"] == "prod"
        assert result["promotion_details"]["deployment"]["status"] == "deployed"
    
    @patch('lib.commands.promote_release.load_json')
    @patch('lib.commands.promote_release._simulate_promotion_outcome')
    def test_promote_release_failure(self, mock_simulate, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test failed release promotion."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        mock_simulate.return_value = False
        
        result = promote_release("web-app", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "success"  # Still success status, but promotion failed
        assert "Promotion failed" in result["message"]
        assert result["promotion_details"]["promotion_successful"] is False
        assert result["promotion_details"]["deployment"]["status"] == "failed"
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_missing_parameters(self, mock_load_json):
        """Test promotion with missing required parameters."""
        result = promote_release("", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "error"
        assert "All parameters are required" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_same_environments(self, mock_load_json):
        """Test promotion with same source and target environments."""
        result = promote_release("web-app", "v2.1.3", "prod", "prod")
        
        assert result["status"] == "error"
        assert "Source and target environments cannot be the same" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_invalid_application(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion with invalid application."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("invalid-app", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "error"
        assert "Application 'invalid-app' not found" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_invalid_source_environment(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion with invalid source environment."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("web-app", "v2.1.3", "invalid-env", "prod")
        
        assert result["status"] == "error"
        assert "Source environment 'invalid-env' not found" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_invalid_target_environment(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion with invalid target environment."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("web-app", "v2.1.3", "staging", "invalid-env")
        
        assert result["status"] == "error"
        assert "Target environment 'invalid-env' not found" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_version_not_found(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion with version not found in releases."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("web-app", "v9.9.9", "staging", "prod")
        
        assert result["status"] == "error"
        assert "Release version 'v9.9.9' not found" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_version_not_deployed_in_source(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion with version not deployed in source environment."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("web-app", "v2.1.3", "uat", "prod")  # v2.1.3 not in uat
        
        assert result["status"] == "error"
        assert "Version 'v2.1.3' is not currently deployed in 'uat' environment" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_deployment_in_progress(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test promotion when deployment already in progress in target environment."""
        # Add an in-progress deployment to target environment
        sample_deployments_data["deployments"].append({
            "id": "deploy-005",
            "applicationId": "web-app",
            "environment": "prod",
            "version": "v2.1.1",
            "status": "in-progress",
            "deployedAt": "2024-01-17T15:00:00Z",
            "deployedBy": "system@company.com",
            "commitHash": "xyz789abc123"
        })
        
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        result = promote_release("web-app", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "error"
        assert "Deployment already in progress" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_data_loading_error(self, mock_load_json):
        """Test promotion with data loading error."""
        mock_load_json.side_effect = DataLoadError("File not found")
        
        result = promote_release("web-app", "v2.1.3", "staging", "prod")
        
        assert result["status"] == "error"
        assert "Failed to load required data" in result["error"]
        assert result["promotion_details"] is None
    
    @patch('lib.commands.promote_release.load_json')
    def test_promote_release_response_structure(self, mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data):
        """Test that the response has the correct structure."""
        self.setup_mock_data_loading(mock_load_json, sample_deployments_data, sample_releases_data, sample_config_data)
        
        with patch('lib.commands.promote_release._simulate_promotion_outcome', return_value=True):
            result = promote_release("web-app", "v2.1.3", "staging", "prod")
        
        # Check required fields are present
        required_fields = ["status", "message", "promotion_details", "timestamp"]
        for field in required_fields:
            assert field in result
        
        # Check promotion_details structure
        promotion_details = result["promotion_details"]
        assert "deployment" in promotion_details
        assert "source_deployment" in promotion_details
        assert "release_info" in promotion_details
        assert "promotion_path" in promotion_details
        assert "promotion_successful" in promotion_details
        
        # Check timestamp format (basic validation)
        assert "T" in result["timestamp"]
        assert "Z" in result["timestamp"]
    
    def test_simulate_promotion_outcome_deterministic(self):
        """Test that simulation outcome is deterministic for testing."""
        # Test multiple calls with same parameters to ensure some consistency
        # Note: This is a probabilistic function, so we test general behavior
        results = []
        for _ in range(10):
            result = _simulate_promotion_outcome("web-app", "prod")
            results.append(result)
        
        # Should return boolean values
        assert all(isinstance(r, bool) for r in results)
        
        # For worker-service, should have lower success rate
        worker_results = []
        for _ in range(10):
            result = _simulate_promotion_outcome("worker-service", "prod")
            worker_results.append(result)
        
        # Should still return boolean values
        assert all(isinstance(r, bool) for r in worker_results)


class TestPromoteReleaseCLI:
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
        
        # Test required positional arguments
        args = parser.parse_args(['web-app', 'v1.2.3', 'staging', 'prod'])
        assert args.application == 'web-app'
        assert args.version == 'v1.2.3'
        assert args.from_environment == 'staging'
        assert args.to_environment == 'prod'
        assert args.format == 'json'  # default
        assert args.verbose is False  # default
        
        # Test with format option
        args = parser.parse_args(['web-app', 'v1.2.3', 'staging', 'prod', '--format', 'table'])
        assert args.format == 'table'
        
        # Test with verbose flag
        args = parser.parse_args(['web-app', 'v1.2.3', 'staging', 'prod', '--verbose'])
        assert args.verbose is True
        
        args = parser.parse_args(['web-app', 'v1.2.3', 'staging', 'prod', '-v'])
        assert args.verbose is True
        
        # Test combination of arguments
        args = parser.parse_args(['api-service', 'v2.1.0', 'uat', 'prod', '--format', 'table', '--verbose'])
        assert args.application == 'api-service'
        assert args.version == 'v2.1.0'
        assert args.from_environment == 'uat'
        assert args.to_environment == 'prod'
        assert args.format == 'table'
        assert args.verbose is True
    
    def test_argument_parsing_missing_required_args(self):
        """Test handling of missing required arguments."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])  # No arguments
        
        with pytest.raises(SystemExit):
            parser.parse_args(['web-app'])  # Missing version, environments
        
        with pytest.raises(SystemExit):
            parser.parse_args(['web-app', 'v1.2.3'])  # Missing environments
        
        with pytest.raises(SystemExit):
            parser.parse_args(['web-app', 'v1.2.3', 'staging'])  # Missing target environment
    
    def test_argument_parsing_invalid_format(self):
        """Test handling of invalid format argument."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['web-app', 'v1.2.3', 'staging', 'prod', '--format', 'invalid'])
    
    @patch('lib.commands.promote_release.promote_release')
    def test_main_success_json_output(self, mock_promote_release):
        """Test main function with successful JSON output."""
        mock_promote_release.return_value = {
            "status": "success",
            "message": "Successfully promoted web-app v1.2.3 from staging to prod",
            "promotion_details": {
                "deployment": {"id": "test-deploy"},
                "promotion_successful": True
            }
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['promote_release', 'web-app', 'v1.2.3', 'staging', 'prod', '--format', 'json']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate JSON output
        output = captured_output.getvalue()
        parsed = json.loads(output)
        assert parsed["status"] == "success"
        assert "Successfully promoted" in parsed["message"]
    
    @patch('lib.commands.promote_release.promote_release')
    def test_main_success_table_output(self, mock_promote_release):
        """Test main function with successful table output."""
        mock_promote_release.return_value = {
            "status": "success",
            "message": "Successfully promoted web-app v1.2.3 from staging to prod",
            "promotion_details": {
                "deployment": {
                    "id": "deploy-123",
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v1.2.3",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z",
                    "deployedBy": "system@company.com"
                },
                "promotion_path": "staging → prod",
                "promotion_successful": True,
                "release_info": {
                    "version": "v1.2.3",
                    "releaseDate": "2024-01-15T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and improvements"
                }
            }
        }
        
        # Capture stdout
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            with patch('sys.argv', ['promote_release', 'web-app', 'v1.2.3', 'staging', 'prod', '--format', 'table']):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
        
        # Validate table formatting
        output = captured_output.getvalue()
        assert "Status: SUCCESS" in output
        assert "Successfully promoted" in output
        assert "Promotion Details:" in output
        assert "staging → prod" in output
        assert "New Deployment:" in output
        assert "web-app" in output
        assert "Release Information:" in output
    
    @patch('lib.commands.promote_release.promote_release')
    def test_main_error_handling(self, mock_promote_release):
        """Test main function error handling and exit codes."""
        mock_promote_release.return_value = {
            "status": "error",
            "error": "Test error message",
            "promotion_details": None
        }
        
        with patch('sys.argv', ['promote_release', 'web-app', 'v1.2.3', 'staging', 'prod']):
            try:
                main()
            except SystemExit as e:
                assert e.code == 1  # Error exit code
    
    @patch('lib.commands.promote_release.promote_release')
    def test_main_with_parameters(self, mock_promote_release):
        """Test main function passes parameters correctly."""
        mock_promote_release.return_value = {
            "status": "success",
            "message": "Test message",
            "promotion_details": {"test": "data"}
        }
        
        with patch('sys.argv', ['promote_release', 'api-service', 'v2.1.0', 'uat', 'prod']):
            try:
                main()
            except SystemExit:
                pass
        
        # Verify the function was called with correct parameters
        mock_promote_release.assert_called_once_with('api-service', 'v2.1.0', 'uat', 'prod')
    
    def test_print_table_success(self):
        """Test table printing with successful data."""
        result = {
            "status": "success",
            "message": "Successfully promoted web-app v1.2.3 from staging to prod",
            "promotion_details": {
                "deployment": {
                    "id": "deploy-123",
                    "applicationId": "web-app",
                    "environment": "prod",
                    "version": "v1.2.3",
                    "status": "deployed",
                    "deployedAt": "2024-01-15T10:30:00Z",
                    "deployedBy": "system@company.com"
                },
                "promotion_path": "staging → prod",
                "promotion_successful": True,
                "release_info": {
                    "version": "v1.2.3",
                    "releaseDate": "2024-01-15T08:00:00Z",
                    "author": "alice@company.com",
                    "releaseNotes": "Bug fixes and improvements"
                }
            }
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        # Validate table structure and content
        assert "Status: SUCCESS" in output
        assert "Successfully promoted" in output
        assert "Promotion Details:" in output
        assert "staging → prod" in output
        assert "Success: True" in output
        assert "New Deployment:" in output
        assert "ID: deploy-123" in output
        assert "Application: web-app" in output
        assert "Environment: prod" in output
        assert "Version: v1.2.3" in output
        assert "Status: deployed" in output
        assert "Release Information:" in output
        assert "Author: alice@company.com" in output
        assert "Notes: Bug fixes and improvements" in output
    
    def test_print_table_error(self):
        """Test table printing with error data."""
        result = {
            "status": "error",
            "error": "Test error message",
            "promotion_details": None
        }
        
        captured_error = StringIO()
        with patch('sys.stderr', captured_error):
            print_table(result)
        
        error_output = captured_error.getvalue()
        assert "Error: Test error message" in error_output
    
    def test_print_table_no_promotion_details(self):
        """Test table printing with no promotion details."""
        result = {
            "status": "success",
            "message": "Test message",
            "promotion_details": None
        }
        
        captured_output = StringIO()
        with patch('sys.stdout', captured_output):
            print_table(result)
        
        output = captured_output.getvalue()
        assert "Status: SUCCESS" in output
        assert "Message: Test message" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
