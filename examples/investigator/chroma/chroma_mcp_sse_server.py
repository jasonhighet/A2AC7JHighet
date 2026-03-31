#!/usr/bin/env python3
"""
Run chroma-mcp server in SSE transport mode.

This allows the agent to connect via HTTP/SSE instead of stdio,
avoiding the macOS KqueueSelector hang issue.
"""
import argparse
import asyncio
import os
import sys
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Set up argument parser
parser = argparse.ArgumentParser(description="Run chroma-mcp in SSE mode")
parser.add_argument("--host", default=os.getenv("CHROMA_MCP_HOST", "0.0.0.0"), help="Host to bind to")
parser.add_argument("--port", type=int, default=int(os.getenv("CHROMA_MCP_PORT", "8001")), help="Port to bind to")
parser.add_argument("--client-type", default="persistent", choices=["http", "cloud", "persistent", "ephemeral"],
                   help="Chroma client type")
parser.add_argument("--data-dir", default=os.getenv("CHROMA_DATA_DIR", "./data/chromadb"),
                   help="Data directory for persistent client")
parser.add_argument("--log-level", default="info", help="Log level")

args = parser.parse_args()

# Set environment variables for chroma-mcp configuration
os.environ["CHROMA_CLIENT_TYPE"] = args.client_type
if args.data_dir:
    os.environ["CHROMA_DATA_DIR"] = args.data_dir

print("Starting chroma-mcp server in SSE mode...")
print(f"  Host: {args.host}")
print(f"  Port: {args.port}")
print(f"  Client type: {args.client_type}")
print(f"  Data directory: {args.data_dir}")
print(f"  SSE endpoint: http://{args.host}:{args.port}/sse")
print()

# Import the server
from chroma_mcp.server import mcp
import uvicorn

# Override the settings
mcp.settings.host = args.host
mcp.settings.port = args.port
mcp.settings.log_level = args.log_level.upper()

# Run the SSE server
async def main():
    """Run the SSE server"""
    starlette_app = mcp.sse_app()

    config = uvicorn.Config(
        starlette_app,
        host=args.host,
        port=args.port,
        log_level=args.log_level,
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down chroma-mcp server...")
        sys.exit(0)
