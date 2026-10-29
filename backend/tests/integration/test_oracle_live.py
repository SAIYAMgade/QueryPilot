"""Live Oracle Database Integration Tests.

These tests execute queries directly against an active Oracle Database instance
(e.g., Oracle Database 23ai Free or 19c XE).
They are automatically skipped when live Oracle connectivity is not available.
"""

import pytest
from app.database.connection import is_oracle_connected, get_oracle_connection
from app.database.metadata import get_tables_oracle, get_table_detail_oracle
from app.diagnostics.plan_analyzer import generate_execution_plan_oracle
from app.database.executor import execute_query_oracle

ORACLE_AVAILABLE = is_oracle_connected()


@pytest.mark.skipif(not ORACLE_AVAILABLE, reason="Oracle Database instance is unreachable at localhost:1521")
def test_oracle_live_connection():
    """Verify live connectivity and authenticated session creation."""
    conn = get_oracle_connection()
    assert conn is not None
    cur = conn.cursor()
    cur.execute("SELECT banner FROM v$version FETCH FIRST 1 ROWS ONLY")
    row = cur.fetchone()
    assert row is not None
    assert "Oracle" in row[0]
    cur.close()
    conn.close()


@pytest.mark.skipif(not ORACLE_AVAILABLE, reason="Oracle Database instance is unreachable at localhost:1521")
def test_oracle_data_dictionary_inspection():
    """Verify inspection of ALL_TABLES and ALL_TAB_COLUMNS in live Oracle."""
    conn = get_oracle_connection()
    tables = get_tables_oracle(conn)
    assert len(tables) > 0
    conn.close()


@pytest.mark.skipif(not ORACLE_AVAILABLE, reason="Oracle Database instance is unreachable at localhost:1521")
def test_oracle_live_explain_plan():
    """Verify EXPLAIN PLAN FOR execution and PLAN_TABLE extraction in live Oracle."""
    plan = generate_execution_plan_oracle("SELECT customer_id, email FROM customers WHERE status = 'ACTIVE'")
    assert plan.plan_type == "ESTIMATED"
    assert len(plan.operations) > 0
    assert "TABLE ACCESS" in [op.operation for op in plan.operations]


@pytest.mark.skipif(not ORACLE_AVAILABLE, reason="Oracle Database instance is unreachable at localhost:1521")
def test_oracle_live_query_execution_and_types():
    """Verify execution of read-only query and data type serialization in live Oracle."""
    res = execute_query_oracle("SELECT customer_id, first_name, created_at FROM customers FETCH FIRST 5 ROWS ONLY")
    assert res.status == "SUCCESS"
    assert len(res.rows) <= 5
    assert res.duration_ms > 0
