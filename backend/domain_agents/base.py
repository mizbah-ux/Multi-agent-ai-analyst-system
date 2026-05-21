from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from tools.execution_engine import tool_execution_engine


@dataclass
class AgentResult:
    agent_name: str
    output: Any
    confidence_score: float = 0.75
    reasoning_summary: str = ""
    validation_status: str = "pending"


class BaseDomainAgent:
    agent_name = "Base Agent"
    permissions: Iterable[str] = ()

    def run_tool(self, tool_name: str, payload: Dict[str, Any], task_id: Optional[int] = None):
        return tool_execution_engine.execute(
            tool_name,
            payload,
            user_permissions=self.permissions,
            task_id=task_id,
        )
