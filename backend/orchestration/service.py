import json
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from core.config import settings
from evaluation.engine import evaluation_engine
from events.dispatcher import publish_event
from events.events import EventType
from events.retry_manager import retry_manager
from memory.retrieval_service import retrieval_service
from memory.short_term import short_term_memory
from models.schemas import Task, Workflow
from observability.metrics import record_task_completion, record_tool_latency
from orchestration.lifecycle import record_agent_state, transition_task
from orchestration.state_machine import TaskState
from services.db_service import SessionLocal
from services.log_service import log_event
from tools.builtin_tools import register_builtin_tools
from tools.execution_engine import tool_execution_engine


class OrchestrationService:
    """Central control plane around the existing analyst pipeline."""

    def __init__(self):
        register_builtin_tools()
        self.permissions = {
            "tool:data",
            "tool:analysis",
            "tool:visualization",
            "tool:reporting",
            "tool:retrieval",
        }

    def run_analysis_workflow(
        self,
        task_id: int,
        file_id: str,
        user_request: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        started = time.perf_counter()
        workflow_id = f"wf-{task_id}"
        db = SessionLocal()
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            db.close()
            raise RuntimeError(f"Task {task_id} not found")

        if not task.state:
            task.state = TaskState.PENDING.value
        task.workflow_id = workflow_id
        task.max_retries = task.max_retries if task.max_retries is not None else settings.DEFAULT_MAX_RETRIES
        db.add(task)
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            workflow = Workflow(id=workflow_id)
        workflow.user_id = user_id
        workflow.name = "CSV analysis workflow"
        workflow.status = "running"
        workflow.dependency_graph = json.dumps(self.workflow_graph())
        db.add(workflow)
        db.commit()

        try:
            publish_event(
                EventType.TASK_CREATED,
                task_id=task_id,
                workflow_id=workflow_id,
                payload={"file_id": file_id, "user_request": user_request},
            )
            transition_task(db, task, TaskState.PLANNING)
            short_term_memory.set_context(
                workflow_id,
                {
                    "task_id": task_id,
                    "file_id": file_id,
                    "user_request": user_request,
                    "workflow_graph": self.workflow_graph(),
                },
            )

            retrieved_context = retrieval_service.retrieve_for_task(user_request or "", user_id)
            short_term_memory.append_event(
                workflow_id,
                {"type": "retrieval", "items": len(retrieved_context)},
            )

            clean_result = self._run_stage(
                db,
                task,
                agent_name="Data",
                tool_name="data.clean_csv",
                payload={"file_id": file_id},
                retrieved_context=retrieved_context,
            )

            analysis = self._run_stage(
                db,
                task,
                agent_name="Analysis",
                tool_name="analysis.profile_dataset",
                payload={
                    "file_id": file_id,
                    "user_request": user_request,
                    "retrieved_context": retrieved_context,
                },
                retrieved_context=retrieved_context,
            )

            charts = self._run_stage(
                db,
                task,
                agent_name="Visualization",
                tool_name="visualization.generate_charts",
                payload={"file_id": file_id},
                retrieved_context=retrieved_context,
            )

            analysis_path = self._persist_analysis(task_id, user_request, analysis, charts, clean_result)

            report_result = self._run_stage(
                db,
                task,
                agent_name="Report",
                tool_name="report.generate_exports",
                payload={
                    "task_id": task_id,
                    "analysis": analysis,
                    "charts": charts,
                    "user_request": user_request,
                },
                retrieved_context=retrieved_context,
            )

            task.result_path = str(analysis_path)
            task.ppt_path = report_result["ppt_path"]
            task.validation_status = "passed"
            task.confidence_score = self._aggregate_confidence(db, task_id)
            task.reasoning_summary = "Workflow completed through data, analysis, visualization, and report stages."
            db.add(task)
            transition_task(db, task, TaskState.COMPLETED)

            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow:
                workflow.status = "completed"
                db.add(workflow)
                db.commit()

            latency = time.perf_counter() - started
            record_task_completion("completed", latency, task_id=task_id)
            publish_event(
                EventType.TASK_COMPLETED,
                task_id=task_id,
                workflow_id=workflow_id,
                payload={"latency_seconds": latency},
            )
            retrieval_service.index_task_summary(
                task_id,
                user_id,
                self._task_memory_summary(user_request, analysis, report_result),
                metadata={"file_id": file_id, "workflow_id": workflow_id},
            )
            return {
                "analysis_path": str(analysis_path),
                "pdf": report_result["report_path"],
                "ppt": report_result["ppt_path"],
            }
        except Exception as exc:
            db.rollback()
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                try:
                    transition_task(db, task, TaskState.FAILED, error_message=str(exc))
                except Exception:
                    task.state = TaskState.FAILED.value
                    task.status = "failed"
                    task.error_message = str(exc)
                    db.add(task)
                    db.commit()
            workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
            if workflow:
                workflow.status = "failed"
                db.add(workflow)
                db.commit()
            latency = time.perf_counter() - started
            record_task_completion("failed", latency, task_id=task_id)
            publish_event(
                EventType.TASK_FAILED,
                task_id=task_id,
                workflow_id=workflow_id,
                payload={"error": str(exc), "latency_seconds": latency},
            )
            log_event(task_id, "Orchestrator", f"Workflow failed: {str(exc)}", "failed")
            raise
        finally:
            db.close()

    def _run_stage(
        self,
        db,
        task: Task,
        agent_name: str,
        tool_name: str,
        payload: Dict[str, Any],
        retrieved_context: Optional[Iterable[Dict[str, Any]]] = None,
    ):
        while True:
            transition_task(db, task, TaskState.WAITING_FOR_TOOL)
            publish_event(
                EventType.TASK_ASSIGNED,
                task_id=task.id,
                workflow_id=task.workflow_id,
                payload={"agent": agent_name, "tool": tool_name},
            )
            log_event(task.id, agent_name, f"Starting {tool_name}.", "running")
            record_agent_state(db, task.id, agent_name, TaskState.EXECUTING)
            transition_task(db, task, TaskState.EXECUTING)

            result = tool_execution_engine.execute(
                tool_name,
                payload,
                user_permissions=self.permissions,
                task_id=task.id,
            )
            record_tool_latency(tool_name, result.latency_ms, task_id=task.id)

            if result.status == "completed":
                transition_task(db, task, TaskState.VALIDATING)
                evaluation = evaluation_engine.evaluate(
                    result.output,
                    agent_name=agent_name,
                    task_id=task.id,
                    retrieved_context=list(retrieved_context or []),
                )
                record_agent_state(
                    db,
                    task.id,
                    agent_name,
                    TaskState.COMPLETED,
                    confidence_score=evaluation["confidence_score"],
                    reasoning_summary=evaluation["reasoning_summary"],
                    validation_status=evaluation["validation_status"],
                )
                if evaluation["validation_status"] != "passed":
                    publish_event(
                        EventType.VALIDATION_FAILED,
                        task_id=task.id,
                        workflow_id=task.workflow_id,
                        payload={"agent": agent_name, "errors": evaluation["errors"]},
                    )
                log_event(
                    task.id,
                    agent_name,
                    f"{agent_name} completed with confidence {evaluation['confidence_score']:.2f}.",
                    "completed",
                )
                short_term_memory.append_event(
                    task.workflow_id,
                    {
                        "type": "stage_completed",
                        "agent": agent_name,
                        "tool": tool_name,
                        "confidence": evaluation["confidence_score"],
                    },
                )
                return result.output

            record_agent_state(db, task.id, agent_name, TaskState.FAILED, validation_status="failed")
            log_event(task.id, agent_name, result.error or f"{tool_name} failed.", "failed")
            if retry_manager.can_retry(task):
                retry_manager.schedule_retry(db, task, result.error or f"{tool_name} failed")
                transition_task(db, task, TaskState.WAITING_FOR_TOOL)
                log_event(task.id, agent_name, f"Retrying {tool_name} (attempt {task.retry_count}).", "running")
                continue
            raise RuntimeError(result.error or f"{tool_name} failed")

    def _persist_analysis(self, task_id, user_request, analysis, charts, clean_result):
        analysis_dir = Path("analysis_results")
        analysis_dir.mkdir(exist_ok=True)
        analysis_path = analysis_dir / f"{task_id}.json"
        with open(analysis_path, "w", encoding="utf-8") as file:
            json.dump(
                {
                    "analysis_request": user_request,
                    "analysis": analysis,
                    "charts": charts,
                    "cleaning": clean_result,
                },
                file,
                indent=2,
            )
        return analysis_path

    def _aggregate_confidence(self, db, task_id: int) -> float:
        from models.schemas import AgentLifecycle

        scores = [
            row.confidence_score
            for row in db.query(AgentLifecycle).filter(AgentLifecycle.task_id == task_id).all()
            if row.confidence_score is not None
        ]
        if not scores:
            return 0.75
        return round(sum(scores) / len(scores), 4)

    def _task_memory_summary(self, user_request, analysis, report_result):
        return " ".join(
            [
                f"Request: {user_request or 'No request supplied.'}",
                f"Summary: {analysis.get('business_summary', '')}",
                f"Rows: {analysis.get('row_count')}. Columns: {analysis.get('column_count')}.",
                f"Exports: {report_result.get('report_path')} and {report_result.get('ppt_path')}.",
            ]
        )

    @staticmethod
    def workflow_graph():
        return {
            "nodes": ["Data", "Analysis", "Visualization", "Report"],
            "edges": [
                ["Data", "Analysis"],
                ["Analysis", "Visualization"],
                ["Visualization", "Report"],
            ],
            "retry_policy": {
                "max_retries": settings.DEFAULT_MAX_RETRIES,
                "timeout_seconds": settings.TASK_TIMEOUT_SECONDS,
            },
        }


orchestration_service = OrchestrationService()
