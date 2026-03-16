#!/usr/bin/env python3
"""
DevOps Dashboard MCP - Stdio Server

A minimal FastMCP stdio server implementation that provides basic DevOps dashboard
functionality. This serves as the foundation for the complete implementation.

This server demonstrates:
- Basic FastMCP stdio server setup
- Tool registration and discovery
- CLI wrapper pattern for enterprise-friendly architecture

This version wraps the standalone acme-devops-cli tool rather than implementing
functionality directly, demonstrating how to wrap existing CLI tools with MCP.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, List

from mcp.server.fastmcp import FastMCP

# Add the current directory to Python path to handle imports correctly
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("DevOps Dashboard")


class CLIError(Exception):
    """Exception raised when CLI command execution fails"""
    pass


def run_cli_command(args: List[str], timeout: int = 30) -> dict[str, Any]:
    """
    Execute the CLI tool with proper error handling.
    
    Args:
        args: List of command arguments to pass to the CLI
        timeout: Maximum time to wait for command completion (seconds)
        
    Returns:
        dict: Parsed JSON response from the CLI tool
        
    Raises:
        CLIError: If the CLI command fails or returns invalid JSON
    """
    # Map CLI commands to their Python modules
    command_map = {
        "status": "lib.commands.deployment_status",
        "releases": "lib.commands.recent_releases",
        "health": "lib.commands.environment_health",
        "promote": "lib.commands.promote_release"
    }
    
    if not args or args[0] not in command_map:
        raise CLIError(f"Unknown or missing CLI command: {args[0] if args else 'None'}")
    
    command = args[0]
    module = command_map[command]
    remaining_args = args[1:]
    
    # Path to the CLI tool root
    cli_root = Path(__file__).parent.parent.parent / "acme-devops-cli"
    
    if not cli_root.exists():
        raise CLIError(f"CLI root directory not found at: {cli_root}")
    
    # Build the full command using sys.executable to ensure cross-platform Python invocation
    cmd = [sys.executable, "-m", module] + remaining_args
    
    logger.info(f"Executing CLI command: {' '.join(cmd)}")
    
    try:
        # Execute the command with timeout
        # Using environment variables to ensure ACME_DATA_DIR is set locally if needed
        # In this modular setup, the commands load data relative to their context
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(cli_root)  # Set working directory to CLI root
        )
        
        # Check if command succeeded
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"CLI command failed with exit code {result.returncode}: {error_msg}")
            raise CLIError(f"CLI command failed: {error_msg}")
        
        # Parse JSON response
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse CLI JSON output: {e}")
            logger.error(f"CLI stdout: {result.stdout}")
            # Sometimes there might be warning text before JSON
            if "{" in result.stdout:
                try:
                    json_start = result.stdout.find("{")
                    return json.loads(result.stdout[json_start:])
                except:
                    pass
            raise CLIError(f"Invalid JSON response from CLI: {e}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"CLI command timed out after {timeout} seconds")
        raise CLIError(f"CLI command timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"Unexpected error executing CLI command: {e}")
        raise CLIError(f"Unexpected error: {e}")


@mcp.tool()
def ping(message: str = "Hello from DevOps Dashboard MCP!") -> dict[str, Any]:
    """
    A simple ping tool to verify MCP server connectivity and tool discovery.
    
    This tool echoes back a message to confirm the MCP server is working correctly
    and can be discovered by MCP clients like Claude Desktop or MCP Inspector.
    
    Args:
        message: Optional message to echo back (default: "Hello from DevOps Dashboard MCP!")
        
    Returns:
        dict: Response containing the echoed message, server status, and metadata
    """
    logger.info(f"Ping tool called with message: {message}")
    
    return {
        "status": "success",
        "message": message,
        "server": "DevOps Dashboard MCP - Stdio Server (CLI Wrapper)",
        "version": "0.2.0",
        "timestamp": "2024-01-15T10:30:00Z",
        "tools_available": 5,
        "architecture": "CLI Wrapper Pattern"
    }


@mcp.tool()
def get_deployment_status(application: str | None = None, environment: str | None = None) -> dict[str, Any]:
    """
    Get current deployment status for applications across environments.
    
    This tool returns deployment information including status, version, and metadata
    for applications in various environments. Can be filtered by application and/or environment.
    
    Args:
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        environment: Optional environment to filter by (e.g., "prod", "staging", "uat")
        
    Returns:
        dict: Response containing deployment status information
    """
    logger.info(f"Getting deployment status - app: {application}, env: {environment}")
    
    # Build CLI arguments
    args = ["status", "--format", "json"]
    if application:
        args.extend(["--app", application])
    if environment:
        args.extend(["--env", environment])
    
    try:
        return run_cli_command(args)
    except CLIError as e:
        logger.error(f"Failed to get deployment status: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve deployment status: {e}",
            "deployments": []
        }


@mcp.tool()
def list_recent_releases(limit: int = 10, application: str | None = None) -> dict[str, Any]:
    """
    Show recent version deployments across all applications.
    
    This tool returns recent release information sorted by release date,
    with optional filtering by application and configurable result limit.
    
    Args:
        limit: Number of recent releases to return (default: 10)
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        
    Returns:
        dict: Response containing recent releases information
    """
    logger.info(f"Listing recent releases - limit: {limit}, app: {application}")
    
    # Build CLI arguments
    args = ["releases", "--format", "json", "--limit", str(limit)]
    if application:
        args.extend(["--app", application])
    
    try:
        return run_cli_command(args)
    except CLIError as e:
        logger.error(f"Failed to list recent releases: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve recent releases: {e}",
            "releases": []
        }


@mcp.tool()
def check_environment_health(environment: str | None = None, application: str | None = None) -> dict[str, Any]:
    """
    Get health status across all services and environments.
    
    This tool returns environment health information including status, uptime,
    response times, and issues. Can be filtered by environment and/or application.
    
    Args:
        environment: Optional environment to filter by (e.g., "prod", "staging", "uat")
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        
    Returns:
        dict: Response containing environment health information
    """
    logger.info(f"Checking environment health - env: {environment}, app: {application}")
    
    # Build CLI arguments
    args = ["health", "--format", "json"]
    if environment:
        args.extend(["--env", environment])
    if application:
        args.extend(["--app", application])
    
    try:
        return run_cli_command(args)
    except CLIError as e:
        logger.error(f"Failed to check environment health: {e}")
        return {
            "status": "error",
            "message": f"Failed to retrieve environment health: {e}",
            "environments": []
        }


@mcp.tool()
def promote_release(
    applicationId: str,
    version: str,
    fromEnvironment: str,
    toEnvironment: str
) -> dict[str, Any]:
    """
    Simulate promoting a release from one environment to another.
    
    This tool simulates the promotion of a release version from a source environment
    to a target environment, performing validation checks and creating a deployment record.
    
    Args:
        applicationId: Application to promote (required)
        version: Version to promote (required)
        fromEnvironment: Source environment (required)
        toEnvironment: Target environment (required)
        
    Returns:
        dict: Response containing promotion status and deployment details
    """
    logger.info(f"Promoting release - app: {applicationId}, version: {version}, from: {fromEnvironment}, to: {toEnvironment}")
    
    # Build CLI arguments - promote uses positional arguments
    args = [
        "promote",
        applicationId,
        version,
        fromEnvironment,
        toEnvironment,
        "--format", "json"
    ]
    
    try:
        return run_cli_command(args)
    except CLIError as e:
        logger.error(f"Failed to promote release: {e}")
        return {
            "status": "error",
            "message": f"Failed to promote release: {e}",
            "promotion": None
        }


def main() -> None:
    """
    Main entry point for the DevOps Dashboard MCP stdio server.
    
    This function starts the FastMCP server in stdio mode, which allows it to
    communicate with MCP clients through standard input/output streams.
    """
    logger.info("Starting DevOps Dashboard MCP stdio server (CLI Wrapper)...")
    
    try:
        # Run the FastMCP server
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
