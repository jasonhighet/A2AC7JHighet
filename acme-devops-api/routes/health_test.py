#!/usr/bin/env python3
"""
Tests for the health API endpoint.

This module contains tests for the FastAPI health endpoint,
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


class TestHealthEndpoint:
    """Test cases for the health API endpoint."""
    
    @patch('routes.health.load_json')
    def test_get_health_success(self, mock_load_json):
        """Test successful health status retrieval."""
        # Mock data
        mock_health_data = {
            'environmentHealth': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'status': 'healthy',
                    'lastChecked': '2024-01-15T10:00:00Z',
                    'responseTime': 150
                }
            ]
        }
        
        mock_load_json.return_value = mock_health_data
        
        # Make request
        response = client.get("/api/v1/health")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'healthStatus' in data['data']
        assert 'summary' in data['data']
        assert len(data['data']['healthStatus']) == 1
        assert data['data']['total'] == 1
        
    @patch('routes.health.load_json')
    def test_get_health_with_filters(self, mock_load_json):
        """Test health status retrieval with filters."""
        # Mock data
        mock_health_data = {
            'environmentHealth': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'status': 'healthy',
                    'lastChecked': '2024-01-15T10:00:00Z'
                },
                {
                    'applicationId': 'api-service',
                    'environment': 'staging',
                    'status': 'degraded',
                    'lastChecked': '2024-01-15T09:00:00Z'
                }
            ]
        }
        
        mock_load_json.return_value = mock_health_data
        
        # Make request with filters
        response = client.get("/api/v1/health?application=web-app&environment=production")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['healthStatus']) == 1
        assert data['data']['healthStatus'][0]['applicationId'] == 'web-app'
        assert data['data']['healthStatus'][0]['environment'] == 'production'
        
    @patch('routes.health.load_json')
    def test_get_health_with_detailed_flag(self, mock_load_json):
        """Test health status retrieval with detailed flag."""
        # Mock data
        mock_health_data = {
            'environmentHealth': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'status': 'healthy',
                    'lastChecked': '2024-01-15T10:00:00Z',
                    'responseTime': 150,
                    'details': {'cpu': 45.2, 'memory': 67.8}
                }
            ]
        }
        
        mock_load_json.return_value = mock_health_data
        
        # Make request with detailed flag
        response = client.get("/api/v1/health?detailed=true")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['metadata']['detailed']
        
    @patch('routes.health.load_json')
    def test_get_health_summary_calculation(self, mock_load_json):
        """Test health summary calculation."""
        # Mock data with mixed health statuses
        mock_health_data = {
            'environmentHealth': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'status': 'healthy',
                    'lastChecked': '2024-01-15T10:00:00Z'
                },
                {
                    'applicationId': 'api-service',
                    'environment': 'production',
                    'status': 'degraded',
                    'lastChecked': '2024-01-15T09:00:00Z'
                },
                {
                    'applicationId': 'db-service',
                    'environment': 'production',
                    'status': 'unhealthy',
                    'lastChecked': '2024-01-15T08:00:00Z'
                }
            ]
        }
        
        mock_load_json.return_value = mock_health_data
        
        # Make request
        response = client.get("/api/v1/health")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Check summary
        summary = data['data']['summary']
        assert summary['totalServices'] == 3
        assert summary['healthyServices'] == 1
        assert summary['degradedServices'] == 1
        assert summary['unhealthyServices'] == 1
        assert summary['overallStatus'] == 'unhealthy'  # Worst status wins
        
    @patch('routes.health.load_json')
    def test_get_health_overall_status_logic(self, mock_load_json):
        """Test overall status calculation logic."""
        # Test healthy only
        mock_health_data = {
            'environmentHealth': [
                {'status': 'healthy', 'applicationId': 'app1', 'environment': 'prod', 'lastChecked': '2024-01-15T10:00:00Z'},
                {'status': 'healthy', 'applicationId': 'app2', 'environment': 'prod', 'lastChecked': '2024-01-15T10:00:00Z'}
            ]
        }
        mock_load_json.return_value = mock_health_data
        
        response = client.get("/api/v1/health")
        data = response.json()
        assert data['data']['summary']['overallStatus'] == 'healthy'
        
        # Test with degraded (no unhealthy)
        mock_health_data['environmentHealth'][1]['status'] = 'degraded'
        mock_load_json.return_value = mock_health_data
        
        response = client.get("/api/v1/health")
        data = response.json()
        assert data['data']['summary']['overallStatus'] == 'degraded'
        
    @patch('routes.health.load_json')
    def test_get_health_data_loading_error(self, mock_load_json):
        """Test health status retrieval when data loading fails."""
        mock_load_json.side_effect = Exception("Data loading failed")
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 500
        data = response.json()
        assert "Data loading error" in data['detail']
        
    @patch('routes.health.load_json')
    def test_get_health_empty_data(self, mock_load_json):
        """Test health status retrieval with empty data."""
        mock_health_data = {'environmentHealth': []}
        
        mock_load_json.return_value = mock_health_data
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['healthStatus']) == 0
        assert data['data']['total'] == 0
        
        # Check that summary shows zero counts
        summary = data['data']['summary']
        assert summary['totalServices'] == 0
        assert summary['healthyServices'] == 0
        assert summary['degradedServices'] == 0
        assert summary['unhealthyServices'] == 0
        assert summary['overallStatus'] == 'unknown'


if __name__ == "__main__":
    pytest.main([__file__])
