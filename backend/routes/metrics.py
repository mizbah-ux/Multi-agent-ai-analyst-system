from fastapi import APIRouter, Response

from observability.metrics import metrics_payload

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
def prometheus_metrics():
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)

