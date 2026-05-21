from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    tool_name: str
    description: str
    capability_type: str
    permissions: List[str] = Field(default_factory=list)
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class RegisteredTool(BaseModel):
    metadata: ToolMetadata
    handler: Callable[[Dict[str, Any]], Any]

    class Config:
        arbitrary_types_allowed = True


class ToolExecutionResult(BaseModel):
    tool_name: str
    status: str
    output: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float = 0.0

