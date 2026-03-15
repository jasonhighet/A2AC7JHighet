
from mcp.server.fastmcp import FastMCP
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("acme-devops-http-mcp")

# Initialize FastMCP
mcp = FastMCP("acme-devops-http")

@mcp.tool()
async def ping(message: str) -> str:
    """
    A simple ping tool to test connectivity.
    
    Args:
        message: The message to echo back.
    """
    logger.info(f"Received ping with message: {message}")
    return f"Pong: {message}"

def main():
    """Main entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
