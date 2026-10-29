"""Unit tests for Oracle Error Diagnostics and Plan Analyzer Rules."""

from app.diagnostics.error_analyzer import analyze_oracle_error
from app.diagnostics.plan_analyzer import evaluate_diagnostic_rules
from app.schemas.plan import PlanOperation


def test_diagnose_ora_00942_table_not_found():
    res = analyze_oracle_error("ORA-00942: table or view does not exist", error_code="ORA-00942")
    assert res.oracle_error_code == "ORA-00942"
    assert res.category == "OBJECT_NOT_FOUND_OR_INACCESSIBLE"
    assert res.is_confirmed_cause is True
    assert res.knowledge_base is not None
    assert "user_tables" in res.knowledge_base.recommended_checks[0].lower()


def test_diagnose_ora_00933_syntax_with_limit_hint():
    sql = "SELECT * FROM orders LIMIT 10"
    res = analyze_oracle_error("ORA-00933: SQL command not properly ended", query_text=sql)
    assert res.oracle_error_code == "ORA-00933"
    assert res.category == "SYNTAX_ERROR"
    assert res.position_hint is not None
    assert "FETCH FIRST" in res.position_hint


def test_diagnose_unknown_oracle_code():
    res = analyze_oracle_error("ORA-60000: unexpected internal condition")
    assert res.category == "UNKNOWN_ORACLE_ERROR"
    assert res.evidence_status == "HYPOTHESIS"
    assert res.is_confirmed_cause is False


def test_plan_diagnostic_rule_fts_not_always_critical():
    # Small cardinality FTS is INFO, not CRITICAL
    ops = [
        PlanOperation(id=1, parent_id=0, operation="TABLE ACCESS", options="FULL", object_name="CATEGORIES", cardinality=8, cost=3)
    ]
    obs = evaluate_diagnostic_rules(ops, "SELECT * FROM categories")
    assert len(obs) == 1
    assert obs[0].category == "FULL_TABLE_SCAN"
    assert obs[0].severity == "INFO"
    assert "multi-block I/O" in obs[0].why_it_matters


def test_plan_diagnostic_rule_function_on_column():
    ops = [
        PlanOperation(id=1, parent_id=0, operation="TABLE ACCESS", options="FULL", object_name="CUSTOMERS", cardinality=1000, cost=25)
    ]
    obs = evaluate_diagnostic_rules(ops, "SELECT * FROM customers WHERE UPPER(email) = 'TEST@EXAMPLE.COM'")
    categories = [o.category for o in obs]
    assert "EXPRESSION_PREVENTS_INDEX" in categories
