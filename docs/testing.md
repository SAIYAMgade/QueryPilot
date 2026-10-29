# QueryPilot Testing Strategy

Testing is a core architectural pillar of QueryPilot. The project implements a multi-tier test suite covering security guardrails, result equivalence algorithms, error categorization, API contracts, and live database integration.

---

## 1. Test Suite Structure

```
backend/tests/
  ├── unit/
  │   ├── test_security.py       # Validates read-only AST safety, DML/DDL rejection, comment smuggling
  │   ├── test_comparator.py     # Validates multiset equivalence, unordered sets, float precision
  │   ├── test_diagnostics.py    # Tests ORA- error categorizations & plan diagnostic rules
  │   └── test_investigations.py # Tests investigation state machine & resolution criteria gating
  ├── api/
  │   └── test_api_endpoints.py  # Tests FastAPI endpoints with TestClient (health, query, schema, reports)
  └── integration/
      └── test_oracle_live.py    # Conditional tests running against live Oracle Database
```

---

## 2. Running Tests

### Run all Unit and API Tests
```bash
python -m pytest backend/tests -v
```

### Run Live Oracle Integration Tests
Live tests connect to Oracle at `localhost:1521/FREEPDB1`. They automatically execute when Oracle is reachable and skip cleanly with a diagnostic reason when offline:
```bash
python -m pytest backend/tests/integration/test_oracle_live.py -v
```

---

## 3. Security Tests Coverage

The test suite validates defense-in-depth security:
- **DML Rejection**: `INSERT`, `UPDATE`, `DELETE`, `MERGE` raise `SecurityViolationError` (HTTP 403).
- **DDL Rejection**: `DROP`, `TRUNCATE`, `CREATE`, `ALTER` raise `SecurityViolationError`.
- **Comment Smuggling**: Validates that leading/multiline comments (`--`, `/* */`) do not hide malicious statements.
- **Multi-Statement Payloads**: Semicolon-delimited queries are rejected.
- **PL/SQL Blocks**: `BEGIN ... END;`, `DECLARE ...`, `EXECUTE` are rejected.
- **Row-Locking Constructs**: `SELECT ... FOR UPDATE` is blocked.
- **Dangerous System Packages**: Calls to `UTL_FILE`, `UTL_HTTP`, `DBMS_SCHEDULER` are blocked.
