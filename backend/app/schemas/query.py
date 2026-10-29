"""Pydantic models for Query Workspace execution, history, and saved queries."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class QueryExecuteRequest(BaseModel):
    sql: str = Field(..., description="Read-only SQL query to execute")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Bind variables (name -> value)")
    max_rows: Optional[int] = Field(default=None, description="Max rows to fetch (capped by system limit)")
    timeout_sec: Optional[int] = Field(default=None, description="Query timeout limit in seconds")


class QueryResultColumn(BaseModel):
    name: str
    data_type: str
    nullable: Optional[bool] = True


class QueryExecutionResponse(BaseModel):
    query_id: str
    sql: str
    status: str = Field(..., description="'SUCCESS' or 'ERROR'")
    duration_ms: float = Field(..., description="Measured query database execution interval in milliseconds")
    fetch_duration_ms: Optional[float] = Field(None, description="Time spent fetching records from driver")
    rows_returned: int
    truncated: bool = Field(False, description="True if output was cut off by max_rows limit")
    columns: List[QueryResultColumn] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[Dict[str, Any]] = None
    environment: str = Field(..., description="e.g. 'Oracle Database 23ai Free' or 'Offline Sandbox'")
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class SavedQueryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = ""
    sql: str = Field(..., min_length=1)
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    investigation_id: Optional[str] = None


class SavedQueryUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    sql: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    investigation_id: Optional[str] = None


class SavedQueryResponse(BaseModel):
    id: str
    title: str
    description: str
    sql: str
    parameters: Dict[str, Any]
    tags: List[str]
    investigation_id: Optional[str]
    created_at: datetime
    updated_at: datetime


class QueryHistoryItem(BaseModel):
    id: str
    sql: str
    status: str
    duration_ms: float
    rows_returned: int
    truncated: bool
    error_summary: Optional[str] = None
    environment: str
    executed_at: datetime
