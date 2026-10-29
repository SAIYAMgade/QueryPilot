"""Schema Explorer API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
import oracledb

from app.database.connection import get_oracle_connection, is_oracle_connected
from app.database.metadata import get_tables_oracle, get_table_detail_oracle, get_relationships_oracle
from app.database.mock_provider import mock_db
from app.schemas.schema_explorer import TableSummary, TableDetail, Relationship

router = APIRouter()


@router.get("/tables", response_model=List[TableSummary])
def list_tables(owner: Optional[str] = None):
    """List accessible tables and column counts."""
    if is_oracle_connected():
        try:
            conn = get_oracle_connection()
            try:
                return get_tables_oracle(conn, owner_filter=owner)
            finally:
                conn.close()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to query Oracle data dictionary: {exc}")
    
    return mock_db.get_tables()


@router.get("/table/{table_name}", response_model=TableDetail)
def get_table_details(table_name: str, owner: Optional[str] = None):
    """Retrieve column specifications, constraints, indexes, and preview rows for a table."""
    if is_oracle_connected():
        try:
            conn = get_oracle_connection()
            try:
                return get_table_detail_oracle(conn, table_name, owner=owner)
            finally:
                conn.close()
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Table metadata retrieval failed: {exc}")

    try:
        return mock_db.get_table_detail(table_name)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")


@router.get("/relationships", response_model=List[Relationship])
def list_relationships(owner: Optional[str] = None):
    """Retrieve foreign key relationship graph."""
    if is_oracle_connected():
        try:
            conn = get_oracle_connection()
            try:
                return get_relationships_oracle(conn, owner=owner)
            finally:
                conn.close()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Failed to query Oracle foreign keys: {exc}")

    return mock_db.get_relationships()
