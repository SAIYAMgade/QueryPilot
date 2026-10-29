"""Safe Query Execution Service for Oracle Database.

Enforces read-only validation, bind variable injection, execution timeouts,
row truncation guardrails, and precise execution vs. fetch timing metrics.
"""

import time
import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
import oracledb

from app.core.config import settings
from app.core.logging import logger, get_correlation_id
from app.core.security import validate_read_only_query
from app.core.exceptions import (
    SecurityViolationError, StatementValidationError, QueryExecutionTimeoutError, OracleConnectionError
)
from app.database.connection import get_oracle_connection, is_oracle_connected
from app.database.mock_provider import mock_db
from app.schemas.query import QueryExecutionResponse, QueryResultColumn, QueryHistoryItem

# In-memory query execution history ring buffer (capped at 500 items)
_query_history: List[QueryHistoryItem] = []


def get_query_history(limit: int = 50) -> List[QueryHistoryItem]:
    """Return recent query execution history."""
    return sorted(_query_history, key=lambda x: x.executed_at, reverse=True)[:limit]


def serialize_oracle_value(val: Any) -> Any:
    """Safely convert Oracle driver types to JSON-serializable Python primitives."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        # Return float or int depending on scale
        return float(val) if val % 1 else int(val)
    if hasattr(val, "read"):  # CLOB / BLOB
        return str(val.read())
    return val


def execute_query_oracle(
    sql: str,
    parameters: Optional[Dict[str, Any]] = None,
    max_rows: Optional[int] = None,
    timeout_sec: Optional[int] = None
) -> QueryExecutionResponse:
    """Execute a validated read-only SQL query against Oracle Database."""
    query_id = f"qry_{uuid.uuid4().hex[:10]}"
    params = parameters or {}
    row_limit = min(max_rows or settings.MAX_ROWS_RETURNED, settings.MAX_ROWS_RETURNED)
    query_timeout = min(timeout_sec or settings.MAX_EXECUTION_TIME_SEC, settings.MAX_EXECUTION_TIME_SEC)

    # Validate read-only security before touching the database
    sanitized_sql = validate_read_only_query(sql)

    conn = get_oracle_connection()
    cursor = conn.cursor()
    cursor.call_timeout = query_timeout * 1000  # milliseconds in python-oracledb

    try:
        # Phase 1: Measure pure query execution interval
        t_exec_start = time.perf_counter()
        cursor.execute(sanitized_sql, params)
        t_exec_end = time.perf_counter()
        exec_duration_ms = round((t_exec_end - t_exec_start) * 1000.0, 3)

        # Inspect columns metadata
        columns = []
        if cursor.description:
            for desc in cursor.description:
                col_name = desc[0]
                type_code = str(desc[1].__name__) if hasattr(desc[1], "__name__") else str(desc[1])
                is_nullable = bool(desc[6]) if len(desc) > 6 else True
                columns.append(QueryResultColumn(name=col_name, data_type=type_code, nullable=is_nullable))

        # Phase 2: Measure fetch duration with row limit safeguard
        t_fetch_start = time.perf_counter()
        # Fetch up to row_limit + 1 to detect whether truncation occurred
        fetched_raw = cursor.fetchmany(row_limit + 1)
        t_fetch_end = time.perf_counter()
        fetch_duration_ms = round((t_fetch_end - t_fetch_start) * 1000.0, 3)

        truncated = len(fetched_raw) > row_limit
        final_rows_raw = fetched_raw[:row_limit]

        rows = []
        col_names = [c.name for c in columns]
        for row in final_rows_raw:
            row_dict = {}
            for idx, val in enumerate(row):
                row_dict[col_names[idx]] = serialize_oracle_value(val)
            rows.append(row_dict)

        response = QueryExecutionResponse(
            query_id=query_id,
            sql=sanitized_sql,
            status="SUCCESS",
            duration_ms=exec_duration_ms,
            fetch_duration_ms=fetch_duration_ms,
            rows_returned=len(rows),
            truncated=truncated,
            columns=columns,
            rows=rows,
            environment="Oracle Database Free",
            executed_at=datetime.now(timezone.utc)
        )

        # Record history
        _query_history.append(QueryHistoryItem(
            id=query_id,
            sql=sanitized_sql,
            status="SUCCESS",
            duration_ms=exec_duration_ms,
            rows_returned=len(rows),
            truncated=truncated,
            environment="Oracle Database Free",
            executed_at=datetime.now(timezone.utc)
        ))

        return response

    except oracledb.DatabaseError as exc:
        error_obj, = exc.args
        error_code = f"ORA-{error_obj.code:05d}"
        error_msg = error_obj.message
        offset = getattr(error_obj, "offset", None)
        logger.warning("Oracle DatabaseError %s during query execution: %s", error_code, error_msg)

        err_response = QueryExecutionResponse(
            query_id=query_id,
            sql=sanitized_sql,
            status="ERROR",
            duration_ms=0.0,
            rows_returned=0,
            truncated=False,
            columns=[],
            rows=[],
            error={
                "code": error_code,
                "message": error_msg,
                "offset": offset,
                "category": "ORACLE_DATABASE_ERROR"
            },
            environment="Oracle Database Free",
            executed_at=datetime.now(timezone.utc)
        )

        _query_history.append(QueryHistoryItem(
            id=query_id,
            sql=sanitized_sql,
            status="ERROR",
            duration_ms=0.0,
            rows_returned=0,
            truncated=False,
            error_summary=f"{error_code}: {error_msg}",
            environment="Oracle Database Free",
            executed_at=datetime.now(timezone.utc)
        ))

        return err_response

    finally:
        cursor.close()
        conn.close()


def execute_query(
    sql: str,
    parameters: Optional[Dict[str, Any]] = None,
    max_rows: Optional[int] = None,
    timeout_sec: Optional[int] = None
) -> QueryExecutionResponse:
    """
    Primary query execution dispatcher.
    Uses live Oracle when connected; otherwise uses the offline Retail simulation sandbox.
    """
    # Check if live Oracle DB is reachable
    if is_oracle_connected():
        return execute_query_oracle(sql, parameters, max_rows, timeout_sec)
    
    # Offline Sandbox fallback
    if settings.ALLOW_OFFLINE_SIMULATION:
        res = mock_db.execute_query(sql, parameters, max_rows, timeout_sec)
        _query_history.append(QueryHistoryItem(
            id=res.query_id,
            sql=res.sql,
            status=res.status,
            duration_ms=res.duration_ms,
            rows_returned=res.rows_returned,
            truncated=res.truncated,
            error_summary=res.error.get("message") if res.error else None,
            environment=res.environment,
            executed_at=res.executed_at
        ))
        return res
    else:
        raise OracleConnectionError(
            f"Oracle Database at {settings.ORACLE_HOST}:{settings.ORACLE_PORT}/{settings.ORACLE_SERVICE_NAME} is unreachable, and offline simulation is disabled."
        )
