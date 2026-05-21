from agents.analysis_agent import run_analysis
from agents.data_agent import run_data_cleaning
from agents.report_agent import generate_report
from agents.visualization_agent import run_visualization
from memory.retrieval_service import retrieval_service
from tools.registry import tool_registry
from tools.schemas import ToolMetadata


def _register_once(metadata: ToolMetadata, handler):
    if not tool_registry.get(metadata.tool_name):
        tool_registry.register(metadata, handler)


def register_builtin_tools():
    _register_once(
        ToolMetadata(
            tool_name="data.clean_csv",
            description="Clean uploaded tabular datasets and persist a normalized CSV.",
            capability_type="data_preprocessing",
            permissions=["tool:data"],
            input_schema={
                "type": "object",
                "required": ["file_id"],
                "properties": {"file_id": {"type": "string"}},
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "required": ["file_id", "cleaned_rows", "columns", "cleaned_file_path"],
                "properties": {
                    "file_id": {"type": "string"},
                    "original_rows": {"type": "number"},
                    "cleaned_rows": {"type": "number"},
                    "columns": {"type": "array"},
                    "cleaned_file_path": {"type": "string"},
                },
            },
        ),
        lambda payload: run_data_cleaning(payload["file_id"]),
    )

    _register_once(
        ToolMetadata(
            tool_name="analysis.profile_dataset",
            description="Generate descriptive statistics, quality checks, and request-aligned insights.",
            capability_type="analysis",
            permissions=["tool:analysis"],
            input_schema={
                "type": "object",
                "required": ["file_id"],
                "properties": {
                    "file_id": {"type": "string"},
                    "user_request": {"type": ["string", "null"]},
                    "retrieved_context": {"type": "array"},
                },
                "additionalProperties": False,
            },
            output_schema={"type": "object"},
        ),
        lambda payload: run_analysis(payload["file_id"], user_request=payload.get("user_request")),
    )

    _register_once(
        ToolMetadata(
            tool_name="visualization.generate_charts",
            description="Create adaptive chart assets for cleaned datasets.",
            capability_type="visualization",
            permissions=["tool:visualization"],
            input_schema={
                "type": "object",
                "required": ["file_id"],
                "properties": {"file_id": {"type": "string"}},
                "additionalProperties": False,
            },
            output_schema={"type": "array"},
        ),
        lambda payload: run_visualization(payload["file_id"]),
    )

    _register_once(
        ToolMetadata(
            tool_name="report.generate_exports",
            description="Compile PDF and PPT report exports from analysis and chart outputs.",
            capability_type="reporting",
            permissions=["tool:reporting"],
            input_schema={
                "type": "object",
                "required": ["task_id", "analysis", "charts"],
                "properties": {
                    "task_id": {"type": "integer"},
                    "analysis": {"type": "object"},
                    "charts": {"type": "array"},
                    "user_request": {"type": ["string", "null"]},
                },
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "required": ["report_path", "ppt_path"],
                "properties": {
                    "report_path": {"type": "string"},
                    "ppt_path": {"type": "string"},
                },
            },
        ),
        lambda payload: generate_report(
            payload["task_id"],
            payload["analysis"],
            payload["charts"],
            user_request=payload.get("user_request"),
        ),
    )

    _register_once(
        ToolMetadata(
            tool_name="memory.semantic_search",
            description="Retrieve semantically similar task history, documents, and execution outputs.",
            capability_type="retrieval",
            permissions=["tool:retrieval"],
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "namespace": {"type": ["string", "null"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
                "additionalProperties": False,
            },
            output_schema={"type": "array"},
        ),
        lambda payload: retrieval_service.search(
            payload["query"],
            namespace=payload.get("namespace"),
            limit=payload.get("limit", 5),
        ),
    )


register_builtin_tools()

