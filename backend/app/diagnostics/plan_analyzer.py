"""Oracle Execution Plan Generation, Parsing, and Rule-Based Diagnostics.

Executes EXPLAIN PLAN with managed statement identifiers, extracts hierarchical
plan operations via PLAN_TABLE and DBMS_XPLAN, safely deletes temporary plan rows,
and evaluates actionable diagnostic rules.
"""

import uuid
from typing import List, Dict, Any, Optional
import oracledb

from app.core.logging import logger
from app.core.security import validate_read_only_query
from app.core.exceptions import PlanAnalysisError
from app.database.connection import get_oracle_connection, is_oracle_connected
from app.database.mock_provider import mock_db
from app.schemas.plan import PlanOperation, DiagnosticObservation, ExecutionPlanResponse


def evaluate_diagnostic_rules(operations: List[PlanOperation], sql_text: str) -> List[DiagnosticObservation]:
    """
    Evaluate rule-based observations on Oracle execution plan operations.
    Observations are presented as investigation leads, never unquestionable verdicts.
    """
    observations: List[DiagnosticObservation] = []
    sql_upper = sql_text.upper()

    for op in operations:
        # Rule 1: Full Table Scan (FTS)
        if op.operation == "TABLE ACCESS" and op.options and "FULL" in op.options:
            card = op.cardinality or 0
            cost = op.cost or 0
            is_large = card > 500 or cost > 50

            observations.append(DiagnosticObservation(
                id=f"obs_fts_{op.id}",
                category="FULL_TABLE_SCAN",
                severity="INVESTIGATE" if is_large else "INFO",
                title=f"Full Table Scan on '{op.object_name}' (Cost: {cost}, Est Rows: {card})",
                what_observed=f"Oracle cost-based optimizer chose TABLE ACCESS FULL on '{op.object_name}'.",
                where_observed=f"Plan Node {op.id}: {op.operation} {op.options} [{op.object_name}]",
                why_it_matters=(
                    "A full table scan is not inherently bad. For small tables or queries that retrieve a high percentage of rows (>15%), "
                    "multi-block I/O makes full scans more efficient than single-block index lookups. However, if this table is large and "
                    "selective filters exist, an appropriate index might substantially reduce buffer gets."
                ),
                evidence_needed="Examine physical buffer gets, row count of the table, and selectivity of WHERE clause predicates.",
                suggested_step=f"Check if filters on {op.object_name} (e.g. {op.filter_predicates or 'predicates'}) match existing index leading columns.",
                confidence="EVIDENCED"
            ))

        # Rule 2: Index Full Scan vs Index Range Scan
        if op.operation == "INDEX" and op.options and "FULL SCAN" in op.options:
            observations.append(DiagnosticObservation(
                id=f"obs_ifs_{op.id}",
                category="INDEX_FULL_SCAN",
                severity="INVESTIGATE",
                title=f"Index Full Scan on '{op.object_name}'",
                what_observed=f"Optimizer is scanning all leaf blocks of index '{op.object_name}'.",
                where_observed=f"Plan Node {op.id}: INDEX FULL SCAN [{op.object_name}]",
                why_it_matters="An Index Full Scan reads the entire index tree sequentially. This typically happens when the query requires sorted output (avoiding a SORT operation) or retrieves all keys without a selective filter.",
                evidence_needed="Check if an ORDER BY clause is forcing index traversal or if an inequality filter is used.",
                suggested_step="Evaluate if an INDEX RANGE SCAN could be achieved by adding bounded range or equality predicates.",
                confidence="EVIDENCED"
            ))

        # Rule 3: Hash Join on high cardinality
        if op.operation == "HASH JOIN":
            observations.append(DiagnosticObservation(
                id=f"obs_hj_{op.id}",
                category="JOIN_METHOD",
                severity="INFO",
                title="Hash Join Selected by Optimizer",
                what_observed="Oracle optimizer chose HASH JOIN for joining two row sources.",
                where_observed=f"Plan Node {op.id}: HASH JOIN (Est Rows: {op.cardinality}, Cost: {op.cost})",
                why_it_matters="Hash joins build an in-memory hash table of the smaller (build) input and probe it with the larger (probe) input. Hash joins excel for unsorted, large datasets, but consume PGA memory.",
                evidence_needed="Check PGA memory consumption (V$SQL_WORKAREA) and ensure hash table fits in memory without spilling to TEMP.",
                suggested_step="If only a few rows are expected, verify if an index on the join key would allow an efficient NESTED LOOPS join.",
                confidence="HEURISTIC"
            ))

        # Rule 4: Sort or Aggregation spilling risk
        if "SORT" in op.operation:
            observations.append(DiagnosticObservation(
                id=f"obs_sort_{op.id}",
                category="SORT_OPERATION",
                severity="INFO",
                title=f"{op.operation} {op.options or ''} Present",
                what_observed=f"Plan contains explicit sorting operation '{op.operation} {op.options or ''}'.",
                where_observed=f"Plan Node {op.id}: {op.operation} {op.options or ''}",
                why_it_matters="Sort operations require PGA workarea allocation. If the volume of sorted data exceeds pga_aggregate_limit, sort runs spill to the temporary tablespace (TEMP I/O).",
                evidence_needed="Verify if sorting is strictly necessary for the caller, or if a pre-sorted composite index matches the ORDER BY clause.",
                suggested_step="Check if an existing B-tree index on the sorted columns can eliminate the sort operation entirely.",
                confidence="EVIDENCED"
            ))

    # Rule 5: Function on column in predicate (preventing standard index usage)
    fn_matches = ["UPPER(", "LOWER(", "SUBSTR(", "TRUNC(", "TO_CHAR("]
    for fn in fn_matches:
        if fn in sql_upper and "WHERE" in sql_upper:
            observations.append(DiagnosticObservation(
                id=f"obs_fn_{uuid.uuid4().hex[:4]}",
                category="EXPRESSION_PREVENTS_INDEX",
                severity="INVESTIGATE",
                title=f"Function Call '{fn[:-1]}' in SQL Predicate",
                what_observed=f"Detected function '{fn[:-1]}' applied to an expression or column in the query text.",
                where_observed="SQL Query Predicate Clause",
                why_it_matters=(
                    f"Applying a function such as {fn[:-1]} to a column in a WHERE clause prevents Oracle from utilizing standard B-tree indexes "
                    "on that column, forcing the optimizer into a full table scan or full index scan."
                ),
                evidence_needed="Verify whether a function-based index exists on the exact expression (e.g., CREATE INDEX idx ON table(UPPER(col))).",
                suggested_step=f"Either rewrite the query to avoid wrapping the column in {fn[:-1]}, or create an Oracle Function-Based Index.",
                confidence="HYPOTHESIS"
            ))
            break

    return observations


def generate_execution_plan_oracle(sql: str) -> ExecutionPlanResponse:
    """
    Generate an estimated execution plan using Oracle EXPLAIN PLAN FOR and PLAN_TABLE.
    """
    sanitized_sql = validate_read_only_query(sql)
    stmt_id = f"QP_{uuid.uuid4().hex[:12].upper()}"
    conn = get_oracle_connection()
    cursor = conn.cursor()

    try:
        # Step 1: Explain Plan
        explain_sql = f"EXPLAIN PLAN SET STATEMENT_ID = '{stmt_id}' FOR {sanitized_sql}"
        cursor.execute(explain_sql)

        # Step 2: Fetch raw DBMS_XPLAN formatted text
        cursor.execute(f"SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', '{stmt_id}', 'ALL +PREDICATE'))")
        raw_lines = [row[0] for row in cursor.fetchall() if row and row[0] is not None]
        raw_plan_text = "\n".join(raw_lines)

        # Step 3: Fetch structured plan nodes from PLAN_TABLE
        nodes_sql = """
        SELECT id, parent_id, operation, options, object_name, object_type,
               cost, cardinality, bytes, cpu_cost, io_cost, time,
               access_predicates, filter_predicates, depth
        FROM plan_table
        WHERE statement_id = :stmt_id
        ORDER BY id
        """
        cursor.execute(nodes_sql, {"stmt_id": stmt_id})
        raw_ops = cursor.fetchall()

        operations: List[PlanOperation] = []
        optimizer_cost = None

        for row in raw_ops:
            (op_id, parent_id, operation, options, object_name, object_type,
             cost, cardinality, bytes_val, cpu_cost, io_cost, time_val,
             access_pred, filter_pred, depth) = row

            if op_id == 0:
                optimizer_cost = cost

            operations.append(PlanOperation(
                id=op_id,
                parent_id=parent_id,
                operation=operation,
                options=options,
                object_name=object_name,
                object_type=object_type,
                cost=cost,
                cardinality=cardinality,
                bytes=bytes_val,
                cpu_cost=cpu_cost,
                io_cost=io_cost,
                time_sec=time_val,
                access_predicates=access_pred,
                filter_predicates=filter_pred,
                depth=depth or 0
            ))

        # Step 4: Safely delete temporary plan records from PLAN_TABLE
        cursor.execute("DELETE FROM plan_table WHERE statement_id = :stmt_id", {"stmt_id": stmt_id})
        conn.commit()

        # Step 5: Evaluate diagnostic observations
        observations = evaluate_diagnostic_rules(operations, sanitized_sql)

        return ExecutionPlanResponse(
            query_id=f"qry_{uuid.uuid4().hex[:8]}",
            statement_id=stmt_id,
            plan_type="ESTIMATED",
            is_actual=False,
            operations=operations,
            observations=observations,
            raw_plan_text=raw_plan_text,
            optimizer_cost=optimizer_cost,
            limitations_note="ESTIMATED execution plan computed by the Oracle cost-based optimizer via EXPLAIN PLAN without runtime execution.",
            generated_at=datetime.now(timezone.utc)
        )

    except Exception as exc:
        logger.error("Failed to generate Oracle execution plan: %s", exc)
        raise PlanAnalysisError(f"Oracle EXPLAIN PLAN failed: {exc}", details={"error": str(exc)})
    finally:
        cursor.close()
        conn.close()


def generate_execution_plan(sql: str) -> ExecutionPlanResponse:
    """
    Main execution plan dispatcher.
    Uses live Oracle when connected; otherwise uses the offline Retail simulation sandbox.
    """
    if is_oracle_connected():
        return generate_execution_plan_oracle(sql)
    
    # Offline Sandbox fallback
    return mock_db.generate_simulated_plan(sql)
