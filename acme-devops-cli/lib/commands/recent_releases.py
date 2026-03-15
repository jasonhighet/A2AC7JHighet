#!/usr/bin/env python3
"""
Recent Releases CLI Command

This module provides CLI functionality to retrieve and filter recent release
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


def list_recent_releases(limit: int = 10, application: str | None = None) -> dict[str, Any]:
    """
    Show recent version deployments across all applications.
    
    This function returns recent release information sorted by release date,
    with optional filtering by application and configurable result limit.
    
    Args:
        limit: Number of recent releases to return (default: 10)
        application: Optional application ID to filter by (e.g., "web-app", "api-service")
        
    Returns:
        dict: Response containing recent releases information
    """
    logger.info(f"list_recent_releases called with limit={limit}, application={application}")
    
    # Validate limit parameter
    if limit <= 0:
        return {
            "status": "error",
            "error": "Limit must be a positive integer",
            "releases": [],
            "total_count": 0,
            "filters_applied": {
                "limit": limit,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    # Load releases data using our centralized data loader
    try:
        releases_data = load_json("releases.json")
        all_releases = releases_data.get("releases", [])
        
        if not all_releases:
            logger.warning("No releases data available")
            return {
                "status": "error",
                "error": "No releases data available",
                "releases": [],
                "total_count": 0,
                "filters_applied": {
                    "limit": limit,
                    "application": application
                },
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Apply application filter if provided
        filtered_releases = all_releases
        if application:
            filtered_releases = [r for r in filtered_releases if r["applicationId"] == application]
        
        # Sort by release date (most recent first)
        try:
            filtered_releases.sort(
                key=lambda x: datetime.fromisoformat(x["releaseDate"].replace('Z', '+00:00')), 
                reverse=True
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Error sorting releases by date: {e}")
            # Continue without sorting if date parsing fails
        
        # Apply limit
        limited_releases = filtered_releases[:limit]
        
        return {
            "status": "success",
            "releases": limited_releases,
            "total_count": len(limited_releases),
            "total_available": len(filtered_releases),
            "filters_applied": {
                "limit": limit,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except DataLoadError as e:
        logger.error(f"Error loading releases data: {e}")
        return {
            "status": "error",
            "error": f"Failed to load releases data: {str(e)}",
            "releases": [],
            "total_count": 0,
            "filters_applied": {
                "limit": limit,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Unexpected error processing releases data: {e}")
        return {
            "status": "error",
            "error": f"Failed to process releases data: {str(e)}",
            "releases": [],
            "total_count": 0,
            "filters_applied": {
                "limit": limit,
                "application": application
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }


def print_table(result: dict[str, Any]) -> None:
    """Print recent releases in table format."""
    if result["status"] == "error":
        print(f"Error: {result['error']}", file=sys.stderr)
        return
    
    releases = result["releases"]
    if not releases:
        print("No releases found matching the criteria.")
        return
    
    # Print header
    print(f"{'Application':<15} {'Version':<10} {'Release Date':<20} {'Author':<15} {'Notes':<30}")
    print("-" * 95)
    
    # Print releases
    for release in releases:
        app_id = release.get("applicationId", "N/A")[:14]
        version = release.get("version", "N/A")[:9]
        release_date = release.get("releaseDate", "N/A")[:19]
        author = release.get("author", "N/A")[:14]
        notes = release.get("releaseNotes", "N/A")[:29]
        
        print(f"{app_id:<15} {version:<10} {release_date:<20} {author:<15} {notes:<30}")
    
    total_available = result.get("total_available", result["total_count"])
    if result["total_count"] < total_available:
        print(f"\nShowing {result['total_count']} of {total_available} releases")
    else:
        print(f"\nTotal: {result['total_count']} releases")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for this command."""
    parser = argparse.ArgumentParser(
        description='Show recent version deployments across all applications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devops-cli releases                         # Get 10 most recent releases
  devops-cli releases --limit 20              # Get 20 most recent releases
  devops-cli releases --app web-app           # Filter by application
  devops-cli releases --app web-app --limit 5 # Filter by app, limit to 5
  devops-cli releases --format table         # Display as table
        """
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=10,
        help='Number of recent releases to return (default: 10)'
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
    result = list_recent_releases(parsed_args.limit, parsed_args.app)
    
    # Format and output result
    if parsed_args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_table(result)
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
