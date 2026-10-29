"""Pydantic models for Oracle Execution Plans and Diagnostic Observations."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PlanOperation(BaseModel):
    id: int
    parent_id: Optional[int] = None
    operation: str
    options: Optional[str] = None
    object_name: Optional[str] = None
    object_type: Optional[str] = None
    cost: Optional[int] = None
    cardinality: Optional[int] = None
    bytes: Optional[int] = None
    cpu_cost: Optional[int] = None
    io_cost: Optional[int] = None
    time_sec: Optional[int] = None
    access_predicates: Optional[str] = None
    filter_predicates: Optional[str] = None
    depth: int = 0
    children: List["PlanOperation"] = Field(default_factory=list)


class DiagnosticObservation(BaseModel):
    id: str
    category: str  # e.g. 'FULL_TABLE_SCAN', 'HIGH_CARDINALITY_JOIN', 'INDEX_USAGE', 'FILTER_SELECTIVITY'
    severity: str  # 'INFO', 'INVESTIGATE', 'WARNING', 'CRITICAL'
    title: str
    what_observed: str
    where_observed: str
    why_it_matters: str
    evidence_needed: str
    suggested_step: str
    confidence: str  # 'EVIDENCED', 'HYPOTHESIS', 'HEURISTIC'


class ExecutionPlanResponse(BaseModel):
    query_id: str
    statement_id: str
    plan_type: str = Field("ESTIMATED", description="'ESTIMATED' (EXPLAIN PLAN) or 'ACTUAL_STATS' (V$SQL_PLAN_STATISTICS)")
    is_actual: bool = False
    operations: List[PlanOperation] = Field(default_factory=list)
    observations: List[DiagnosticObservation] = Field(default_factory=list)
    raw_plan_text: str = Field("", description="Raw DBMS_XPLAN format output")
    optimizer_cost: Optional[int] = None
    limitations_note: str = Field(
        default="This is an ESTIMATED execution plan computed by the Oracle cost-based optimizer without query execution. Runtime cardinality and timings may vary based on bind peeking and system load."
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
