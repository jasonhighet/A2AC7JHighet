import pytest
import json
from acme_devops_mcp.server import mcp

@pytest.mark.asyncio
async def test_ping():
    """Test the ping tool directly via FastMCP.call_tool."""
    result = await mcp.call_tool("ping", {"message": "Direct Test"})
    # FastMCP.call_tool returns (list[ContentBlock], dict) when convert_result=True
    content, _ = result
    assert "Pong: Direct Test" in content[0].text

@pytest.mark.asyncio
async def test_get_deployment_status():
    """Test get_deployment_status tool directly."""
    result = await mcp.call_tool("get_deployment_status", {"application": "web-app", "environment": "prod"})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert len(data["deployments"]) > 0
    assert data["deployments"][0]["applicationId"] == "web-app"

@pytest.mark.asyncio
async def test_check_environment_health():
    """Test check_environment_health tool directly."""
    result = await mcp.call_tool("check_environment_health", {"environment": "prod"})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "overall_status" in data

@pytest.mark.asyncio
async def test_list_recent_releases():
    """Test list_recent_releases tool directly."""
    result = await mcp.call_tool("list_recent_releases", {"limit": 5})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert len(data["releases"]) <= 5

@pytest.mark.asyncio
async def test_promote_release():
    """Test promote_release tool directly."""
    # We need a valid version from data
    status_result = await mcp.call_tool("get_deployment_status", {"application": "web-app", "environment": "uat"})
    content, _ = status_result
    status_data = json.loads(content[0].text)
    version = status_data["deployments"][0]["version"]

    result = await mcp.call_tool("promote_release", {
        "applicationId": "web-app",
        "version": version,
        "fromEnvironment": "uat",
        "toEnvironment": "prod"
    })
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_list_releases_subprocess():
    """Test list-releases (subprocess) tool directly."""
    result = await mcp.call_tool("list-releases", {"limit": 2})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "releases" in data

@pytest.mark.asyncio
async def test_check_health_subprocess():
    """Test check-health (subprocess) tool directly."""
    result = await mcp.call_tool("check-health", {"env": "prod"})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert "health_checks" in data

@pytest.mark.asyncio
async def test_invalid_app_returns_empty():
    """Test tool behavior when application is not found (should return success but empty list).."""
    result = await mcp.call_tool("get_deployment_status", {"application": "non-existent-app"})
    content, _ = result
    data = json.loads(content[0].text)
    assert data["status"] == "success"
    assert data["total_count"] == 0
    assert len(data["deployments"]) == 0
