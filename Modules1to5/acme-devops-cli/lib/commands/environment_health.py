#!/usr/bin/env python3
"""
Environment Health CLI Command

This module provides CLI functionality to retrieve and filter environment health
information from the DevOps dashboard data files.
"""

import argparse
import json
import sys
import logging
from typing import Any
from datetime import datetime

# Import our local data loader
from lib.data_loader import load_json, DataLoadError

# Configure logging
logger = logging.getLogger(__name__)


def check_environment_health(environment: str | None = None, application: str | None = None) -> dict[str, Any]:
    """
    Get health status across all services and environments.
    
    This function returns environment health information including status, uptime,
    response times, and issues. Can be filtered by environment and/or application.
    
    Args:
        environment: Optional environment to filter by (e.g., "prod", "staging", "uat")
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        
    Returns:
        dict: Response containing environment health information
    """
    logger.info(f"check_environment_health called with environment={environment}, application={application}")
    
    # Load environment health data using our centralized data loader
    try:
        health_data = load_json("release_health.json")
        all_health_data = health_data.get("releaseHealth", [])
        
        if not all_health_data:
            logger.warning("No environment health data available")
            return {
                "status": "error",
                "error": "No environment health data available",
                "health_checks": [],
                "total_count": 0,
                "summary": {
                    "healthy": 0,
                    "degraded": 0,
                    "unhealthy": 0
                },
                "filters_applied": {
                    "environment": environment,
                    "application": application
                },
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Apply filters if provided
        filtered_health_data = all_health_data
        
        if environment:
            filtered_health_data = [h for h in filtered_health_data if h["environment"] == environment]
        
        if application:
            filtered_health_data = [h for h in filtered_health_data if h["applicationId"] == application]
        
        # Calculate summary statistics
        summary = {
            "healthy": len([h for h in filtered_health_data if h["status"] == "healthy"]),
            "degraded": len([h for h in filtered_health_data if h["status"] == "degraded"]),
            "unhealthy": len([h for h in filtered_health_data if h["status"] == "unhealthy"])
        }
        
        # Sort by status priority (unhealthy first, then degraded, then healthy)
        status_priority = {"unhealthy": 0, "degraded": 1, "healthy": 2}
        filtered_health_data.sort(key=lambda x: status_priority.get(x["status"], 3))
        
        return {
            "status": "success",
            "health_checks": filtered_health_data,
            "total_count": len(filtered_health_data),
            "summary": summary,
            "overall_status": _determine_overall_status(summary),
            "filters_applied": {
                "environment": environment,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except DataLoadError as e:
        logger.error(f"Error loading environment health data: {e}")
        return {
            "status": "error",
            "error": f"Failed to load environment health data: {str(e)}",
            "health_checks": [],
            "total_count": 0,
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0
            },
            "filters_applied": {
                "environment": environment,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Unexpected error processing environment health data: {e}")
        return {
            "status": "error",
            "error": f"Failed to process environment health data: {str(e)}",
            "health_checks": [],
            "total_count": 0,
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0
            },
            "filters_applied": {
                "environment": environment,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }


def _determine_overall_status(summary: dict[str, int]) -> str:
    """
    Determine overall health status based on individual service statuses.
    
    Args:
        summary: Dictionary with counts of healthy, degraded, and unhealthy services
        
    Returns:
        str: Overall status ("healthy", "degraded", or "unhealthy")
    """
    if summary["unhealthy"] > 0:
        return "unhealthy"
    elif summary["degraded"] > 0:
        return "degraded"
    elif summary["healthy"] > 0:
        return "healthy"
    else:
        return "unknown"


def print_table(result: dict[str, Any]) -> None:
    """Print environment health in table format."""
    if result["status"] == "error":
        print(f"Error: {result['error']}", file=sys.stderr)
        return
    
    health_checks = result["health_checks"]
    if not health_checks:
        print("No health checks found matching the criteria.")
        return
    
    # Print summary
    summary = result["summary"]
    overall_status = result["overall_status"]
    print(f"Overall Status: {overall_status.upper()}")
    print(f"Healthy: {summary['healthy']}, Degraded: {summary['degraded']}, Unhealthy: {summary['unhealthy']}")
    print()
    
    # Print header
    print(f"{'Application':<15} {'Environment':<12} {'Status':<10} {'Uptime':<8} {'Response Time':<15} {'Issues':<20}")
    print("-" * 85)
    
    # Print health checks
    for health in health_checks:
        app_id = health.get("applicationId", "N/A")[:14]
        env = health.get("environment", "N/A")[:11]
        status = health.get("status", "N/A")[:9]
        uptime = f"{health.get('uptime', 0):.1f}%"[:7]
        response_time = f"{health.get('responseTime', 0)}ms"[:14]
        issues = str(health.get('issues', 0))[:19]
        
        print(f"{app_id:<15} {env:<12} {status:<10} {uptime:<8} {response_time:<15} {issues:<20}")
    
    print(f"\nTotal: {result['total_count']} health checks")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for this command."""
    parser = argparse.ArgumentParser(
        description='Get health status across all services and environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devops-cli health                           # Get all health statuses
  devops-cli health --env prod                # Filter by environment
  devops-cli health --app web-app             # Filter by application
  devops-cli health --env prod --app web-app  # Filter by both
  devops-cli health --format table           # Display as table
        """
    )
    
    parser.add_argument(
        '--env', '--environment',
        help='Filter by environment (e.g., "prod", "staging", "uat")'
    )
    parser.add_argument(
        '--app', '--application',
        help='Filter by application ID (e.g., "web-app", "api-service")'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'table'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser


def main(args=None):
    """Main entry point for CLI command."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Configure logging
    if parsed_args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Call business logic
    result = check_environment_health(parsed_args.env, parsed_args.app)
    
    # Format and output result
    if parsed_args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_table(result)
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
