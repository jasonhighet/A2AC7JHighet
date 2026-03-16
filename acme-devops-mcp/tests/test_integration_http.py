
import pytest
import respx
from httpx import Response
from http_server.main import mcp

@pytest.mark.asyncio
async def test_ping():
    result = await mcp.call_tool("ping", {"message": "Test In-Memory"})
    # Result is a list of content blocks
    content = result[0]
    assert "Test In-Memory" in content[0].text
    assert "status\": \"success\"" in content[0].text

@pytest.mark.asyncio
@respx.mock
async def test_get_deployments():
    # Mock the API response
    respx.get("http://localhost:8000/api/v1/deployments").mock(return_value=Response(200, json={
        "status": "success",
        "deployments": [{"id": "dep-1", "applicationId": "web-app", "environment": "prod"}]
    }))
    
    result = await mcp.call_tool("get_deployments", {"application": "web-app"})
    content = result[0]
    assert "dep-1" in content[0].text
    assert "web-app" in content[0].text

@pytest.mark.asyncio
@respx.mock
async def test_get_metrics():
    # Mock the API response
    respx.get("http://localhost:8000/api/v1/metrics").mock(return_value=Response(200, json={
        "status": "success",
        "metrics": {"cpu": 45, "memory": 72}
    }))
    
    result = await mcp.call_tool("get_metrics", {"application": "web-app"})
    content = result[0]
    assert "cpu\": 45" in content[0].text

@pytest.mark.asyncio
@respx.mock
async def test_api_error_handling():
    # Mock a 500 error
    respx.get("http://localhost:8000/api/v1/health").mock(return_value=Response(500))
    
    result = await mcp.call_tool("get_health", {"detailed": True})
    content = result[0]
    assert "error" in content[0].text
    assert "500" in content[0].text

@pytest.mark.asyncio
@respx.mock
async def test_api_unavailable():
    # Mock a connection error
    respx.get("http://localhost:8000/api/v1/logs").side_effect = Exception("Connection Refused")
    
    result = await mcp.call_tool("get_logs", {"limit": 5})
    content = result[0]
    assert "error" in content[0].text
    assert "Connection Refused" in content[0].text

@pytest.mark.asyncio
async def test_environment_validation():
    # Test invalid environment (should fail before API call)
    result = await mcp.call_tool("get_health", {"environment": "invalid-env"})
    content = result[0]
    assert "error" in content[0].text
    assert "Invalid environment" in content[0].text

@pytest.mark.asyncio
@respx.mock
async def test_pagination_parameters():
    # Verify limit and offset are passed to params
    mock_deploy = respx.get("http://localhost:8000/api/v1/deployments").mock(return_value=Response(200, json={
        "status": "success", "deployments": []
    }))
    
    await mcp.call_tool("get_deployments", {"limit": 5, "offset": 10})
    
    # Check the call parameters
    assert mock_deploy.calls[0].request.url.params["limit"] == "5"
    assert mock_deploy.calls[0].request.url.params["offset"] == "10"
