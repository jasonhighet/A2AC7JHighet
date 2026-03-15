#!/usr/bin/env python3
"""
Tests for the logs API endpoint.

This module contains tests for the FastAPI logs endpoint,
testing the HTTP interface and response format.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

client = TestClient(app)


class TestLogsEndpoint:
    """Test cases for the logs API endpoint."""
    
    @patch('routes.logs.load_json')
    def test_get_logs_success(self, mock_load_json):
        """Test successful logs retrieval."""
        # Mock data
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'level': 'info',
                    'message': 'Application started successfully',
                    'source': 'application'
                }
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request
        response = client.get("/api/v1/logs")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'logs' in data['data']
        assert 'summary' in data['data']
        assert len(data['data']['logs']) == 1
        assert data['data']['total'] == 1
        
    @patch('routes.logs.load_json')
    def test_get_logs_with_filters(self, mock_load_json):
        """Test logs retrieval with filters."""
        # Mock data
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'level': 'error',
                    'message': 'Database connection failed',
                    'source': 'database'
                },
                {
                    'applicationId': 'api-service',
                    'environment': 'staging',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'level': 'info',
                    'message': 'Request processed',
                    'source': 'application'
                }
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request with filters
        response = client.get("/api/v1/logs?application=web-app&environment=production&level=error")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['logs']) == 1
        assert data['data']['logs'][0]['applicationId'] == 'web-app'
        assert data['data']['logs'][0]['environment'] == 'production'
        assert data['data']['logs'][0]['level'] == 'error'
        
    @patch('routes.logs.load_json')
    def test_get_logs_with_limit(self, mock_load_json):
        """Test logs retrieval with limit."""
        # Mock data with multiple logs
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': f'2024-01-15T{10+i:02d}:00:00Z',
                    'level': 'info',
                    'message': f'Log entry {i}',
                    'source': 'application'
                }
                for i in range(10)
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request with limit
        response = client.get("/api/v1/logs?limit=5")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['limit'] == 5
        assert data['data']['showing'] == 5
        assert data['data']['total'] == 10
        assert len(data['data']['logs']) == 5
        
    def test_get_logs_invalid_limit(self):
        """Test logs retrieval with invalid limit parameter."""
        # Test negative limit
        response = client.get("/api/v1/logs?limit=-1")
        assert response.status_code == 422  # Validation error
        
    @patch('routes.logs.load_json')
    def test_get_logs_summary_calculation(self, mock_load_json):
        """Test logs summary calculation."""
        # Mock data with different log levels
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'level': 'error',
                    'message': 'Error occurred',
                    'source': 'application'
                },
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'level': 'warn',
                    'message': 'Warning message',
                    'source': 'application'
                },
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T08:00:00Z',
                    'level': 'info',
                    'message': 'Info message',
                    'source': 'application'
                },
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T07:00:00Z',
                    'level': 'debug',
                    'message': 'Debug message',
                    'source': 'application'
                }
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request
        response = client.get("/api/v1/logs")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Check summary
        summary = data['data']['summary']
        assert summary['totalLogs'] == 4
        assert summary['errorLogs'] == 1
        assert summary['warnLogs'] == 1
        assert summary['infoLogs'] == 1
        assert summary['debugLogs'] == 1
        assert 'error' in summary['logLevels']
        assert 'warn' in summary['logLevels']
        assert 'info' in summary['logLevels']
        assert 'debug' in summary['logLevels']
        
    @patch('routes.logs.load_json')
    def test_get_logs_level_filtering(self, mock_load_json):
        """Test logs filtering by level."""
        # Mock data with different log levels
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'level': 'error',
                    'message': 'Error occurred',
                    'source': 'application'
                },
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'level': 'info',
                    'message': 'Info message',
                    'source': 'application'
                }
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request filtering by error level
        response = client.get("/api/v1/logs?level=error")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['logs']) == 1
        assert data['data']['logs'][0]['level'] == 'error'
        assert data['data']['total'] == 1  # Total after filtering
        
    @patch('routes.logs.load_json')
    def test_get_logs_data_loading_error(self, mock_load_json):
        """Test logs retrieval when data loading fails."""
        mock_load_json.side_effect = Exception("Data loading failed")
        
        response = client.get("/api/v1/logs")
        
        assert response.status_code == 500
        data = response.json()
        assert "Data loading error" in data['detail']
        
    @patch('routes.logs.load_json')
    def test_get_logs_empty_data(self, mock_load_json):
        """Test logs retrieval with empty data."""
        mock_logs_data = {'logs': []}
        
        mock_load_json.return_value = mock_logs_data
        
        response = client.get("/api/v1/logs")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['logs']) == 0
        assert data['data']['total'] == 0
        
        # Check that summary shows zero counts
        summary = data['data']['summary']
        assert summary['totalLogs'] == 0
        assert summary['errorLogs'] == 0
        assert summary['warnLogs'] == 0
        assert summary['infoLogs'] == 0
        assert summary['debugLogs'] == 0
        assert summary['logLevels'] == []
        
    @patch('routes.logs.load_json')
    def test_get_logs_metadata(self, mock_load_json):
        """Test logs metadata in response."""
        # Mock data
        mock_logs_data = {
            'logs': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'level': 'info',
                    'message': 'Application started',
                    'source': 'application'
                },
                {
                    'applicationId': 'api-service',
                    'environment': 'staging',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'level': 'error',
                    'message': 'Database error',
                    'source': 'database'
                }
            ]
        }
        
        mock_load_json.return_value = mock_logs_data
        
        # Make request
        response = client.get("/api/v1/logs")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Check metadata
        metadata = data['data']['metadata']
        assert metadata['totalApplications'] == 2
        assert metadata['totalEnvironments'] == 2
        assert metadata['timeRange'] == 'recent'
        assert 'application' in metadata['sources']
        assert 'database' in metadata['sources']


if __name__ == "__main__":
    pytest.main([__file__])
