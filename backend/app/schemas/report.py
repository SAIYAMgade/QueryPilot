"""Pydantic models for Technical Report Generation."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.investigation import InvestigationResponse
from app.schemas.comparison import ComparisonResponse
from app.schemas.plan import ExecutionPlanResponse


class ReportGenerateRequest(BaseModel):
    investigation_id: str
    include_raw_plan: bool = True
    include_comparison_data: bool = True


class ReportResponse(BaseModel):
    report_id: str
    investigation: InvestigationResponse
    comparison: Optional[ComparisonResponse] = None
    baseline_plan: Optional[ExecutionPlanResponse] = None
    candidate_plan: Optional[ExecutionPlanResponse] = None
    html_content: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
