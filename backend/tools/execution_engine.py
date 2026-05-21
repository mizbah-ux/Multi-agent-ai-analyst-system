import json
import time
from typing import Any, Dict, Iterable, Optional

from jsonschema import ValidationError, validate

from models.schemas import ToolExecutionRecord
from services.db_service import SessionLocal
from tools.registry import tool_registry
from tools.schemas import ToolExecutionResult


class ToolExecutionEngine:
    def execute(
        self,
        tool_name: str,
        payload: Dict[str, Any],
        user_permissions: Optional[Iterable[str]] = None,
        task_id: Optional[int] = None,
    ) -> ToolExecutionResult:
        tool = tool_registry.get(tool_name)
        if not tool:
            return ToolExecutionResult(
                tool_name=tool_name,
                status="failed",
                error=f"Tool '{tool_name}' is not registered",
            )

        granted = set(user_permissions or [])
        required = set(tool.metadata.permissions)
        if required and not required.issubset(granted):
            return ToolExecutionResult(
                tool_name=tool_name,
                status="failed",
                error=f"Missing permissions: {', '.join(sorted(required - granted))}",
            )

        started_at = time.perf_counter()
        error = None
        output = None
        status = "completed"

        try:
            if tool.metadata.input_schema:
                validate(instance=payload, schema=tool.metadata.input_schema)
            output = tool.handler(payload)
            if tool.metadata.output_schema:
                validate(instance=output, schema=tool.metadata.output_schema)
        except ValidationError as exc:
            status = "failed"
            error = f"Schema validation failed: {exc.message}"
        except Exception as exc:
            status = "failed"
            error = str(exc)

        latency_ms = (time.perf_counter() - started_at) * 1000
        self._record(tool_name, tool.metadata.capability_type, status, latency_ms, payload, output, error, task_id)
        return ToolExecutionResult(
            tool_name=tool_name,
            status=status,
            output=output,
            error=error,
            latency_ms=latency_ms,
        )

    def _record(self, tool_name, capability_type, status, latency_ms, payload, output, error, task_id):
        db = SessionLocal()
        try:
            output_summary = None
            if output is not None:
                output_summary = json.dumps(output, default=str)[:4000]
            db.add(
                ToolExecutionRecord(
                    task_id=task_id,
                    tool_name=tool_name,
                    capability_type=capability_type,
                    status=status,
                    latency_ms=latency_ms,
                    input_payload=json.dumps(payload, default=str)[:4000],
                    output_summary=output_summary,
                    error_message=error,
                )
            )
            db.commit()
        finally:
            db.close()


tool_execution_engine = ToolExecutionEngine()
