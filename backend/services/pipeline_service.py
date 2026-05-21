from orchestration.service import orchestration_service


def run_pipeline(task_id, file_id, user_request=None, user_id=None):
    """Backward-compatible entrypoint for the original threaded pipeline.

    New code should call the orchestration service directly. Keeping this
    function preserves existing imports and tests that expect run_pipeline.
    """

    return orchestration_service.run_analysis_workflow(
        task_id=task_id,
        file_id=file_id,
        user_request=user_request,
        user_id=user_id,
    )

