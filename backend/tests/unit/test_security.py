"""Unit tests for SQL Security Guardrails and Read-Only Validation."""

import pytest
from app.core.security import validate_read_only_query
from app.core.exceptions import SecurityViolationError, StatementValidationError


def test_valid_select_queries():
    assert "SELECT 1 FROM DUAL" in validate_read_only_query("SELECT 1 FROM DUAL")
    assert "SELECT * FROM customers WHERE status = 'ACTIVE'" in validate_read_only_query(
        "SELECT * FROM customers WHERE status = 'ACTIVE';"
    )
    # Common Table Expression (WITH)
    cte_sql = "WITH high_orders AS (SELECT * FROM orders WHERE total_amount > 500) SELECT * FROM high_orders"
    assert "WITH" in validate_read_only_query(cte_sql)


def test_comments_handling():
    # Query with leading single-line comment
    sql_with_comment = "-- Get all products\nSELECT product_id, sku FROM products"
    res = validate_read_only_query(sql_with_comment)
    assert "SELECT product_id, sku FROM products" in res

    # Query with multiline comment
    sql_multiline = "/* Important report */ SELECT order_id FROM orders"
    res = validate_read_only_query(sql_multiline)
    assert "SELECT order_id FROM orders" in res


def test_reject_dml_statements():
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("INSERT INTO customers (customer_id, first_name) VALUES (1, 'Eve')")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("UPDATE customers SET status = 'INACTIVE' WHERE customer_id = 5")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("DELETE FROM orders WHERE order_id = 10")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("MERGE INTO products p USING (SELECT 1 FROM dual) s ON (p.product_id = 1) WHEN MATCHED THEN UPDATE SET p.status = 'ACTIVE'")


def test_reject_ddl_statements():
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("DROP TABLE customers")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("TRUNCATE TABLE orders")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("CREATE TABLE hack (id INT)")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("ALTER TABLE customers ADD (credit_card VARCHAR2(20))")


def test_reject_multi_statements():
    # Semicolon separating statements
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("SELECT * FROM customers; DROP TABLE orders;")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("SELECT 1 FROM dual; SELECT 2 FROM dual")


def test_reject_plsql_blocks():
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("BEGIN DBMS_OUTPUT.PUT_LINE('hack'); END;")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("DECLARE x NUMBER; BEGIN x := 1; END;")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("CALL some_proc()")


def test_reject_for_update_locks():
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("SELECT * FROM orders WHERE status = 'PENDING' FOR UPDATE")


def test_reject_dangerous_oracle_packages():
    with pytest.raises(SecurityViolationError):
        validate_read_only_query("SELECT UTL_FILE.FOPEN('DIR', 'test.txt', 'R') FROM dual")

    with pytest.raises(SecurityViolationError):
        validate_read_only_query("SELECT UTL_HTTP.REQUEST('http://attacker.com') FROM dual")


def test_reject_empty_query():
    with pytest.raises(StatementValidationError):
        validate_read_only_query("")

    with pytest.raises(StatementValidationError):
        validate_read_only_query("   \n  ")
