from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]

class ToolResult(BaseModel):
    tool_call_id: str
    content: str
    success: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Message(BaseModel):
    role: str
    content: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_prompt: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
