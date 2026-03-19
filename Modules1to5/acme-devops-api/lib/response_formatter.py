"""
Response formatting utilities for DevOps Dashboard API.

This module provides standardized response formatting for API endpoints,
ensuring consistent response structure across all endpoints.
"""

from typing import Any, Dict, Optional
from datetime import datetime, timezone


def format_success_response(
    data: Any,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a successful API response.
    
    Args:
        data: The main response data
        message: Optional success message
        metadata: Optional metadata to include
        
    Returns:
        Dict: Standardized success response
    """
    response = {
        "status": "success",
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if message:
        response["message"] = message
    
    if metadata:
        response["metadata"] = metadata
    
    return response


def format_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format an error API response.
    
    Args:
        message: Error message
        error_code: Optional error code
        details: Optional error details
        
    Returns:
        Dict: Standardized error response
    """
    response = {
        "status": "error",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response


def format_paginated_response(
    items: list,
    total: int,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format a paginated API response.
    
    Args:
        items: List of items for current page
        total: Total number of items available
        limit: Items per page limit
        offset: Pagination offset
        metadata: Optional additional metadata
        
    Returns:
        Dict: Standardized paginated response
    """
    pagination_info = {
        "total": total,
        "returned": len(items),
        "limit": limit,
        "offset": offset or 0,
        "has_more": (offset or 0) + len(items) < total
    }
    
    response_data = {
        "items": items,
        "pagination": pagination_info
    }
    
    if metadata:
        response_data["metadata"] = metadata
    
    return format_success_response(response_data)
