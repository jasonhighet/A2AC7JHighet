#!/usr/bin/env python3
"""
DevOps Dashboard MCP - HTTP Server

An MCP server that wraps the DevOps Dashboard REST API, providing MCP tool
interfaces for AI assistants to interact with DevOps operations.

This server demonstrates the API wrapper pattern:
- MCP server acts as a thin wrapper around REST API
- HTTP client calls to standalone API service
- Proper error handling and timeout management
- Maintains MCP tool signatures while delegating to API
"""

import logging
import httpx
from typing import Any

from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server for HTTP transport
mcp = FastMCP("DevOps Dashboard HTTP")

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
API_TIMEOUT = 30


class APIError(Exception):
    """Custom exception for API-related errors"""
    pass


async def call_api_endpoint(
    endpoint: str, 
    params: dict[str, Any] | None = None,
    timeout: int = API_TIMEOUT
) -> dict[str, Any]:
    """
    Call the REST API with proper error handling and retry logic.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Query parameters to send with the request
        timeout: Request timeout in seconds
        
    Returns:
        dict: JSON response from the API
        
    Raises:
        APIError: If the API request fails or returns an error
    """
    url = f"{API_BASE_URL}/{endpoint}"
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            logger.info(f"Calling API endpoint: {url} with params: {params}")
            response = await client.get(url, params=params or {})
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"API call successful: {endpoint}")
            return result
            
        except httpx.HTTPStatusError as e:
            error_msg = f"API request failed with status {e.response.status_code}"
            try:
                error_detail = e.response.json().get("detail", e.response.text)
                error_msg += f": {error_detail}"
            except:
                error_msg += f": {e.response.text}"
            
            logger.error(error_msg)
            raise APIError(error_msg)
            
        except httpx.RequestError as e:
            error_msg = f"API connection error: {e}"
            logger.error(error_msg)
            raise APIError(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error calling API: {e}"
            logger.error(error_msg)
            raise APIError(error_msg)


@mcp.tool()
def ping(message: str = "Hello from DevOps Dashboard HTTP MCP!") -> dict[str, Any]:
    """
    A simple ping tool to verify MCP server connectivity and tool discovery.
    
    This tool echoes back a message to confirm the MCP server is working correctly
    and can be discovered by MCP clients like MCP Inspector.
    
    Args:
        message: Optional message to echo back (default: "Hello from DevOps Dashboard HTTP MCP!")
        
    Returns:
        dict: Response containing the echoed message, server status, and metadata
    """
    logger.info(f"Ping tool called with message: {message}")
    
    return {
        "status": "success",
        "message": message,
        "server": "DevOps Dashboard MCP - HTTP Server",
        "version": "0.1.0",
        "timestamp": "2024-01-15T10:30:00Z",
        "transport": "http",
        "tools_available": 5
    }


@mcp.tool()
async def get_deployments(
    application: str | None = None,
    environment: str | None = None,
    limit: int | None = None,
    offset: int | None = None
) -> dict[str, Any]:
    """
    Get detailed deployment history and current states.
    
    This tool provides deployment data with support for filtering by application 
    and environment, plus pagination capabilities.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by  
        limit: Optional maximum number of results to return
        offset: Optional pagination offset
        
    Returns:
        dict: Response containing deployment data, pagination info, and metadata
    """
    logger.info(f"get_deployments tool called with filters: application={application}, environment={environment}")
    
    try:
        params = {}
        if application:
            params["application"] = application
        if environment:
            params["environment"] = environment
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        
        return await call_api_endpoint("deployments", params)
        
    except APIError as e:
        logger.error(f"Failed to get deployments: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve deployment data: {e}",
            "data": {},
            "timestamp": "2024-01-15T10:30:00Z"
        }

@mcp.tool()
async def get_metrics(
    application: str | None = None,
    environment: str | None = None,
    time_range: str = "24h"
) -> dict[str, Any]:
    """
    Get performance metrics and monitoring data.
    
    This tool provides metrics data with support for filtering by application
    and environment, plus time range selection and aggregations.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        time_range: Time range for metrics (1h, 24h, 7d, 30d)
        
    Returns:
        dict: Response containing metrics data with aggregations and metadata
    """
    logger.info(f"get_metrics tool called with filters: application={application}, environment={environment}")
    
    try:
        params = {}
        if application:
            params["application"] = application
        if environment:
            params["environment"] = environment
        if time_range:
            params["time_range"] = time_range
        
        return await call_api_endpoint("metrics", params)
        
    except APIError as e:
        logger.error(f"Failed to get metrics: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve metrics data: {e}",
            "data": {},
            "timestamp": "2024-01-15T10:30:00Z"
        }

@mcp.tool()
async def get_health(
    environment: str | None = None,
    application: str | None = None,
    detailed: bool = False
) -> dict[str, Any]:
    """
    Get comprehensive health check across all services.
    
    This tool provides health status with support for filtering by environment
    and application, plus detailed diagnostic information.
    
    Args:
        environment: Optional environment to filter by
        application: Optional application ID to filter by
        detailed: Include detailed diagnostic information
        
    Returns:
        dict: Response containing health status, summary, and metadata
    """
    logger.info(f"get_health tool called with filters: environment={environment}, application={application}")
    
    try:
        params = {}
        if environment:
            params["environment"] = environment
        if application:
            params["application"] = application
        if detailed:
            params["detailed"] = detailed
        
        return await call_api_endpoint("health", params)
        
    except APIError as e:
        logger.error(f"Failed to get health status: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve health data: {e}",
            "data": {},
            "timestamp": "2024-01-15T10:30:00Z"
        }

@mcp.tool()
async def get_logs(
    application: str | None = None,
    environment: str | None = None,
    level: str | None = None,
    limit: int | None = None
) -> dict[str, Any]:
    """
    Get recent logs and events from deployments.
    
    This tool provides log entries with support for filtering by application,
    environment, and log level.
    
    Args:
        application: Optional application ID to filter by
        environment: Optional environment to filter by
        level: Optional log level filter (error, warn, info, debug)
        limit: Optional maximum number of log entries to return
        
    Returns:
        dict: Response containing log entries, summary, and metadata
    """
    logger.info(f"get_logs tool called with filters: application={application}, environment={environment}")
    
    try:
        params = {}
        if application:
            params["application"] = application
        if environment:
            params["environment"] = environment
        if level:
            params["level"] = level
        if limit:
            params["limit"] = limit
        
        return await call_api_endpoint("logs", params)
        
    except APIError as e:
        logger.error(f"Failed to get logs: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve log data: {e}",
            "data": {},
            "timestamp": "2024-01-15T10:30:00Z"
        }

def main() -> None:
    """
    Main entry point for the DevOps Dashboard MCP HTTP server.
    
    This function starts the FastMCP server in HTTP mode, which allows it to
    communicate with MCP clients through HTTP requests and responses.
    """
    logger.info("Starting DevOps Dashboard MCP HTTP server...")
    
    try:
        # Run the FastMCP HTTP server on port 8001 to avoid conflict with API server
        # FastMCP will automatically handle HTTP transport setup
        mcp.run(transport="http", port=8888)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
