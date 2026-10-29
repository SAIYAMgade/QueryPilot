"""Execution Plan API Endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.diagnostics.plan_analyzer import generate_execution_plan
from app.schemas.plan import ExecutionPlanResponse

router = APIRouter()


class PlanRequest(BaseModel):
    sql: str = Field(..., description="Query SQL text to explain")


@router.post("/explain", response_model=ExecutionPlanResponse)
def explain_query_plan(req: PlanRequest):
    """
    Generate an Oracle execution plan using EXPLAIN PLAN / PLAN_TABLE / DBMS_XPLAN
    and evaluate rule-based diagnostic observations.
    """
    return generate_execution_plan(req.sql)
