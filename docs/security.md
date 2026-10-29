# QueryPilot Security & Guardrails

Query execution is a sensitive capability. QueryPilot implements defense-in-depth safeguards across both application and database layers.

---

## 1. Defense-in-Depth Model

```
[ Client Request ]
       |
       v
[ Step 1: Pre-Execution AST Validation ]
  - Strips leading & multiline comments
  - Enforces single-statement structure (rejects semicolons)
  - Validates leading token is SELECT or WITH
  - Scans for disallowed keywords (DML, DDL, DCL, TCL, PL/SQL)
  - Rejects FOR UPDATE locking clauses
  - Rejects dangerous system packages (UTL_FILE, UTL_HTTP, DBMS_SCHEDULER)
       |
       v
[ Step 2: Application Execution Safeguards ]
  - Query timeout capped via cursor.call_timeout (30s)
  - Row fetching capped at MAX_ROWS_RETURNED (1,000 rows)
  - Safe parameter binding (:param) instead of string interpolation
       |
       v
[ Step 3: Database Least-Privilege Account ]
  - Dedicated user: QP_APP_USER
  - GRANTED ONLY: CREATE SESSION, SELECT ON retail tables
  - REVOKED: CREATE TABLE, DROP, ALTER, INSERT, UPDATE, DELETE, EXECUTE ON SYS
  - NEVER CONNECTS AS SYSDBA
```

---

## 2. Blocked SQL Operations

| Category | Disallowed Tokens / Constructs | Security Rationale |
| :--- | :--- | :--- |
| **DML** | `INSERT`, `UPDATE`, `DELETE`, `MERGE` | Prevents unauthorized modification of database state. |
| **DDL** | `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME` | Prevents destruction or alteration of schema objects. |
| **DCL / Admin** | `GRANT`, `REVOKE`, `AUDIT` | Prevents privilege escalation. |
| **TCL** | `COMMIT`, `ROLLBACK`, `SAVEPOINT` | Protects driver transaction boundaries. |
| **Locks** | `FOR UPDATE` | Prevents acquiring row exclusive locks that block concurrent transactions. |
| **PL/SQL** | `BEGIN`, `DECLARE`, `EXECUTE`, `CALL` | Blocks arbitrary code execution and autonomous transactions. |
| **System Packages** | `UTL_FILE`, `UTL_HTTP`, `UTL_TCP`, `DBMS_SCHEDULER` | Prevents filesystem exfiltration and SSRF network access. |

---

## 3. Least-Privilege Database Account Setup

QueryPilot operates using a dedicated read-only account:

```sql
-- Created by DBA during initialization:
CREATE USER qp_app_user IDENTIFIED BY "qp_app_password";
GRANT CREATE SESSION TO qp_app_user;

-- Read-only grants to retail demo schema:
GRANT SELECT ON categories TO qp_app_user;
GRANT SELECT ON products TO qp_app_user;
GRANT SELECT ON customers TO qp_app_user;
GRANT SELECT ON orders TO qp_app_user;
GRANT SELECT ON order_items TO qp_app_user;
GRANT SELECT ON payments TO qp_app_user;
GRANT SELECT ON shipments TO qp_app_user;
GRANT SELECT ON support_tickets TO qp_app_user;

-- Grants for Explain Plan:
GRANT SELECT ON plan_table TO qp_app_user;
GRANT INSERT, DELETE ON plan_table TO qp_app_user;
```

---

## 4. Bind Variable vs Interpolation Policy

QueryPilot enforces bind variables for query parameters. Direct value concatenation into SQL strings is prohibited:

```python
# Permitted: Driver-level parameterized binding
cursor.execute(
    "SELECT * FROM orders WHERE status = :status AND total_amount >= :min_amt",
    {"status": "COMPLETED", "min_amt": 100.0}
)

# Prohibited: Unsafe string interpolation
cursor.execute(f"SELECT * FROM orders WHERE status = '{user_input}'") # NEVER ALLOWED
```
