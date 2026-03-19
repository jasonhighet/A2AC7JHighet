import json
import inspect
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from .models import ToolCall, ToolResult

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable):
        self.tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler
        )

    async def execute(self, tool_call: ToolCall) -> ToolResult:
        if tool_call.name not in self.tools:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error: Tool {tool_call.name} not found.",
                success=False
            )
        
        tool = self.tools[tool_call.name]
        try:
            if inspect.iscoroutinefunction(tool.handler):
                result = await tool.handler(**tool_call.arguments)
            else:
                result = tool.handler(**tool_call.arguments)
                
            return ToolResult(
                tool_call_id=tool_call.id,
                content=json.dumps(result) if not isinstance(result, (str, int, float, bool)) else str(result),
                success=True
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error executing tool {tool_call.name}: {str(e)}",
                success=False
            )

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters
                }
            }
            for t in self.tools.values()
        ]

# Mock Release Assessment Tools
def get_release_summary(release_id: str):
    """Get a summary of a release including test results and metrics."""
    if "999" in release_id:
        return {
            "id": release_id,
            "status": "failed",
            "tests": {"total": 100, "passed": 85, "failed": 15},
            "metrics": {"error_rate": "2.5%"}
        }
    if "123" in release_id:
        return {
            "id": release_id,
            "status": "success",
            "tests": {"total": 100, "passed": 100, "failed": 0},
            "metrics": {"error_rate": "0.1%"}
        }
    return {"error": f"Release {release_id} not found"}

def file_risk_report(filename: str):
    """Generate a risk report for a specific file based on recent changes."""
    if "core" in filename:
        return {"filename": filename, "risk_score": 0.8, "reason": "Modified critical path functions"}
    return {"filename": filename, "risk_score": 0.2, "reason": "Minor changes"}

default_registry = ToolRegistry()
default_registry.register(
    name="get_release_summary",
    description="Retrieve high-level release information including version, changes, tests, and metrics.",
    parameters={
        "type": "object",
        "properties": {
            "release_id": {"type": "string", "description": "The unique identifier for the release (e.g., 'v2.1.0')"}
        },
        "required": ["release_id"]
    },
    handler=get_release_summary
)
default_registry.register(
    name="file_risk_report",
    description="Generate a risk report for a specific file based on recent changes.",
    parameters={
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "The name of the file to analyze"}
        },
        "required": ["filename"]
    },
    handler=file_risk_report
)
