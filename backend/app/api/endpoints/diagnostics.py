"""SQL Error Diagnostics and Curated Knowledge Base API Endpoints."""

from typing import List
from fastapi import APIRouter
from app.schemas.diagnostic import ErrorAnalysisRequest, ErrorAnalysisResponse, KnowledgeBaseEntry
from app.diagnostics.error_analyzer import analyze_oracle_error, KNOWLEDGE_BASE

router = APIRouter()


@router.post("/analyze-error", response_model=ErrorAnalysisResponse)
def analyze_error(req: ErrorAnalysisRequest):
    """Analyze an Oracle SQL runtime error and suggest evidence-backed diagnostic steps."""
    return analyze_oracle_error(
        error_message=req.error_message,
        error_code=req.error_code,
        query_text=req.query_text,
        parameters=req.parameters
    )


@router.get("/knowledge-base", response_model=List[KnowledgeBaseEntry])
def get_knowledge_base():
    """Retrieve all curated Oracle error knowledge base entries."""
    return list(KNOWLEDGE_BASE.values())
