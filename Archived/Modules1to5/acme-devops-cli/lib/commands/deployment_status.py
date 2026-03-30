#!/usr/bin/env python3
"""
Deployment Status CLI Command

This module provides CLI functionality to retrieve and filter deployment status
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


def get_deployment_status(application: str | None = None, environment: str | None = None) -> dict[str, Any]:
    """
    Get current deployment status for applications across environments.
    
    This function returns deployment information including status, version, and metadata
    for applications in various environments. Can be filtered by application and/or environment.
    
    Args:
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        environment: Optional environment to filter by (e.g., "prod", "staging", "uat")
        
    Returns:
        dict: Response containing deployment status information
    """
    logger.info(f"get_deployment_status called with application={application}, environment={environment}")
    
    # Load deployment data using our centralized data loader
    try:
        deployments_data = load_json("deployments.json")
        all_deployments = deployments_data.get("deployments", [])
        
        # If no deployments in the data file, return error
        if not all_deployments:
            logger.warning("No deployment data available")
            return {
                "status": "error",
                "error": "No deployment data available",
                "deployments": [],
                "total_count": 0,
                "filters_applied": {
                    "application": application,
                    "environment": environment
                },
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Apply filters if provided
        filtered_deployments = all_deployments
        
        if application:
            filtered_deployments = [d for d in filtered_deployments if d["applicationId"] == application]
        
        if environment:
            filtered_deployments = [d for d in filtered_deployments if d["environment"] == environment]
        
        return {
            "status": "success",
            "deployments": filtered_deployments,
            "total_count": len(filtered_deployments),
            "filters_applied": {
                "application": application,
                "environment": environment
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except DataLoadError as e:
        logger.error(f"Error loading deployment data: {e}")
        return {
            "status": "error",
            "error": f"Failed to load deployment data: {str(e)}",
            "deployments": [],
            "total_count": 0,
            "filters_applied": {
                "application": application,
                "environment": environment
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Unexpected error processing deployment data: {e}")
        return {
            "status": "error",
            "error": f"Failed to process deployment data: {str(e)}",
            "deployments": [],
            "total_count": 0,
            "filters_applied": {
                "application": application,
                "environment": environment
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }


def print_table(result: dict[str, Any]) -> None:
    """Print deployment status in table format."""
    if result["status"] == "error":
        print(f"Error: {result['error']}", file=sys.stderr)
        return
    
    deployments = result["deployments"]
    if not deployments:
        print("No deployments found matching the criteria.")
        return
    
    # Print header
    print(f"{'Application':<15} {'Environment':<12} {'Version':<10} {'Status':<12} {'Deployed At':<20}")
    print("-" * 75)
    
    # Print deployments
    for deployment in deployments:
        app_id = deployment.get("applicationId", "N/A")[:14]
        env = deployment.get("environment", "N/A")[:11]
        version = deployment.get("version", "N/A")[:9]
        status = deployment.get("status", "N/A")[:11]
        deployed_at = deployment.get("deployedAt", "N/A")[:19]
        
        print(f"{app_id:<15} {env:<12} {version:<10} {status:<12} {deployed_at:<20}")
    
    print(f"\nTotal: {result['total_count']} deployments")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for this command."""
    parser = argparse.ArgumentParser(
        description='Get deployment status for applications across environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devops-cli status                           # Get all deployment statuses
  devops-cli status --app web-app             # Filter by application
  devops-cli status --env prod                # Filter by environment
  devops-cli status --app web-app --env prod  # Filter by both
  devops-cli status --format table           # Display as table
        """
    )
    
    parser.add_argument(
        '--app', '--application',
        help='Filter by application ID (e.g., "web-app", "api-service")'
    )
    parser.add_argument(
        '--env', '--environment',
        help='Filter by environment (e.g., "prod", "staging", "uat")'
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
    result = get_deployment_status(parsed_args.app, parsed_args.env)
    
    # Format and output result
    if parsed_args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_table(result)
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
