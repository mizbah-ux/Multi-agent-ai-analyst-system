from agents.data_agent import run_data_cleaning
from agents.analysis_agent import run_analysis
from agents.visualization_agent import run_visualization
from agents.report_agent import generate_report
from services.log_service import log_event
import json
from pathlib import Path

def run_pipeline(task_id, file_id, user_request=None):
    current_stage = None

    def stage_log(agent, message, status):
        log_event(task_id, agent, message, status)

    try:
        current_stage = "Data"
        stage_log("Data", "Starting data cleaning.", "running")
        clean_result = run_data_cleaning(file_id)
        stage_log(
            "Data",
            f"Data cleaned: {clean_result['cleaned_rows']} rows, {len(clean_result['columns'])} columns.",
            "completed"
        )

        current_stage = "Analysis"
        stage_log("Analysis", "Running analytical summary and request-focused insights.", "running")
        analysis = run_analysis(file_id, user_request=user_request)
        stage_log("Analysis", "Analysis completed successfully.", "completed")

        current_stage = "Visualization"
        stage_log("Visualization", "Generating adaptive charts from dataset characteristics.", "running")
        charts = run_visualization(file_id)
        stage_log("Visualization", f"Generated {len(charts)} chart assets.", "completed")

        analysis_dir = Path("analysis_results")
        analysis_dir.mkdir(exist_ok=True)
        analysis_path = analysis_dir / f"{task_id}.json"

        with open(analysis_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "analysis_request": user_request,
                    "analysis": analysis,
                    "charts": charts
                },
                f,
                indent=2
            )

        current_stage = "Report"
        stage_log("Report", "Compiling business report and export artifacts.", "running")
        report_result = generate_report(
            task_id,
            analysis,
            charts,
            user_request=user_request
        )
        stage_log("Report", "PDF and PPT exports generated.", "completed")

        return {
            "analysis_path": str(analysis_path),
            "pdf": report_result["report_path"],
            "ppt": report_result["ppt_path"]
        }
    except Exception as e:
        if current_stage:
            stage_log(current_stage, f"{current_stage} failed: {str(e)}", "failed")
        raise
