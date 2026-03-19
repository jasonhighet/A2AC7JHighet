import pytest
import json
from .tools import ToolRegistry, get_release_summary, file_risk_report
from .models import ToolCall

@pytest.mark.asyncio
async def test_tool_registry_registration_and_execution():
    registry = ToolRegistry()
    def sample_handler(x: int, y: int):
        return x + y
    
    registry.register(
        name="add",
        description="add numbers",
        parameters={"type": "object", "properties": {"x": {"type": "int"}, "y": {"type": "int"}}},
        handler=sample_handler
    )
    
    call = ToolCall(id="1", name="add", arguments={"x": 5, "y": 10})
    result = await registry.execute(call)
    
    assert result.success is True
    assert result.content == "15"

@pytest.mark.asyncio
async def test_get_release_summary():
    registry = ToolRegistry()
    registry.register(
        name="get_release_summary",
        description="test",
        parameters={},
        handler=get_release_summary
    )
    
    call = ToolCall(id="2", name="get_release_summary", arguments={"release_id": "v2.1.0"})
    result = await registry.execute(call)
    
    assert result.success is True
    data = json.loads(result.content)
    assert data["version"] == "v2.1.0"

def test_get_definitions():
    registry = ToolRegistry()
    registry.register("foo", "bar", {"p": 1}, lambda x: x)
    defs = registry.get_definitions()
    assert len(defs) == 1
    assert defs[0]["function"]["name"] == "foo"
