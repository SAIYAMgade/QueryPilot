"""Pydantic models for Oracle SQL Error Diagnostics and Knowledge Base."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorAnalysisRequest(BaseModel):
    error_code: Optional[str] = None  # e.g. "ORA-00942"
    error_message: str
    query_text: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class KnowledgeBaseEntry(BaseModel):
    oracle_code: str
    category: str
    official_title: str
    plain_english: str
    common_scenarios: List[str]
    root_cause_analysis: str
    recommended_checks: List[str]
    resolution_steps: List[str]
    sample_problematic_sql: Optional[str] = None
    sample_corrected_sql: Optional[str] = None


class ErrorAnalysisResponse(BaseModel):
    analysis_id: str
    oracle_error_code: str
    category: str  # 'SYNTAX', 'OBJECT_NOT_FOUND', 'CONSTRAINT_VIOLATION', 'TYPE_CONVERSION', etc.
    sanitized_message: str
    likely_causes: List[str]
    recommended_checks: List[str]
    knowledge_base: Optional[KnowledgeBaseEntry] = None
    position_hint: Optional[str] = None
    is_confirmed_cause: bool = False
    evidence_status: str  # 'CONFIRMED' or 'HYPOTHESIS'
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
