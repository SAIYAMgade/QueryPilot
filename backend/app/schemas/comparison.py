"""Pydantic models for Query Comparison Lab and Performance Benchmarking."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QueryVariant(BaseModel):
    sql: str = Field(..., description="Query SQL text")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Bind variables")
    label: Optional[str] = "Query"


class EquivalenceResult(BaseModel):
    is_equivalent: bool
    status: str  # 'EQUIVALENT', 'DIFFERENT', 'INCONCLUSIVE'
    reason: str
    row_count_baseline: int
    row_count_candidate: int
    column_match: bool
    columns_baseline: List[str]
    columns_candidate: List[str]
    diff_summary: Optional[str] = None
    sample_discrepancy: Optional[Dict[str, Any]] = None


class RunMeasurement(BaseModel):
    run_index: int
    baseline_duration_ms: float
    candidate_duration_ms: float
    baseline_rows: int
    candidate_rows: int


class VariantStatistics(BaseModel):
    label: str
    runs: int
    median_ms: float
    min_ms: float
    max_ms: float
    iqr_ms: float
    successful_runs: int
    failed_runs: int
    rows: int
    optimizer_cost: Optional[int] = None


class ComparisonRequest(BaseModel):
    baseline: QueryVariant
    candidate: QueryVariant
    warmup_runs: int = Field(default=1, ge=0, le=5)
    measured_runs: int = Field(default=3, ge=1, le=10)
    compare_equivalence: bool = True
    hypothesis: Optional[str] = None


class ComparisonResponse(BaseModel):
    comparison_id: str
    hypothesis: Optional[str] = None
    equivalence: EquivalenceResult
    baseline_stats: VariantStatistics
    candidate_stats: VariantStatistics
    runs_data: List[RunMeasurement] = Field(default_factory=list)
    speedup_ratio: Optional[float] = None
    improvement_summary: str
    caveat: str
    environment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
