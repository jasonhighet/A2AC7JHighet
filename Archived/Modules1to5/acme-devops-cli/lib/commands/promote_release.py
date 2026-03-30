#!/usr/bin/env python3
"""
Promote Release CLI Command

This module provides CLI functionality to simulate promoting a release from one
environment to another in the DevOps dashboard.
"""

import argparse
import json
import sys
import logging
import uuid
from typing import Any
from datetime import datetime

# Import our local data loader
from lib.data_loader import load_json, DataLoadError

# Configure logging
logger = logging.getLogger(__name__)


def promote_release(
    applicationId: str,
    version: str,
    fromEnvironment: str,
    toEnvironment: str
) -> dict[str, Any]:
    """
    Simulate promoting a release from one environment to another.
    
    This function simulates the promotion of a release version from a source environment
    to a target environment, performing validation checks and creating a deployment record.
    
    Args:
        applicationId: Application to promote (required)
        version: Version to promote (required)
        fromEnvironment: Source environment (required)
        toEnvironment: Target environment (required)
        
    Returns:
        dict: Response containing promotion status and deployment details
    """
    logger.info(f"promote_release called with applicationId={applicationId}, version={version}, "
                f"fromEnvironment={fromEnvironment}, toEnvironment={toEnvironment}")
    
    # Validate required parameters
    if not all([applicationId, version, fromEnvironment, toEnvironment]):
        return {
            "status": "error",
            "error": "All parameters are required: applicationId, version, fromEnvironment, toEnvironment",
            "promotion_details": None,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    if fromEnvironment == toEnvironment:
        return {
            "status": "error",
            "error": "Source and target environments cannot be the same",
            "promotion_details": None,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    
    try:
        # Load data files using our centralized data loader
        deployments_data = load_json("deployments.json")
        releases_data = load_json("releases.json")
        config = load_json("config.json")
        
        deployments = deployments_data.get("deployments", [])
        releases = releases_data.get("releases", [])
        
        if not deployments or not releases or not config:
            return {
                "status": "error",
                "error": "Failed to load required data files",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Validate application exists
        valid_applications = [app["id"] for app in config.get("applications", [])]
        if applicationId not in valid_applications:
            return {
                "status": "error",
                "error": f"Application '{applicationId}' not found. Valid applications: {valid_applications}",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Validate environments exist
        valid_environments = [env["id"] for env in config.get("environments", [])]
        if fromEnvironment not in valid_environments:
            return {
                "status": "error",
                "error": f"Source environment '{fromEnvironment}' not found. Valid environments: {valid_environments}",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        if toEnvironment not in valid_environments:
            return {
                "status": "error",
                "error": f"Target environment '{toEnvironment}' not found. Valid environments: {valid_environments}",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Check if version exists in releases
        release = next((r for r in releases if r["applicationId"] == applicationId and r["version"] == version), None)
        if not release:
            return {
                "status": "error",
                "error": f"Release version '{version}' not found for application '{applicationId}'",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Check if version is currently deployed in source environment
        source_deployment = next((d for d in deployments 
                                if d["applicationId"] == applicationId 
                                and d["environment"] == fromEnvironment 
                                and d["version"] == version 
                                and d["status"] == "deployed"), None)
        
        if not source_deployment:
            return {
                "status": "error",
                "error": f"Version '{version}' is not currently deployed in '{fromEnvironment}' environment",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Check if there's already a deployment in progress for the target environment
        existing_deployment = next((d for d in deployments 
                                  if d["applicationId"] == applicationId 
                                  and d["environment"] == toEnvironment 
                                  and d["status"] == "in-progress"), None)
        
        if existing_deployment:
            return {
                "status": "error",
                "error": f"Deployment already in progress for '{applicationId}' in '{toEnvironment}' environment",
                "promotion_details": None,
                "timestamp": datetime.now().isoformat() + "Z"
            }
        
        # Simulate promotion success/failure based on simple rules
        # In a real system, this would trigger actual deployment processes
        promotion_success = _simulate_promotion_outcome(applicationId, toEnvironment)
        
        # Create new deployment record
        new_deployment = {
            "id": f"deploy-{str(uuid.uuid4())[:8]}",
            "applicationId": applicationId,
            "environment": toEnvironment,
            "version": version,
            "status": "deployed" if promotion_success else "failed",
            "deployedAt": datetime.now().isoformat() + "Z",
            "deployedBy": "system@company.com",  # In real system, would use actual user
            "commitHash": release["commitHash"]
        }
        
        promotion_details = {
            "deployment": new_deployment,
            "source_deployment": source_deployment,
            "release_info": {
                "version": release["version"],
                "releaseDate": release["releaseDate"],
                "author": release["author"],
                "releaseNotes": release["releaseNotes"]
            },
            "promotion_path": f"{fromEnvironment} → {toEnvironment}",
            "promotion_successful": promotion_success
        }
        
        return {
            "status": "success",
            "message": f"Successfully promoted {applicationId} {version} from {fromEnvironment} to {toEnvironment}" if promotion_success 
                      else f"Promotion failed for {applicationId} {version} from {fromEnvironment} to {toEnvironment}",
            "promotion_details": promotion_details,
            "timestamp": datetime.now().isoformat() + "Z"
        }
        
    except DataLoadError as e:
        logger.error(f"Error loading data during release promotion: {e}")
        return {
            "status": "error",
            "error": f"Failed to load required data: {str(e)}",
            "promotion_details": None,
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        logger.error(f"Unexpected error during release promotion: {e}")
        return {
            "status": "error",
            "error": f"Failed to promote release: {str(e)}",
            "promotion_details": None,
            "timestamp": datetime.now().isoformat() + "Z"
        }


def _simulate_promotion_outcome(applicationId: str, toEnvironment: str) -> bool:
    """
    Simulate promotion outcome based on simple rules.
    
    In a real system, this would involve actual deployment processes,
    health checks, and validation steps.
    
    Args:
        applicationId: The application being promoted
        toEnvironment: The target environment
        
    Returns:
        bool: True if promotion succeeds, False if it fails
    """
    # Simple simulation rules:
    # - Promotions to prod have 90% success rate
    # - Promotions to uat have 95% success rate  
    # - Promotions to staging have 98% success rate
    # - worker-service has lower success rates (simulating a problematic service)
    
    import random
    
    base_success_rates = {
        "prod": 0.90,
        "uat": 0.95,
        "staging": 0.98
    }
    
    success_rate = base_success_rates.get(toEnvironment, 0.95)
    
    # Reduce success rate for worker-service
    if applicationId == "worker-service":
        success_rate *= 0.8
    
    return random.random() < success_rate


def print_table(result: dict[str, Any]) -> None:
    """Print promotion result in table format."""
    if result["status"] == "error":
        print(f"Error: {result['error']}", file=sys.stderr)
        return
    
    print(f"Status: {result['status'].upper()}")
    print(f"Message: {result['message']}")
    print()
    
    promotion_details = result.get("promotion_details")
    if not promotion_details:
        return
    
    # Print promotion summary
    print("Promotion Details:")
    print(f"  Path: {promotion_details['promotion_path']}")
    print(f"  Success: {promotion_details['promotion_successful']}")
    print()
    
    # Print deployment info
    deployment = promotion_details["deployment"]
    print("New Deployment:")
    print(f"  ID: {deployment['id']}")
    print(f"  Application: {deployment['applicationId']}")
    print(f"  Environment: {deployment['environment']}")
    print(f"  Version: {deployment['version']}")
    print(f"  Status: {deployment['status']}")
    print(f"  Deployed At: {deployment['deployedAt']}")
    print(f"  Deployed By: {deployment['deployedBy']}")
    print()
    
    # Print release info
    release_info = promotion_details["release_info"]
    print("Release Information:")
    print(f"  Version: {release_info['version']}")
    print(f"  Release Date: {release_info['releaseDate']}")
    print(f"  Author: {release_info['author']}")
    print(f"  Notes: {release_info['releaseNotes']}")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for this command."""
    parser = argparse.ArgumentParser(
        description='Simulate promoting a release from one environment to another',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  devops-cli promote web-app v2.1.4 uat prod    # Promote web-app v2.1.4 from uat to prod
  devops-cli promote api-service v1.8.2 prod uat    # Deomote api-service v1.8.2 from prod to uat
  devops-cli promote --format table analytics-dashboard v1.5.0 uat prod  # Display as table
        """
    )
    
    parser.add_argument(
        'application',
        help='Application ID to promote (e.g., "web-app", "api-service")'
    )
    parser.add_argument(
        'version',
        help='Version to promote (e.g., "v1.2.3")'
    )
    parser.add_argument(
        'from_environment',
        help='Source environment (e.g., "staging", "uat")'
    )
    parser.add_argument(
        'to_environment',
        help='Target environment (e.g., "prod", "uat")'
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
    result = promote_release(
        parsed_args.application,
        parsed_args.version,
        parsed_args.from_environment,
        parsed_args.to_environment
    )
    
    # Format and output result
    if parsed_args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print_table(result)
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1)


if __name__ == '__main__':
    main()
