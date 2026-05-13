import os
from pathlib import Path
from fastapi import Header, HTTPException
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from services.ppt_service import generate_ppt

CLEAN_DIR = "cleaned"
CHART_DIR = "charts"
REPORT_DIR = "reports"
BASE_DIR = Path(__file__).resolve().parent.parent

os.makedirs(REPORT_DIR, exist_ok=True)


def generate_report(file_id: str, analysis: dict, charts: list, user_request: str = None):
    report_path = f"{REPORT_DIR}/{file_id}_report.pdf"

    doc = SimpleDocTemplate(report_path)
    styles = getSampleStyleSheet()

    content = []

    # Title
    content.append(Paragraph("AI Analyst Report", styles["Title"]))
    content.append(Spacer(1, 10))

    # Summary
    content.append(Paragraph("Executive Summary", styles["Heading2"]))
    content.append(Spacer(1, 8))

    summary_text = (
        f"Rows analyzed: {analysis.get('row_count')}<br/>"
        f"Columns analyzed: {analysis.get('column_count')}"
    )
    content.append(Paragraph(summary_text, styles["Normal"]))
    content.append(Spacer(1, 12))

    if user_request:
        content.append(Paragraph("Analysis Request", styles["Heading2"]))
        content.append(Spacer(1, 8))
        content.append(Paragraph(user_request, styles["Normal"]))
        content.append(Spacer(1, 12))

    business_summary = analysis.get("business_summary")
    if business_summary:
        content.append(Paragraph("Business Narrative", styles["Heading2"]))
        content.append(Spacer(1, 8))
        content.append(Paragraph(business_summary, styles["Normal"]))
        content.append(Spacer(1, 12))

    request_alignment = analysis.get("request_alignment", {})
    request_insights = request_alignment.get("insights", [])
    if request_insights:
        content.append(Paragraph("Request-Aligned Insights", styles["Heading2"]))
        content.append(Spacer(1, 8))
        for item in request_insights:
            content.append(Paragraph(f"- {item}", styles["Normal"]))
            content.append(Spacer(1, 6))
        content.append(Spacer(1, 6))

    # Numeric Summary
    content.append(Paragraph("Key Metrics", styles["Heading2"]))
    content.append(Spacer(1, 8))

    for col, stats in analysis.get("numeric_summary", {}).items():
        text = (
            f"{col} -> Mean: {stats['mean']:.2f}, Min: {stats['min']:.2f}, "
            f"Max: {stats['max']:.2f}, Median: {stats['median']:.2f}"
        )
        content.append(Paragraph(text, styles["Normal"]))

    content.append(Spacer(1, 12))

    quality = analysis.get("data_quality", {})
    missing = quality.get("missing_by_column", {})
    if missing:
        content.append(Paragraph("Data Quality Notes", styles["Heading2"]))
        content.append(Spacer(1, 8))
        for col, meta in missing.items():
            content.append(
                Paragraph(
                    f"{col} -> Missing: {meta['count']} ({meta['percent']:.2f}%)",
                    styles["Normal"]
                )
            )
        content.append(Spacer(1, 12))

    # Charts
    content.append(Paragraph("Visualizations", styles["Heading2"]))
    content.append(Spacer(1, 10))

    for chart in charts:
        chart_path = chart
        if not os.path.isabs(chart):
            chart_path = os.path.join(BASE_DIR, chart)

        if os.path.exists(chart_path):
            content.append(Image(chart_path, width=400, height=250))
            content.append(Spacer(1, 10))

    doc.build(content)

    ppt_path = generate_ppt(file_id, charts)

    return {
        "report_path": report_path,
        "ppt_path": ppt_path
    }


INTERNAL_API_KEY = "internal-secret"


def verify_internal_key(
    x_internal_key: str = Header(None)
):

    if x_internal_key != INTERNAL_API_KEY:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized"
        )
