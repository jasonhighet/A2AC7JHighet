"""
Error handling utilities for DevOps Dashboard API.

This module provides standardized error handling and HTTP exception
utilities for consistent error responses across all endpoints.
"""

import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from .response_formatter import format_error_response

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception class for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


class ValidationError(APIError):
    """Exception for validation errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundError(APIError):
    """Exception for resource not found errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            details=details
        )


class DataLoadError(APIError):
    """Exception for data loading errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATA_LOAD_ERROR",
            details=details
        )


def handle_api_error(error: APIError) -> HTTPException:
    """
    Convert an APIError to an HTTPException.
    
    Args:
        error: The APIError to convert
        
    Returns:
        HTTPException: FastAPI HTTPException with formatted response
    """
    logger.error(f"API Error: {error.message}", exc_info=True)
    
    response_content = format_error_response(
        message=error.message,
        error_code=error.error_code,
        details=error.details
    )
    
    return HTTPException(
        status_code=error.status_code,
        detail=response_content
    )


def handle_validation_error(field: str, value: Any, message: str) -> ValidationError:
    """
    Create a validation error with standardized details.
    
    Args:
        field: The field that failed validation
        value: The invalid value
        message: Validation error message
        
    Returns:
        ValidationError: Formatted validation error
    """
    details = {
        "field": field,
        "value": str(value),
        "validation_message": message
    }
    
    return ValidationError(
        message=f"Validation failed for field '{field}': {message}",
        details=details
    )


def handle_not_found_error(resource: str, identifier: str) -> NotFoundError:
    """
    Create a not found error with standardized details.
    
    Args:
        resource: The type of resource that was not found
        identifier: The identifier used to search for the resource
        
    Returns:
        NotFoundError: Formatted not found error
    """
    details = {
        "resource": resource,
        "identifier": identifier
    }
    
    return NotFoundError(
        message=f"{resource} not found with identifier: {identifier}",
        details=details
    )
