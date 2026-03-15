#!/usr/bin/env python3
"""
Tests for the metrics API endpoint.

This module contains tests for the FastAPI metrics endpoint,
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


class TestMetricsEndpoint:
    """Test cases for the metrics API endpoint."""
    
    @patch('routes.metrics.load_json')
    def test_get_metrics_success(self, mock_load_json):
        """Test successful metrics retrieval."""
        # Mock data
        mock_metrics_data = {
            'metrics': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'cpu': 45.2,
                    'memory': 67.8,
                    'requests': 1250,
                    'errors': 5
                }
            ]
        }
        
        mock_load_json.return_value = mock_metrics_data
        
        # Make request
        response = client.get("/api/v1/metrics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert 'data' in data
        assert 'metrics' in data['data']
        assert 'aggregations' in data['data']
        assert len(data['data']['metrics']) == 1
        assert data['data']['total'] == 1
        
    @patch('routes.metrics.load_json')
    def test_get_metrics_with_filters(self, mock_load_json):
        """Test metrics retrieval with filters."""
        # Mock data
        mock_metrics_data = {
            'metrics': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'cpu': 45.2,
                    'memory': 67.8,
                    'requests': 1250,
                    'errors': 5
                },
                {
                    'applicationId': 'api-service',
                    'environment': 'staging',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'cpu': 32.1,
                    'memory': 54.3,
                    'requests': 890,
                    'errors': 2
                }
            ]
        }
        
        mock_load_json.return_value = mock_metrics_data
        
        # Make request with filters
        response = client.get("/api/v1/metrics?application=web-app&environment=production")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['metrics']) == 1
        assert data['data']['metrics'][0]['applicationId'] == 'web-app'
        assert data['data']['metrics'][0]['environment'] == 'production'
        
    @patch('routes.metrics.load_json')
    def test_get_metrics_with_time_range(self, mock_load_json):
        """Test metrics retrieval with time range."""
        # Mock data
        mock_metrics_data = {
            'metrics': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'cpu': 45.2,
                    'memory': 67.8,
                    'requests': 1250,
                    'errors': 5
                }
            ]
        }
        
        mock_load_json.return_value = mock_metrics_data
        
        # Make request with time range
        response = client.get("/api/v1/metrics?time_range=7d")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['metadata']['timeRange'] == '7d'
        
    @patch('routes.metrics.load_json')
    def test_get_metrics_aggregations(self, mock_load_json):
        """Test metrics aggregations calculation."""
        # Mock data with multiple metrics for aggregation
        mock_metrics_data = {
            'metrics': [
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T10:00:00Z',
                    'cpu': 40.0,
                    'memory': 60.0,
                    'requests': 1000,
                    'errors': 5
                },
                {
                    'applicationId': 'web-app',
                    'environment': 'production',
                    'timestamp': '2024-01-15T09:00:00Z',
                    'cpu': 50.0,
                    'memory': 70.0,
                    'requests': 1200,
                    'errors': 3
                }
            ]
        }
        
        mock_load_json.return_value = mock_metrics_data
        
        # Make request
        response = client.get("/api/v1/metrics")
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        
        # Check aggregations
        agg = data['data']['aggregations']
        assert agg['cpu']['avg'] == 45.0  # (40 + 50) / 2
        assert agg['cpu']['min'] == 40.0
        assert agg['cpu']['max'] == 50.0
        assert agg['memory']['avg'] == 65.0  # (60 + 70) / 2
        assert agg['requests']['avg'] == 1100.0  # (1000 + 1200) / 2
        
    @patch('routes.metrics.load_json')
    def test_get_metrics_data_loading_error(self, mock_load_json):
        """Test metrics retrieval when data loading fails."""
        mock_load_json.side_effect = Exception("Data loading failed")
        
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 500
        data = response.json()
        assert "Data loading error" in data['detail']
        
    @patch('routes.metrics.load_json')
    def test_get_metrics_empty_data(self, mock_load_json):
        """Test metrics retrieval with empty data."""
        mock_metrics_data = {'metrics': []}
        
        mock_load_json.return_value = mock_metrics_data
        
        response = client.get("/api/v1/metrics")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert len(data['data']['metrics']) == 0
        assert data['data']['total'] == 0
        
        # Check that aggregations are zero for empty data
        agg = data['data']['aggregations']
        assert agg['cpu']['avg'] == 0.0
        assert agg['memory']['avg'] == 0.0
        assert agg['requests']['avg'] == 0.0
        assert agg['errors']['avg'] == 0.0


if __name__ == "__main__":
    pytest.main([__file__])
