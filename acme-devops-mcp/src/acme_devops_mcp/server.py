import asyncio
import sys

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions

async def _main():
    """
    Internal main entry point for the minimal MCP server.
    """
    # Create the server instance
    server = Server("acme-devops-mcp")

    # Define the ping tool handler
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="ping",
                description="A simple ping tool to test connectivity.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The message to ping with."
                        }
                    },
                    "required": ["message"],
                },
            )
        ]

    # Define the tool execution handler
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        """Handle tool calls."""
        if name == "ping":
            message = (arguments or {}).get("message", "")
            return [
                types.TextContent(
                    type="text",
                    text=f"Pong: {message}"
                )
            ]
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
