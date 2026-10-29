"""Technical Report Generation Service for QueryPilot Investigations.

Generates self-contained HTML reports and CSV exports with full audit trails,
baseline vs candidate comparisons, execution plans, and documented root causes.
"""

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.schemas.investigation import InvestigationResponse
from app.schemas.comparison import ComparisonResponse
from app.schemas.plan import ExecutionPlanResponse
from app.schemas.report import ReportResponse


def generate_html_report(
    inv: InvestigationResponse,
    comparison: Optional[ComparisonResponse] = None,
    baseline_plan: Optional[ExecutionPlanResponse] = None,
    candidate_plan: Optional[ExecutionPlanResponse] = None
) -> str:
    """Generate professional, self-contained HTML technical report."""
    comp_html = ""
    if comparison:
        comp_html = f"""
        <div class="card">
            <h2>Performance Benchmark & Result Equivalence</h2>
            <div class="metric-grid">
                <div class="metric-box">
                    <span class="metric-label">Equivalence Status</span>
                    <span class="metric-val status-{comparison.equivalence.status.lower()}">{comparison.equivalence.status}</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Baseline Median Latency</span>
                    <span class="metric-val">{comparison.baseline_stats.median_ms} ms</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Candidate Median Latency</span>
                    <span class="metric-val">{comparison.candidate_stats.median_ms} ms</span>
                </div>
                <div class="metric-box">
                    <span class="metric-label">Speedup Factor</span>
                    <span class="metric-val highlight">{comparison.speedup_ratio or 'N/A'}x</span>
                </div>
            </div>
            <p><strong>Equivalence Note:</strong> {comparison.equivalence.reason}</p>
            <p><strong>Measurement Summary:</strong> {comparison.improvement_summary}</p>
            <p class="caveat"><em>Caveat:</em> {comparison.caveat}</p>
        </div>
        """

    timeline_html = "".join(
        f"<li><strong>{evt.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</strong> [{evt.event_type}]: {evt.description}</li>"
        for evt in inv.timeline
    )

    baseline_plan_html = ""
    if baseline_plan and baseline_plan.raw_plan_text:
        baseline_plan_html = f"""
        <div class="card">
            <h2>Baseline Oracle Execution Plan</h2>
            <pre class="plan-box">{baseline_plan.raw_plan_text}</pre>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>QueryPilot Technical Investigation Report: {inv.id}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 32px; }}
    .container {{ max-width: 960px; margin: 0 auto; }}
    .header {{ border-bottom: 2px solid #334155; padding-bottom: 16px; margin-bottom: 24px; }}
    h1 {{ margin: 0 0 8px 0; font-size: 24px; color: #38bdf8; }}
    .meta-bar {{ font-size: 13px; color: #94a3b8; display: flex; gap: 24px; }}
    .badge {{ padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase; }}
    .status-resolved {{ background: #065f46; color: #34d399; }}
    .status-investigating {{ background: #1e3a8a; color: #60a5fa; }}
    .status-open {{ background: #854d0e; color: #facc15; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
    h2 {{ margin-top: 0; font-size: 16px; color: #e2e8f0; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
    pre {{ background: #090d16; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; color: #38bdf8; font-family: ui-monospace, Menlo, monospace; }}
    .plan-box {{ font-size: 11px; color: #cbd5e1; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }}
    .metric-box {{ background: #0f172a; padding: 12px; border-radius: 6px; border: 1px solid #334155; text-align: center; }}
    .metric-label {{ font-size: 11px; color: #94a3b8; display: block; }}
    .metric-val {{ font-size: 18px; font-weight: bold; color: #f8fafc; margin-top: 4px; display: block; }}
    .highlight {{ color: #34d399; }}
    .caveat {{ font-size: 12px; color: #94a3b8; border-left: 3px solid #f59e0b; padding-left: 10px; }}
    ul.timeline {{ list-style: none; padding-left: 0; }}
    ul.timeline li {{ padding: 6px 0; border-bottom: 1px solid #293548; font-size: 13px; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>{inv.title}</h1>
        <div class="meta-bar">
            <span><strong>Case ID:</strong> {inv.id}</span>
            <span><strong>Category:</strong> {inv.category}</span>
            <span><strong>Status:</strong> <span class="badge status-{inv.status.value.lower()}">{inv.status.value}</span></span>
            <span><strong>Generated:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</span>
        </div>
    </div>

    <div class="card">
        <h2>Problem Statement & Initial Hypothesis</h2>
        <p>{inv.description}</p>
        <p><strong>Initial Hypothesis:</strong> {inv.initial_hypothesis or 'None recorded'}</p>
    </div>

    <div class="card">
        <h2>SQL Statements Under Investigation</h2>
        <p><strong>Baseline Query:</strong></p>
        <pre>{inv.baseline_sql or '-- No baseline SQL recorded'}</pre>
        {f"<p><strong>Candidate Query:</strong></p><pre>{inv.candidate_sql}</pre>" if inv.candidate_sql else ""}
    </div>

    {comp_html}
    {baseline_plan_html}

    <div class="card">
        <h2>Findings, Root Cause & Resolution</h2>
        <p><strong>Root Cause Analysis:</strong> {inv.root_cause_explanation or 'Pending investigation completion'}</p>
        <p><strong>Proposed or Implemented Fix:</strong> {inv.proposed_fix or 'None specified'}</p>
        <p><strong>Verification Evidence:</strong> {inv.verification_notes or 'Pending verification testing'}</p>
    </div>

    <div class="card">
        <h2>Investigation Timeline Audit</h2>
        <ul class="timeline">
            {timeline_html}
        </ul>
    </div>
</div>
</body>
</html>"""


def generate_benchmark_csv(comparison: ComparisonResponse) -> str:
    """Generate RFC 4180 CSV export of repeated benchmark runs."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Run_Index", "Baseline_Duration_ms", "Candidate_Duration_ms", "Baseline_Rows", "Candidate_Rows"])
    for run in comparison.runs_data:
        writer.writerow([run.run_index, run.baseline_duration_ms, run.candidate_duration_ms, run.baseline_rows, run.candidate_rows])
    return output.getvalue()
