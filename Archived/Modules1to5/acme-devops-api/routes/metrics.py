"""
Metrics FastAPI endpoint implementation.

This module provides the /api/v1/metrics endpoint for the DevOps Dashboard API.
It handles performance metrics and monitoring data with filtering and aggregation capabilities.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Import our local data loader
from lib.data_loader import load_json

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


class MetricAggregation(BaseModel):
    """Aggregation statistics for a metric"""
    avg: float
    min: float
    max: float


class MetricAggregations(BaseModel):
    """All metric aggregations"""
    cpu: MetricAggregation
    memory: MetricAggregation
    requests: MetricAggregation
    errors: MetricAggregation


class MetricMetadata(BaseModel):
    """Metadata for metrics response"""
    timeRange: str
    totalApplications: int
    totalEnvironments: int
    dataPoints: int
    filteredByApplication: Optional[str] = None
    filteredByEnvironment: Optional[str] = None


class MetricData(BaseModel):
    """Metrics data response model"""
    metrics: List[Dict[str, Any]]
    total: int
    aggregations: MetricAggregations
    metadata: MetricMetadata


class MetricResponse(BaseModel):
    """Complete metrics response model"""
    status: str
    data: MetricData


def calculate_aggregations(metrics: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate aggregations (avg, min, max) for numeric metrics.
    
    Args:
        metrics: List of metric data points
        
    Returns:
        Dictionary containing aggregations for each metric type
    """
    if not metrics:
        return {
            'cpu': {'avg': 0.0, 'min': 0.0, 'max': 0.0},
            'memory': {'avg': 0.0, 'min': 0.0, 'max': 0.0},
            'requests': {'avg': 0.0, 'min': 0.0, 'max': 0.0},
            'errors': {'avg': 0.0, 'min': 0.0, 'max': 0.0}
        }
    
    # Extract numeric values for each metric type
    cpu_values = [m['cpu'] for m in metrics if 'cpu' in m]
    memory_values = [m['memory'] for m in metrics if 'memory' in m]
    requests_values = [m['requests'] for m in metrics if 'requests' in m]
    errors_values = [m['errors'] for m in metrics if 'errors' in m]
    
    def calc_stats(values: List[float]) -> Dict[str, float]:
        if not values:
            return {'avg': 0.0, 'min': 0.0, 'max': 0.0}
        return {
            'avg': round(sum(values) / len(values), 2),
            'min': min(values),
            'max': max(values)
        }
    
    return {
        'cpu': calc_stats(cpu_values),
        'memory': calc_stats(memory_values),
        'requests': calc_stats(requests_values),
        'errors': calc_stats(errors_values)
    }


def filter_metrics(
    metrics: List[Dict[str, Any]], 
    application: Optional[str] = None,
    environment: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter metrics based on query parameters.
    
    Args:
        metrics: List of all metrics
        application: Filter by application ID
        environment: Filter by environment
        
    Returns:
        Filtered list of metrics
    """
    filtered = metrics
    
    if application:
        filtered = [m for m in filtered if m.get('applicationId') == application]
    
    if environment:
        filtered = [m for m in filtered if m.get('environment') == environment]
    
    return filtered


async def get_metrics_data(
    application: Optional[str] = None,
    environment: Optional[str] = None,
    time_range: str = "24h"
) -> Dict[str, Any]:
    """
    Get performance metrics and monitoring data.
    
    This function provides the core business logic for retrieving metrics data
    with support for filtering by application and environment, plus time range
    selection and aggregations.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        time_range: Time range for metrics (1h, 24h, 7d, 30d)
        
    Returns:
        dict: Response containing metrics data with aggregations and metadata
        
    Raises:
        HTTPException: If data files cannot be loaded
    """
    logger.info(f"Getting metrics data with filters: application={application}, environment={environment}, time_range={time_range}")
    
    try:
        # Load data from JSON files
        metrics_data = load_json("metrics.json")
    except Exception as e:
        logger.error(f"Failed to load metrics data: {e}")
        raise HTTPException(status_code=500, detail=f"Data loading error: {str(e)}")
    
    # Get metrics list
    all_metrics = metrics_data.get('metrics', [])
    
    # Apply filters
    filtered_metrics = filter_metrics(
        all_metrics,
        application=application,
        environment=environment
    )
    
    # Sort by timestamp (most recent first)
    filtered_metrics.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Calculate aggregations
    aggregations = calculate_aggregations(filtered_metrics)
    
    # Build metadata
    metadata = {
        'timeRange': time_range,
        'totalApplications': len(set(m['applicationId'] for m in filtered_metrics)),
        'totalEnvironments': len(set(m['environment'] for m in filtered_metrics)),
        'dataPoints': len(filtered_metrics)
    }
    
    # Add filter information to metadata
    if application:
        metadata['filteredByApplication'] = application
    if environment:
        metadata['filteredByEnvironment'] = environment
    
    # Build response
    response_data = {
        'status': 'success',
        'data': {
            'metrics': filtered_metrics,
            'total': len(filtered_metrics),
            'aggregations': aggregations,
            'metadata': metadata
        }
    }
    
    logger.info(f"Returning {len(filtered_metrics)} metrics with aggregations")
    return response_data


@router.get("/metrics", response_model=MetricResponse)
async def get_metrics(
    application: Optional[str] = Query(None, description="Filter by application ID"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    time_range: str = Query("24h", description="Time range for metrics (1h, 24h, 7d, 30d)")
):
    """
    Get performance metrics and monitoring data.
    
    Retrieves performance metrics with support for:
    - Filtering by application ID and environment
    - Time range selection
    - Automatic aggregations (avg, min, max) for all metric types
    - Summary statistics and metadata
    
    Returns metrics data sorted by most recent first with calculated aggregations.
    """
    try:
        result = await get_metrics_data(application, environment, time_range)
        return result
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
