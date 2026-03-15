"""
Deployments FastAPI endpoint implementation.

This module provides the /api/v1/deployments endpoint for the DevOps Dashboard API.
It handles deployment data retrieval with filtering, pagination, and data integration.
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


class DeploymentMetadata(BaseModel):
    """Metadata for deployment response"""
    endpoint: str
    version: str
    filters_applied: Dict[str, Optional[str]]
    available_applications: List[str]
    available_environments: List[str]


class DeploymentData(BaseModel):
    """Deployment data response model"""
    deployments: List[Dict[str, Any]]
    total: int
    returned: int
    limit: Optional[int]
    offset: Optional[int]
    has_more: bool
    metadata: DeploymentMetadata


class DeploymentResponse(BaseModel):
    """Complete deployment response model"""
    status: str
    data: DeploymentData
    timestamp: str


def filter_deployments(
    deployments: List[Dict[str, Any]], 
    application: Optional[str] = None,
    environment: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter deployments based on application and environment criteria.
    
    Args:
        deployments: List of deployment objects to filter
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        
    Returns:
        List of filtered deployment objects
    """
    filtered = deployments
    
    if application:
        filtered = [d for d in filtered if d.get('applicationId') == application]
        logger.debug(f"Filtered by application '{application}': {len(filtered)} results")
    
    if environment:
        filtered = [d for d in filtered if d.get('environment') == environment]
        logger.debug(f"Filtered by environment '{environment}': {len(filtered)} results")
    
    return filtered


def paginate_results(
    items: List[Dict[str, Any]], 
    limit: Optional[int] = None, 
    offset: Optional[int] = None
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply pagination to a list of items.
    
    Args:
        items: List of items to paginate
        limit: Maximum number of items to return
        offset: Number of items to skip
        
    Returns:
        Tuple of (paginated_items, pagination_metadata)
    """
    total = len(items)
    
    # Apply offset
    start_idx = offset or 0
    if start_idx >= total:
        return [], {
            'total': total,
            'returned': 0,
            'limit': limit,
            'offset': start_idx,
            'has_more': False
        }
    
    # Apply limit
    if limit is not None:
        end_idx = start_idx + limit
        paginated_items = items[start_idx:end_idx]
        has_more = end_idx < total
    else:
        paginated_items = items[start_idx:]
        has_more = False
    
    pagination_metadata = {
        'total': total,
        'returned': len(paginated_items),
        'limit': limit,
        'offset': start_idx,
        'has_more': has_more
    }
    
    return paginated_items, pagination_metadata


def enrich_deployment_data(
    deployments: List[Dict[str, Any]], 
    config_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Enrich deployment data with additional metadata from config.
    
    Args:
        deployments: List of deployment objects
        config_data: Configuration data containing application and environment info
        
    Returns:
        List of enriched deployment objects
    """
    # Create lookup maps for efficient enrichment
    app_lookup = {app['id']: app for app in config_data.get('applications', [])}
    env_lookup = {env['id']: env for env in config_data.get('environments', [])}
    
    enriched_deployments = []
    for deployment in deployments:
        enriched = deployment.copy()
        
        # Add application metadata
        app_id = deployment.get('applicationId')
        if app_id and app_id in app_lookup:
            enriched['applicationName'] = app_lookup[app_id]['name']
        
        # Add environment metadata
        env_id = deployment.get('environment')
        if env_id and env_id in env_lookup:
            enriched['environmentName'] = env_lookup[env_id]['name']
            enriched['environmentUrl'] = env_lookup[env_id]['url']
        
        enriched_deployments.append(enriched)
    
    return enriched_deployments


async def get_deployments_data(
    application: Optional[str] = None,
    environment: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get deployment data with filtering and pagination.
    
    This function provides the core business logic for retrieving deployment
    history and current states with support for filtering and pagination.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        limit: Optional maximum number of results to return
        offset: Optional pagination offset
        
    Returns:
        dict: Response containing deployment data, pagination info, and metadata
        
    Raises:
        ValueError: If pagination parameters are invalid
        HTTPException: If data files cannot be loaded
    """
    logger.info(f"Getting deployments data with filters: application={application}, environment={environment}, limit={limit}, offset={offset}")
    
    # Validate pagination parameters
    if limit is not None and limit <= 0:
        raise ValueError("Limit must be positive")
    if offset is not None and offset < 0:
        raise ValueError("Offset must be non-negative")
    
    try:
        # Load data files using our local data loader
        deployments_data = load_json("deployments.json")
        config_data = load_json("config.json")
    except Exception as e:
        logger.error(f"Failed to load data files: {e}")
        raise HTTPException(status_code=500, detail=f"Data loading error: {str(e)}")
    
    # Extract deployments list
    deployments = deployments_data.get('deployments', [])
    
    # Apply filters
    filtered_deployments = filter_deployments(deployments, application, environment)
    
    # Sort by deployment date (most recent first)
    filtered_deployments.sort(key=lambda x: x.get('deployedAt', ''), reverse=True)
    
    # Apply pagination
    paginated_deployments, pagination_info = paginate_results(filtered_deployments, limit, offset)
    
    # Enrich with additional metadata
    enriched_deployments = enrich_deployment_data(paginated_deployments, config_data)
    
    # Build response
    response_data = {
        'status': 'success',
        'data': {
            'deployments': enriched_deployments,
            'total': pagination_info['total'],
            'returned': pagination_info['returned'],
            'limit': pagination_info['limit'],
            'offset': pagination_info['offset'],
            'has_more': pagination_info['has_more'],
            'metadata': {
                'endpoint': 'deployments',
                'version': '1.0.0',
                'filters_applied': {
                    'application': application,
                    'environment': environment
                },
                'available_applications': [app['id'] for app in config_data.get('applications', [])],
                'available_environments': [env['id'] for env in config_data.get('environments', [])]
            }
        },
        'timestamp': '2024-01-15T11:00:00Z'
    }
    
    logger.info(f"Returning {len(enriched_deployments)} deployments (total: {pagination_info['total']})")
    return response_data


@router.get("/deployments", response_model=DeploymentResponse)
async def get_deployments(
    application: Optional[str] = Query(None, description="Filter by application ID"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum results to return"),
    offset: Optional[int] = Query(None, ge=0, description="Pagination offset")
):
    """
    Get deployment data with filtering and pagination.
    
    Retrieves deployment history and current states with support for:
    - Filtering by application ID and environment
    - Pagination with limit and offset
    - Enriched data with application and environment metadata
    
    Returns deployment data sorted by most recent first.
    """
    try:
        result = await get_deployments_data(application, environment, limit, offset)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_deployments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
