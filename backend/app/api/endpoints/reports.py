"""Technical Report Generation and Export Endpoints."""

import uuid
from fastapi import APIRouter, HTTPException, Response
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.schemas.comparison import ComparisonResponse
from app.investigations.repository import get_investigation_by_id
from app.diagnostics.plan_analyzer import generate_execution_plan
from app.reports.generator import generate_html_report, generate_benchmark_csv

router = APIRouter()


@router.post("/generate", response_model=ReportResponse)
def create_report(req: ReportGenerateRequest):
    """Generate technical investigation report."""
    inv = get_investigation_by_id(req.investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    baseline_plan = None
    if req.include_raw_plan and inv.baseline_sql:
        try:
            baseline_plan = generate_execution_plan(inv.baseline_sql)
        except Exception:
            pass

    html_content = generate_html_report(inv=inv, baseline_plan=baseline_plan)
    report_id = f"rpt_{uuid.uuid4().hex[:8]}"

    return ReportResponse(
        report_id=report_id,
        investigation=inv,
        baseline_plan=baseline_plan,
        html_content=html_content
    )


@router.get("/{investigation_id}/export/html")
def export_html(investigation_id: str):
    """Download technical investigation report as HTML document."""
    inv = get_investigation_by_id(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    baseline_plan = None
    if inv.baseline_sql:
        try:
            baseline_plan = generate_execution_plan(inv.baseline_sql)
        except Exception:
            pass

    html_content = generate_html_report(inv=inv, baseline_plan=baseline_plan)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename=querypilot_report_{investigation_id}.html"}
    )


@router.post("/export/csv")
def export_csv(comparison: ComparisonResponse):
    """Export benchmark run metrics as CSV."""
    csv_content = generate_benchmark_csv(comparison)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=benchmark_{comparison.comparison_id}.csv"}
    )
