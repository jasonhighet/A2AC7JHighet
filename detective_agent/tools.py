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
def get_release_summary(release_id: str) -> Dict[str, Any]:
    """Mock implementation of get_release_summary."""
    releases = {
        "v2.1.0": {
            "version": "v2.1.0",
            "changes": ["Added payment processing", "Fixed authentication bug"],
            "tests": {"passed": 142, "failed": 2, "skipped": 5},
            "deployment_metrics": {
                "error_rate": 0.02,
                "response_time_p95": 450
            }
        },
        "v2.0.0": {
            "version": "v2.0.0",
            "changes": ["Initial release"],
            "tests": {"passed": 100, "failed": 0, "skipped": 0},
            "deployment_metrics": {
                "error_rate": 0.00,
                "response_time_p95": 200
            }
        }
    }
    return releases.get(release_id, {"error": "Release not found"})

def file_risk_report(release_id: str, severity: str, findings: List[str]) -> Dict[str, Any]:
    """Mock implementation of file_risk_report."""
    return {
        "status": "success",
        "report_id": f"risk-{release_id}-{severity}",
        "message": f"Risk report filed for {release_id} with severity {severity}"
    }

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
    description="Submit a risk assessment report for a release.",
    parameters={
        "type": "object",
        "properties": {
            "release_id": {"type": "string", "description": "The unique identifier for the release"},
            "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"], "description": "The assessed severity level"},
            "findings": {"type": "array", "items": {"type": "string"}, "description": "Key findings or concerns identified"}
        },
        "required": ["release_id", "severity", "findings"]
    },
    handler=file_risk_report
)
