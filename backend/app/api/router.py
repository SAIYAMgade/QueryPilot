"""Main API router aggregating all QueryPilot endpoint routers."""

from fastapi import APIRouter
from app.api.endpoints import (
    health, query, schema, plan, comparison, diagnostics, investigations, reports
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Connection"])
api_router.include_router(query.router, prefix="/query", tags=["SQL Workspace"])
api_router.include_router(schema.router, prefix="/schema", tags=["Schema Explorer"])
api_router.include_router(plan.router, prefix="/plan", tags=["Execution Plans"])
api_router.include_router(comparison.router, prefix="/comparison", tags=["Comparison Lab"])
api_router.include_router(diagnostics.router, prefix="/diagnostics", tags=["Error Diagnostics"])
api_router.include_router(investigations.router, prefix="/investigations", tags=["Investigations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
