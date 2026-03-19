import uuid
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    success: bool = True

class Message(BaseModel):
    role: str # 'system', 'user', 'assistant', 'tool'
    content: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_prompt: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EvalScenario(BaseModel):
    id: str
    name: str
    description: str
    user_input: str
    expected_risk: str # 'low', 'high', 'unknown'
    expected_tools: List[str] = [] # List of tool names expected to be called

class EvalResult(BaseModel):
    scenario_id: str
    passed: bool
    actual_risk: Optional[str] = None
    actual_tools: List[str] = []
    reasoning: str
    latency_ms: float = 0.0
    tokens_used: int = 0
