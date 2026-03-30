import asyncio
import sys
import json
import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Import DevOps CLI business logic (for direct tools)
from acme_devops_cli.commands.deployment_status import get_deployment_status as get_status_logic
from acme_devops_cli.commands.environment_health import check_environment_health as check_health_logic
from acme_devops_cli.commands.recent_releases import list_recent_releases as list_releases_logic
from acme_devops_cli.commands.promote_release import promote_release as promote_logic

# Initialize FastMCP
mcp = FastMCP("acme-devops")

# Set data directory for acme-devops-cli
project_root = Path(__file__).resolve().parent.parent.parent.parent
os.environ["ACME_DATA_DIR"] = str(project_root / "acme-devops-cli" / "data")

async def _run_cli_command(args: list[str]) -> dict:
    """
    Run the devops-cli tool as a subprocess and return the JSON results.
    """
    try:
        # Construct the command using current python interpreter
        full_cmd = [sys.executable, "-m", "acme_devops_cli.main", "--format", "json"] + args
        
        env = os.environ.copy()
        # Set data directory explicitly
        env["ACME_DATA_DIR"] = str(project_root / "acme-devops-cli" / "data")
        
        # Ensure local CLI source is prioritized if it exists
        cli_src = project_root / "acme-devops-cli" / "src"
        if cli_src.exists():
            current_pp = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = str(cli_src) + (os.pathsep + current_pp if current_pp else "")
            
        # Ensure utf-8 encoding
        env["PYTHONIOENCODING"] = "utf-8"
        
        proc = await asyncio.create_subprocess_exec(
            *full_cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except:
                pass
            return {"status": "error", "error": "CLI command timed out"}

        exit_code = proc.returncode
        
        if exit_code != 0:
            err_msg = stderr.decode().strip()
            return {
                "status": "error",
                "error": f"CLI command failed with exit code {exit_code}",
                "stderr": err_msg
            }
            
        try:
            return json.loads(stdout.decode())
        except json.JSONDecodeError:
            return {
                "status": "error",
                "error": "Failed to parse CLI output as JSON",
                "stdout": stdout.decode().strip()
            }
            
    except Exception as e:
        return {
            "status": "error",
            "error": f"Unexpected error running CLI command: {str(e)}"
        }

@mcp.tool()
async def ping(message: str) -> str:
    """A simple ping tool to test connectivity."""
    return f"Pong: {message}"

@mcp.tool()
async def get_deployment_status(application: str | None = None, environment: str | None = None) -> str:
    """Get deployment status for applications across environments."""
    result = get_status_logic(
        application=application,
        environment=environment
    )
    return json.dumps(result, indent=2)

@mcp.tool()
async def check_environment_health(environment: str | None = None, application: str | None = None) -> str:
    """Get health status across all services and environments."""
    result = check_health_logic(
        environment=environment,
        application=application
    )
    return json.dumps(result, indent=2)

@mcp.tool()
async def list_recent_releases(limit: int = 10, application: str | None = None) -> str:
    """Show recent version deployments across all applications."""
    result = list_releases_logic(
        limit=limit,
        application=application
    )
    return json.dumps(result, indent=2)

@mcp.tool()
async def promote_release(applicationId: str, version: str, fromEnvironment: str, toEnvironment: str) -> str:
    """Promote a release from one environment to another."""
    result = promote_logic(
        applicationId=applicationId,
        version=version,
        fromEnvironment=fromEnvironment,
        toEnvironment=toEnvironment
    )
    return json.dumps(result, indent=2)

@mcp.tool(name="list-releases")
async def list_releases_subprocess(limit: int | None = None, app: str | None = None) -> str:
    """List releases via subprocess call to devops-cli."""
    cmd_args = ["releases"]
    if limit is not None:
        cmd_args += ["--limit", str(limit)]
    if app:
        cmd_args += ["--app", app]
    result = await _run_cli_command(cmd_args)
    return json.dumps(result, indent=2)

@mcp.tool(name="check-health")
async def check_health_subprocess(env: str | None = None) -> str:
    """Check health via subprocess call to devops-cli."""
    cmd_args = ["health"]
    if env:
        cmd_args += ["--env", env]
    result = await _run_cli_command(cmd_args)
    return json.dumps(result, indent=2)

@mcp.tool(name="promote-release")
async def promote_release_subprocess(
    application: str,
    version: str,
    from_environment: str,
    to_environment: str
) -> str:
    """
    Promote a release via subprocess call to devops-cli.
    
    Args:
        application: Application ID (e.g., 'web-app')
        version: Version string (e.g., 'v1.2.3')
        from_environment: Source environment (e.g., 'staging', 'uat')
        to_environment: Target environment (e.g., 'prod', 'uat')
    """
    # Validation
    valid_envs = ["staging", "uat", "prod", "test", "dev"]
    if from_environment not in valid_envs or to_environment not in valid_envs:
        error_msg = f"Invalid environment. Valid environments are: {', '.join(valid_envs)}"
        return json.dumps({"status": "error", "error": error_msg}, indent=2)

    # Production Warning
    warnings = []
    if to_environment == "prod":
        warnings.append("WARNING: This is a promotion to PRODUCTION. High impact operation.")

    cmd_args = [
        "promote",
        "--app", application,
        "--release", version,
        "--from", from_environment,
        "--to", to_environment
    ]
    result = await _run_cli_command(cmd_args)
    
    if warnings:
        result["warnings"] = warnings
        
    return json.dumps(result, indent=2)

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
