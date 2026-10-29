"""API integration tests for QueryPilot FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "QueryPilot API"


def test_connection_status_endpoint():
    res = client.get("/api/connection/status")
    assert res.status_code == 200
    data = res.json()
    assert "is_connected" in data
    assert "driver" in data
    assert "environment" in data


def test_query_execute_valid_select():
    payload = {
        "sql": "SELECT customer_id, first_name, email FROM customers FETCH FIRST 5 ROWS ONLY",
        "parameters": {}
    }
    res = client.post("/api/query/execute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert len(data["rows"]) <= 5
    assert "duration_ms" in data
    assert data["rows_returned"] > 0


def test_query_execute_rejected_dml():
    payload = {
        "sql": "DELETE FROM customers WHERE customer_id = 1",
        "parameters": {}
    }
    res = client.post("/api/query/execute", json=payload)
    assert res.status_code == 403
    data = res.json()
    assert data["error_type"] == "SECURITY_VIOLATION"


def test_schema_tables_endpoint():
    res = client.get("/api/schema/tables")
    assert res.status_code == 200
    tables = res.json()
    assert len(tables) > 0
    table_names = [t["table_name"] for t in tables]
    assert "CUSTOMERS" in table_names
    assert "ORDERS" in table_names


def test_schema_table_detail_endpoint():
    res = client.get("/api/schema/table/CUSTOMERS")
    assert res.status_code == 200
    data = res.json()
    assert data["table_name"] == "CUSTOMERS"
    assert len(data["columns"]) > 0
    assert len(data["preview_rows"]) > 0


def test_plan_explain_endpoint():
    payload = {
        "sql": "SELECT * FROM orders WHERE status = 'COMPLETED'"
    }
    res = client.post("/api/plan/explain", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["plan_type"] == "ESTIMATED"
    assert len(data["operations"]) > 0
    assert "raw_plan_text" in data


def test_comparison_endpoint():
    payload = {
        "baseline": {
            "sql": "SELECT order_id, total_amount FROM orders WHERE status = 'COMPLETED' FETCH FIRST 10 ROWS ONLY",
            "label": "Baseline"
        },
        "candidate": {
            "sql": "SELECT order_id, total_amount FROM orders WHERE status = 'COMPLETED' FETCH FIRST 10 ROWS ONLY",
            "label": "Candidate"
        },
        "warmup_runs": 1,
        "measured_runs": 2,
        "compare_equivalence": True
    }
    res = client.post("/api/comparison/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["equivalence"]["is_equivalent"] is True
    assert "baseline_stats" in data
    assert "candidate_stats" in data
    assert len(data["runs_data"]) == 2


def test_diagnostics_analyze_endpoint():
    payload = {
        "error_code": "ORA-00942",
        "error_message": "ORA-00942: table or view does not exist",
        "query_text": "SELECT * FROM nonexistent_tbl"
    }
    res = client.post("/api/diagnostics/analyze-error", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["oracle_error_code"] == "ORA-00942"
    assert data["category"] == "OBJECT_NOT_FOUND_OR_INACCESSIBLE"


def test_investigations_lifecycle_api():
    # 1. Create
    create_payload = {
        "title": "API Test Investigation",
        "description": "Lifecycle testing via API",
        "category": "PERFORMANCE"
    }
    c_res = client.post("/api/investigations", json=create_payload)
    assert c_res.status_code == 200
    inv = c_res.json()
    inv_id = inv["id"]

    # 2. Update without resolution evidence should fail if status=RESOLVED
    bad_patch = client.patch(f"/api/investigations/{inv_id}", json={"status": "RESOLVED"})
    assert bad_patch.status_code == 400

    # 3. Update with valid resolution evidence
    good_patch = client.patch(f"/api/investigations/{inv_id}", json={
        "status": "RESOLVED",
        "root_cause_explanation": "Identified table scan caused by unindexed column.",
        "proposed_fix": "Add B-tree index.",
        "verification_notes": "Benchmark confirmed 4x speedup across 5 runs."
    })
    assert good_patch.status_code == 200
    assert good_patch.json()["status"] == "RESOLVED"

    # 4. Generate report
    rep_res = client.post("/api/reports/generate", json={"investigation_id": inv_id})
    assert rep_res.status_code == 200
    assert "html_content" in rep_res.json()
