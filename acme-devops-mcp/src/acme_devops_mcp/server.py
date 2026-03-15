import asyncio
import sys
import json
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
import subprocess
import os
from pathlib import Path

# Import DevOps CLI business logic (for direct tools)
from acme_devops_cli.commands.deployment_status import get_deployment_status
from acme_devops_cli.commands.environment_health import check_environment_health
from acme_devops_cli.commands.recent_releases import list_recent_releases
from acme_devops_cli.commands.promote_release import promote_release

async def _run_cli_command(args: list[str]) -> dict:
    """
    Run the devops-cli tool as a subprocess and return the JSON results.
    """
    try:
        # Construct the command using current python interpreter to avoid uv overhead
        # Click global options must come before the command
        full_cmd = [sys.executable, "-m", "acme_devops_cli.main", "--format", "json"] + args
        
        # Execute the process with a timeout and explicit environment
        env = os.environ.copy()
        # Remove problematic environment variables to avoid conflicts with parent environment
        if "PYTHONPATH" in env:
            del env["PYTHONPATH"]
        if "VIRTUAL_ENV" in env:
            del env["VIRTUAL_ENV"]
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

async def _main():
    """
    Internal main entry point for the minimal MCP server.
    """
    # Set data directory for acme-devops-cli
    import os
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    os.environ["ACME_DATA_DIR"] = str(project_root / "acme-devops-cli" / "data")

    # Create the server instance
    server = Server("acme-devops-mcp")

    # Define tool list handler
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool.model_validate({
                "name": "ping",
                "description": "A simple ping tool to test connectivity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "The message to ping with."}
                    },
                    "required": ["message"],
                },
            }),
            types.Tool.model_validate({
                "name": "get_deployment_status",
                "description": "Get deployment status for applications across environments.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "application": {"type": "string", "description": "Optional application ID to filter by."},
                        "environment": {"type": "string", "description": "Optional environment to filter by."}
                    }
                },
            }),
            types.Tool.model_validate({
                "name": "check_environment_health",
                "description": "Get health status across all services and environments.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string", "description": "Optional environment to filter by."},
                        "application": {"type": "string", "description": "Optional application ID to filter by."}
                    }
                },
            }),
            types.Tool.model_validate({
                "name": "list_recent_releases",
                "description": "Show recent version deployments across all applications.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Number of recent releases to return (default: 10)."},
                        "application": {"type": "string", "description": "Optional application ID to filter by."}
                    }
                },
            }),
            types.Tool.model_validate({
                "name": "promote_release",
                "description": "Promote a release from one environment to another.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "applicationId": {"type": "string", "description": "Application to promote."},
                        "version": {"type": "string", "description": "Version to promote."},
                        "fromEnvironment": {"type": "string", "description": "Source environment."},
                        "toEnvironment": {"type": "string", "description": "Target environment."}
                    },
                    "required": ["applicationId", "version", "fromEnvironment", "toEnvironment"],
                },
            }),
            # Subprocess-based tools as requested
            types.Tool.model_validate({
                "name": "list-releases",
                "description": "List releases via subprocess call to devops-cli.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "Limit results."},
                        "app": {"type": "string", "description": "Filter by app ID."}
                    }
                }
            }),
            types.Tool.model_validate({
                "name": "check-health",
                "description": "Check health via subprocess call to devops-cli.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "env": {"type": "string", "description": "Filter by environment."}
                    }
                }
            })
        ]

    # Define the tool execution handler
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        """Handle tool calls."""
        args = arguments or {}
        
        if name == "ping":
            message = args.get("message", "")
            return [types.TextContent(type="text", text=f"Pong: {message}")]
        
        elif name == "get_deployment_status":
            result = get_deployment_status(
                application=args.get("application"),
                environment=args.get("environment")
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "check_environment_health":
            result = check_environment_health(
                environment=args.get("environment"),
                application=args.get("application")
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "list_recent_releases":
            result = list_recent_releases(
                limit=args.get("limit", 10),
                application=args.get("application")
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        elif name == "promote_release":
            result = promote_release(
                applicationId=args.get("applicationId"),
                version=args.get("version"),
                fromEnvironment=args.get("fromEnvironment"),
                toEnvironment=args.get("toEnvironment")
            )
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        # Subprocess-based implementations
        elif name == "list-releases":
            cmd_args = ["releases"]
            if "limit" in args:
                cmd_args += ["--limit", str(args["limit"])]
            if "app" in args:
                cmd_args += ["--app", args["app"]]
            result = await _run_cli_command(cmd_args)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "check-health":
            cmd_args = ["health"]
            if "env" in args:
                cmd_args += ["--env", args["env"]]
            result = await _run_cli_command(cmd_args)
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            
        raise ValueError(f"Unknown tool: {name}")

    # Use stdio transport for communication
    async with stdio_server() as (read_stream, write_stream):
        print("Acme DevOps MCP Server starting...", file=sys.stderr)
        # Run the server with the handshake
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

def main():
    """
    Public entry point for the minimal MCP server.
    """
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
