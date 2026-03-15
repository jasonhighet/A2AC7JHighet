"""
Logs FastAPI endpoint implementation.

This module provides the /api/v1/logs endpoint for the DevOps Dashboard API.
It handles recent logs and events from deployments with filtering and summary capabilities.
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


class LogSummary(BaseModel):
    """Log summary statistics"""
    totalLogs: int
    errorLogs: int
    warnLogs: int
    infoLogs: int
    debugLogs: int
    logLevels: List[str]


class LogMetadata(BaseModel):
    """Metadata for logs response"""
    totalApplications: int
    totalEnvironments: int
    timeRange: str
    sources: List[str]
    filteredByApplication: Optional[str] = None
    filteredByEnvironment: Optional[str] = None
    filteredByLevel: Optional[str] = None


class LogData(BaseModel):
    """Logs data response model"""
    logs: List[Dict[str, Any]]
    total: int
    summary: LogSummary
    metadata: LogMetadata
    limit: Optional[int] = None
    showing: Optional[int] = None


class LogResponse(BaseModel):
    """Complete logs response model"""
    status: str
    data: LogData


def calculate_log_summary(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate log summary statistics.
    
    Args:
        logs: List of log entries
        
    Returns:
        Dictionary containing log summary statistics
    """
    if not logs:
        return {
            'totalLogs': 0,
            'errorLogs': 0,
            'warnLogs': 0,
            'infoLogs': 0,
            'debugLogs': 0,
            'logLevels': []
        }
    
    total = len(logs)
    error_logs = len([log for log in logs if log.get('level') == 'error'])
    warn_logs = len([log for log in logs if log.get('level') == 'warn'])
    info_logs = len([log for log in logs if log.get('level') == 'info'])
    debug_logs = len([log for log in logs if log.get('level') == 'debug'])
    
    # Get unique log levels
    log_levels = list(set(log.get('level', 'unknown') for log in logs))
    log_levels.sort()
    
    return {
        'totalLogs': total,
        'errorLogs': error_logs,
        'warnLogs': warn_logs,
        'infoLogs': info_logs,
        'debugLogs': debug_logs,
        'logLevels': log_levels
    }


def filter_logs(
    logs: List[Dict[str, Any]], 
    application: Optional[str] = None,
    environment: Optional[str] = None,
    level: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Filter logs based on query parameters.
    
    Args:
        logs: List of all log entries
        application: Filter by application ID
        environment: Filter by environment
        level: Filter by log level (error, warn, info, debug)
        limit: Maximum number of logs to return
        
    Returns:
        Filtered list of log entries
    """
    filtered = logs
    
    if application:
        filtered = [log for log in filtered if log.get('applicationId') == application]
    
    if environment:
        filtered = [log for log in filtered if log.get('environment') == environment]
    
    if level:
        filtered = [log for log in filtered if log.get('level') == level]
    
    # Apply limit after filtering
    if limit and limit > 0:
        filtered = filtered[:limit]
    
    return filtered


async def get_logs_data(
    application: Optional[str] = None,
    environment: Optional[str] = None,
    level: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get recent logs and events from deployments.
    
    This function provides the core business logic for retrieving log entries
    with support for filtering by application, environment, and log level.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        level: Optional log level filter (error, warn, info, debug)
        limit: Optional maximum number of log entries to return
        
    Returns:
        dict: Response containing log entries, summary, and metadata
        
    Raises:
        HTTPException: If data files cannot be loaded
    """
    logger.info(f"Getting logs data with filters: application={application}, environment={environment}, level={level}, limit={limit}")
    
    try:
        # Load config and logs data
        logs_data = load_json("logs.json")
    except Exception as e:
        logger.error(f"Failed to load logs data: {e}")
        raise HTTPException(status_code=500, detail=f"Data loading error: {str(e)}")
    
    # Get logs from the data file
    all_logs = logs_data.get('logs', [])
    
    # Sort by timestamp (most recent first)
    all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Apply filters (without limit first to get accurate total)
    filtered_logs_no_limit = filter_logs(
        all_logs,
        application=application,
        environment=environment,
        level=level,
        limit=None  # Don't apply limit yet
    )
    
    # Store total count after filtering but before limit
    total_logs = len(filtered_logs_no_limit)
    
    # Apply limit to get final results
    filtered_logs = filtered_logs_no_limit[:limit] if limit and limit > 0 else filtered_logs_no_limit
    
    # Calculate summary
    summary = calculate_log_summary(filtered_logs)
    
    # Build metadata
    metadata = {
        'totalApplications': len(set(log['applicationId'] for log in filtered_logs)),
        'totalEnvironments': len(set(log['environment'] for log in filtered_logs)),
        'timeRange': 'recent',  # Could be made configurable
        'sources': list(set(log.get('source', 'unknown') for log in filtered_logs))
    }
    
    # Add filter information to metadata
    if application:
        metadata['filteredByApplication'] = application
    if environment:
        metadata['filteredByEnvironment'] = environment
    if level:
        metadata['filteredByLevel'] = level
    
    # Build response data
    response_data = {
        'status': 'success',
        'data': {
            'logs': filtered_logs,
            'total': total_logs,
            'summary': summary,
            'metadata': metadata
        }
    }
    
    # Add pagination info if limit was applied
    if limit:
        response_data['data']['limit'] = limit
        response_data['data']['showing'] = len(filtered_logs)
    
    logger.info(f"Returning {len(filtered_logs)} logs (total: {total_logs}) with summary")
    return response_data


@router.get("/logs", response_model=LogResponse)
async def get_logs(
    application: Optional[str] = Query(None, description="Filter by application ID"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    level: Optional[str] = Query(None, description="Filter by log level (error, warn, info, debug)"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of log entries to return")
):
    """
    Get recent logs and events from deployments.
    
    Retrieves log entries with support for:
    - Filtering by application ID, environment, and log level
    - Limiting the number of results returned
    - Log summary with counts by level
    - Source information and metadata
    
    Returns log entries sorted by most recent first with calculated summary statistics.
    """
    try:
        result = await get_logs_data(application, environment, level, limit)
        return result
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
