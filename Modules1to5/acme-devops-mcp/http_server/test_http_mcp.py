
import asyncio
import json
import pytest
from main import mcp

@pytest.mark.asyncio
async def test_get_deployment_status():
    """Verify get-deployment-status tool."""
    # Call with no params
    result = await mcp.call_tool("get_deployment_status", {})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "deployments" in data["data"]
    assert len(data["data"]["deployments"]) > 0

@pytest.mark.asyncio
async def test_get_performance_metrics():
    """Verify get-performance-metrics tool."""
    result = await mcp.call_tool("get_performance_metrics", {"time_range": "1h"})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "metrics" in data["data"]

@pytest.mark.asyncio
async def test_check_environment_health():
    """Verify check-environment-health tool."""
    result = await mcp.call_tool("check_environment_health", {"detailed": True})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "healthStatus" in data["data"]

@pytest.mark.asyncio
async def test_get_log_entries():
    """Verify get-log-entries tool."""
    result = await mcp.call_tool("get_log_entries", {"limit": 5})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "logs" in data["data"]
    assert len(data["data"]["logs"]) <= 5

if __name__ == "__main__":
    # Optional: run manually if not using pytest
    async def run_tests():
        print("Testing get_deployment_status...")
        result = await mcp.call_tool("get_deployment_status", {})
        print(result[0][0].text)
        
    asyncio.run(run_tests())
