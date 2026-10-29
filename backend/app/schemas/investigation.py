"""Pydantic models for Query Investigation Cases, Timelines, and Evidence."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    FIX_PROPOSED = "FIX_PROPOSED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    RESOLVED = "RESOLVED"
    CLOSED_INCONCLUSIVE = "CLOSED_INCONCLUSIVE"


class InvestigationSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TimelineEvent(BaseModel):
    event_id: str
    event_type: str  # 'CREATED', 'QUERY_EXECUTED', 'ERROR_CAPTURED', 'PLAN_GENERATED', 'COMPARISON_RUN', 'STATUS_CHANGE'
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InvestigationCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field("", max_length=2000)
    category: str = Field("PERFORMANCE", description="PERFORMANCE, ERROR, DATA_CORRECTNESS, or INDEX_EVALUATION")
    severity: InvestigationSeverity = InvestigationSeverity.MEDIUM
    initial_hypothesis: Optional[str] = None
    baseline_query_id: Optional[str] = None
    baseline_sql: Optional[str] = None
    related_error_code: Optional[str] = None


class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[InvestigationSeverity] = None
    status: Optional[InvestigationStatus] = None
    initial_hypothesis: Optional[str] = None
    root_cause_explanation: Optional[str] = None
    proposed_fix: Optional[str] = None
    verification_notes: Optional[str] = None
    candidate_sql: Optional[str] = None
    resolution_evidence: Optional[Dict[str, Any]] = None


class InvestigationResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    severity: InvestigationSeverity
    status: InvestigationStatus
    initial_hypothesis: Optional[str] = None
    baseline_query_id: Optional[str] = None
    baseline_sql: Optional[str] = None
    candidate_sql: Optional[str] = None
    related_error_code: Optional[str] = None
    root_cause_explanation: Optional[str] = None
    proposed_fix: Optional[str] = None
    verification_notes: Optional[str] = None
    timeline: List[TimelineEvent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
