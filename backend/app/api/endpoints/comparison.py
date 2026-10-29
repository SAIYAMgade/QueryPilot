"""Query Comparison and Statistical Benchmark API Endpoints."""

from fastapi import APIRouter, HTTPException
from app.schemas.comparison import ComparisonRequest, ComparisonResponse
from app.benchmarking.runner import run_benchmark_comparison

router = APIRouter()


@router.post("/run", response_model=ComparisonResponse)
def compare_queries(req: ComparisonRequest):
    """
    Execute repeatable benchmark comparison between baseline and candidate queries,
    calculate statistical measurements, and verify result equivalence.
    """
    try:
        return run_benchmark_comparison(req)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
