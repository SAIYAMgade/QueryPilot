"""Pydantic models for Oracle Schema Explorer."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool
    data_length: Optional[int] = None
    data_precision: Optional[int] = None
    data_scale: Optional[int] = None
    column_id: Optional[int] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    fk_ref_table: Optional[str] = None
    fk_ref_column: Optional[str] = None
    num_distinct: Optional[int] = None
    density: Optional[float] = None
    histogram: Optional[str] = None


class IndexMetadata(BaseModel):
    index_name: str
    uniqueness: str  # 'UNIQUE' or 'NONUNIQUE'
    columns: List[str]
    status: str
    index_type: Optional[str] = "NORMAL"
    distinct_keys: Optional[int] = None


class ConstraintMetadata(BaseModel):
    constraint_name: str
    constraint_type: str  # 'P' (PK), 'R' (FK), 'U' (Unique), 'C' (Check)
    type_display: str
    search_condition: Optional[str] = None
    r_constraint_name: Optional[str] = None
    r_table_name: Optional[str] = None
    columns: List[str] = Field(default_factory=list)


class TableSummary(BaseModel):
    owner: str
    table_name: str
    num_rows: Optional[int] = None
    is_estimated_rows: bool = True
    column_count: int
    last_analyzed: Optional[datetime] = None


class TableDetail(BaseModel):
    owner: str
    table_name: str
    num_rows: Optional[int] = None
    is_estimated_rows: bool = True
    last_analyzed: Optional[datetime] = None
    columns: List[ColumnMetadata] = Field(default_factory=list)
    indexes: List[IndexMetadata] = Field(default_factory=list)
    constraints: List[ConstraintMetadata] = Field(default_factory=list)
    preview_rows: List[Dict[str, Any]] = Field(default_factory=list)


class Relationship(BaseModel):
    constraint_name: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
