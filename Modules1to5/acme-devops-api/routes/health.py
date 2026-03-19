"""
Health FastAPI endpoint implementation.

This module provides the /api/v1/health endpoint for the DevOps Dashboard API.
It handles comprehensive health check across all services with filtering and summary capabilities.
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


class HealthSummary(BaseModel):
    """Health summary statistics"""
    totalServices: int
    healthyServices: int
    degradedServices: int
    unhealthyServices: int
    overallStatus: str


class HealthMetadata(BaseModel):
    """Metadata for health response"""
    detailed: bool
    totalEnvironments: int
    totalApplications: int
    lastChecked: str
    filteredByEnvironment: Optional[str] = None
    filteredByApplication: Optional[str] = None


class HealthData(BaseModel):
    """Health data response model"""
    healthStatus: List[Dict[str, Any]]
    total: int
    summary: HealthSummary
    metadata: HealthMetadata


class HealthResponse(BaseModel):
    """Complete health response model"""
    status: str
    data: HealthData


def calculate_health_summary(health_status: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate health summary statistics.
    
    Args:
        health_status: List of health status records
        
    Returns:
        Dictionary containing health summary statistics
    """
    if not health_status:
        return {
            'totalServices': 0,
            'healthyServices': 0,
            'degradedServices': 0,
            'unhealthyServices': 0,
            'overallStatus': 'unknown'
        }
    
    total = len(health_status)
    healthy = len([h for h in health_status if h.get('status') == 'healthy'])
    degraded = len([h for h in health_status if h.get('status') == 'degraded'])
    unhealthy = len([h for h in health_status if h.get('status') == 'unhealthy'])
    
    # Determine overall status
    if unhealthy > 0:
        overall_status = 'unhealthy'
    elif degraded > 0:
        overall_status = 'degraded'
    elif healthy > 0:
        overall_status = 'healthy'
    else:
        overall_status = 'unknown'
    
    return {
        'totalServices': total,
        'healthyServices': healthy,
        'degradedServices': degraded,
        'unhealthyServices': unhealthy,
        'overallStatus': overall_status
    }


def filter_health_status(
    health_status: List[Dict[str, Any]], 
    environment: Optional[str] = None,
    application: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter health status based on query parameters.
    
    Args:
        health_status: List of all health status records
        environment: Filter by environment
        application: Filter by application ID
        
    Returns:
        Filtered list of health status records
    """
    filtered = health_status
    
    if environment:
        filtered = [h for h in filtered if h.get('environment') == environment]
    
    if application:
        filtered = [h for h in filtered if h.get('applicationId') == application]
    
    return filtered


def format_health_response(
    health_status: List[Dict[str, Any]], 
    detailed: bool = False
) -> List[Dict[str, Any]]:
    """
    Format health status response based on detail level.
    
    Args:
        health_status: List of health status records
        detailed: Whether to include detailed diagnostic information
        
    Returns:
        Formatted health status records
    """
    if detailed:
        # Return full health status with all details
        return health_status
    else:
        # Return basic health status (still include all fields for now)
        # In a real implementation, we might exclude some detailed fields
        return health_status


async def get_health_data(
    environment: Optional[str] = None,
    application: Optional[str] = None,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Get comprehensive health check across all services.
    
    This function provides the core business logic for retrieving health status
    with support for filtering by environment and application, plus detailed
    diagnostic information.
    
    Args:
        environment: Optional environment to filter by
        application: Optional application ID to filter by
        detailed: Include detailed diagnostic information
        
    Returns:
        dict: Response containing health status, summary, and metadata
        
    Raises:
        HTTPException: If data files cannot be loaded
    """
    logger.info(f"Getting health data with filters: environment={environment}, application={application}, detailed={detailed}")
    
    try:
        # Load data from JSON files
        health_data = load_json("environments.json")
    except Exception as e:
        logger.error(f"Failed to load health data: {e}")
        raise HTTPException(status_code=500, detail=f"Data loading error: {str(e)}")
    
    # Get health status list
    all_health_status = health_data.get('environmentHealth', [])
    
    # Apply filters
    filtered_health_status = filter_health_status(
        all_health_status,
        environment=environment,
        application=application
    )
    
    # Sort by environment, then by application for consistent ordering
    filtered_health_status.sort(key=lambda x: (x.get('environment', ''), x.get('applicationId', '')))
    
    # Format response based on detail level
    formatted_health_status = format_health_response(filtered_health_status, detailed)
    
    # Calculate health summary
    summary = calculate_health_summary(filtered_health_status)
    
    # Build metadata
    metadata = {
        'detailed': detailed,
        'totalEnvironments': len(set(h['environment'] for h in filtered_health_status)),
        'totalApplications': len(set(h['applicationId'] for h in filtered_health_status)),
        'lastChecked': max([h.get('lastChecked', '') for h in filtered_health_status], default='')
    }
    
    # Add filter information to metadata
    if environment:
        metadata['filteredByEnvironment'] = environment
    if application:
        metadata['filteredByApplication'] = application
    
    # Build response
    response_data = {
        'status': 'success',
        'data': {
            'healthStatus': formatted_health_status,
            'total': len(filtered_health_status),
            'summary': summary,
            'metadata': metadata
        }
    }
    
    logger.info(f"Returning {len(formatted_health_status)} health status records with summary: {summary['overallStatus']}")
    return response_data


@router.get("/health", response_model=HealthResponse)
async def get_health(
    environment: Optional[str] = Query(None, description="Filter by environment"),
    application: Optional[str] = Query(None, description="Filter by application ID"),
    detailed: bool = Query(False, description="Include detailed diagnostic information")
):
    """
    Get comprehensive health check across all services.
    
    Retrieves health status with support for:
    - Filtering by environment and application ID
    - Detailed diagnostic information toggle
    - Health summary with overall status calculation
    - Service counts by health status (healthy, degraded, unhealthy)
    
    Returns health status sorted by environment and application with calculated summary.
    """
    try:
        result = await get_health_data(environment, application, detailed)
        return result
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_health: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
