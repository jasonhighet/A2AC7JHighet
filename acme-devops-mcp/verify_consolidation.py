
import asyncio
import json
import sys
from stdio_server.main import mcp as stdio_mcp
from http_server.main import mcp as http_mcp

async def test_stdio_server():
    print("Testing stdio_server...")
    # Test ping
    result = await stdio_mcp.call_tool("ping", {"message": "Final Consolidate Test"})
    content, _ = result
    print(f"Ping result: {content[0].text}")
    
    # Test status via subprocess
    print("Testing get_deployment_status (stdio)...")
    result = await stdio_mcp.call_tool("get_deployment_status", {"application": "web-app"})
    content, _ = result
    print(f"Status result: {content[0].text[:100]}...")

async def test_http_server():
    print("\nTesting http_server...")
    # Test get_deployments via HTTP
    print("Testing get_deployments (http)...")
    try:
        result = await http_mcp.call_tool("get_deployments", {"application": "web-app"})
        content, _ = result
        print(f"Deployments result: {content[0].text[:100]}...")
    except Exception as e:
        print(f"HTTP Server test failed: {e}. Is the API server running?")

async def main():
    await test_stdio_server()
    await test_http_server()

if __name__ == "__main__":
    asyncio.run(main())
