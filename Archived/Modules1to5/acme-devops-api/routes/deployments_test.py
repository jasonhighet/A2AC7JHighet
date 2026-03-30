#!/usr/bin/env python3
"""
Tests for the deployments API endpoint.

This module contains tests for the FastAPI deployments endpoint,
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


class TestDeploymentsEndpoint:
    """Test cases for the deployments API endpoint."""
    
    @patch('routes.deployments.load_json')
    def test_get_deployments_success(self, mock_load_json):
        """Test successful deployments retrieval."""
        # Mock data
        mock_deployments_data = {
            'deployments': [
                {
                    'id': 'dep-001',
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'deployedAt': '2024-01-15T10:00:00Z',
                    'status': 'success'
                }
            ]
        }
        mock_config_data = {
            'applications': [
                {'id': 'web-app', 'name': 'Web Application'}
            ],
            'environments': [
                {'id': 'production', 'name': 'Production', 'url': 'https://prod.example.com'}
            ]
        }
        
        mock_load_json.side_effect = [mock_deployments_data, mock_config_data]
        
        # Make request
        response = client.get("/api/v1/deployments")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'deployments' in data['data']
        assert len(data['data']['deployments']) == 1
        assert data['data']['total'] == 1
        
    @patch('routes.deployments.load_json')
    def test_get_deployments_with_filters(self, mock_load_json):
        """Test deployments retrieval with filters."""
        # Mock data
        mock_deployments_data = {
            'deployments': [
                {
                    'id': 'dep-001',
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'deployedAt': '2024-01-15T10:00:00Z'
                },
                {
                    'id': 'dep-002',
                    'applicationId': 'api-service',
                    'environment': 'staging',
                    'deployedAt': '2024-01-15T09:00:00Z'
                }
            ]
        }
        mock_config_data = {
            'applications': [
                {'id': 'web-app', 'name': 'Web Application'},
                {'id': 'api-service', 'name': 'API Service'}
            ],
            'environments': [
                {'id': 'production', 'name': 'Production', 'url': 'https://prod.example.com'},
                {'id': 'staging', 'name': 'Staging', 'url': 'https://staging.example.com'}
            ]
        }
        
        mock_load_json.side_effect = [mock_deployments_data, mock_config_data]
        
        # Make request with filters
        response = client.get("/api/v1/deployments?application=web-app&environment=production")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['deployments']) == 1
        assert data['data']['deployments'][0]['applicationId'] == 'web-app'
        assert data['data']['deployments'][0]['environment'] == 'production'
        
    @patch('routes.deployments.load_json')
    def test_get_deployments_with_pagination(self, mock_load_json):
        """Test deployments retrieval with pagination."""
        # Mock data with multiple deployments
        mock_deployments_data = {
            'deployments': [
                {'id': f'dep-{i:03d}', 'applicationId': 'web-app', 'environment': 'production', 'deployedAt': f'2024-01-{15-i:02d}T10:00:00Z'}
                for i in range(10)
            ]
        }
        mock_config_data = {
            'applications': [{'id': 'web-app', 'name': 'Web Application'}],
            'environments': [{'id': 'production', 'name': 'Production', 'url': 'https://prod.example.com'}]
        }
        
        mock_load_json.side_effect = [mock_deployments_data, mock_config_data]
        
        # Make request with pagination
        response = client.get("/api/v1/deployments?limit=5&offset=2")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['limit'] == 5
        assert data['data']['offset'] == 2
        assert data['data']['returned'] == 5
        assert data['data']['total'] == 10
        assert data['data']['has_more']
        
    def test_get_deployments_invalid_pagination(self):
        """Test deployments retrieval with invalid pagination parameters."""
        # Test negative limit
        response = client.get("/api/v1/deployments?limit=-1")
        assert response.status_code == 422  # Validation error
        
        # Test negative offset
        response = client.get("/api/v1/deployments?offset=-1")
        assert response.status_code == 422  # Validation error
        
    @patch('routes.deployments.load_json')
    def test_get_deployments_data_loading_error(self, mock_load_json):
        """Test deployments retrieval when data loading fails."""
        mock_load_json.side_effect = Exception("Data loading failed")
        
        response = client.get("/api/v1/deployments")
        
        assert response.status_code == 500
        data = response.json()
        assert "Data loading error" in data['detail']
        
    @patch('routes.deployments.load_json')
    def test_get_deployments_empty_data(self, mock_load_json):
        """Test deployments retrieval with empty data."""
        mock_deployments_data = {'deployments': []}
        mock_config_data = {'applications': [], 'environments': []}
        
        mock_load_json.side_effect = [mock_deployments_data, mock_config_data]
        
        response = client.get("/api/v1/deployments")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['deployments']) == 0
        assert data['data']['total'] == 0


if __name__ == "__main__":
    pytest.main([__file__])
