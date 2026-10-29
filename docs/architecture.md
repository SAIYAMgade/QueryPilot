# QueryPilot Architecture & System Design

QueryPilot is a local-first SQL diagnostic and performance investigation workbench designed specifically for Oracle Database. It enables developers, DBAs, and database engineers to investigate query performance, analyze execution plans, diagnose SQL errors, verify result equivalence between query variants, and produce reproducible technical reports.

---

## 1. System Topology

```
+-------------------------------------------------------------------------+
|                           FRONTEND (React + TS)                         |
|  - Monaco / CodeEditor   - DataGrid Results        - Plan Tree Viewer   |
|  - Comparison Runner     - Diagnostics Inspector   - Report Generator   |
+------------------------------------+------------------------------------+
                                     | HTTP REST (JSON)
                                     v
+------------------------------------+------------------------------------+
|                           BACKEND (FastAPI)                             |
|                                                                         |
|  +--------------------+  +----------------------+  +-----------------+  |
|  |  Security & AST    |  |  Plan Analyzer       |  | Error Analyzer  |  |
|  |  Read-Only Parser  |  |  PLAN_TABLE & Rules  |  | ORA- KB Engine  |  |
|  +--------------------+  +----------------------+  +-----------------+  |
|                                                                         |
|  +--------------------+  +----------------------+  +-----------------+  |
|  |  Benchmarking      |  |  Multiset Equivalence|  | Investigations  |  |
|  |  Statistical Engine|  |  Row Comparator      |  | State Machine   |  |
|  +--------------------+  +----------------------+  +-----------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  |               Database Access Layer (python-oracledb)             |  |
|  |  - Thin Mode (No Instant Client required)                         |  |
|  |  - Least-Privilege Execution User                                 |  |
|  |  - Fallback: Deterministic Offline Retail Simulation Sandbox      |  |
|  +-------------------------------------------------------------------+  |
+------------------------------------+------------------------------------+
                                     | Oracle Net Protocol (TCP:1521)
                                     v
+-------------------------------------------------------------------------+
|                       ORACLE DATABASE 23ai / 21c                        |
|  - ALL_TABLES, ALL_TAB_COLUMNS, ALL_CONSTRAINTS, ALL_INDEXES (Catalog)  |
|  - PLAN_TABLE / DBMS_XPLAN.DISPLAY (Estimated Execution Plans)          |
|  - Retail Operations Schema (CUSTOMERS, ORDERS, ORDER_ITEMS, PRODUCTS)  |
|  - QUERY_PILOT_PKG (PL/SQL Investigation Lifecycle Package)            |
+-------------------------------------------------------------------------+
```

---

## 2. Core Modules

### 2.1 Security & Statement AST Parser (`app/core/security.py`)
- Analyzes incoming SQL queries via AST and token stream before execution.
- Only permits read-only `SELECT` and `WITH ... SELECT` queries.
- Strictly rejects DML (`INSERT`, `UPDATE`, `DELETE`, `MERGE`), DDL (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`), TCL (`COMMIT`, `ROLLBACK`), session alteration, and dangerous packages (`UTL_FILE`, `UTL_HTTP`, `DBMS_SCHEDULER`).
- Strips comments, checks for embedded statement delimiters (semicolons), and blocks `FOR UPDATE` row-locking clauses.

### 2.2 Database Connection & Execution Layer (`app/database/`)
- Powered by `python-oracledb` in Thin mode (pure Python network communication, no native C libraries required).
- Least-privilege execution: connects with `QP_APP_USER`, never `SYSDBA`.
- Explicit timing boundaries: cleanly isolates pure database execution time (`cursor.execute()`) from driver result fetching time (`cursor.fetchmany()`).
- Safeguards: enforces configurable maximum query duration (`call_timeout = 30s`) and row truncation thresholds (default 1,000 rows).
- Offline Sandbox Fallback: when live Oracle is offline or unreachable, seamlessly provides an in-memory simulation of the retail operations schema with exact column structures and synthetic data, clearly labeled with environment metadata.

### 2.3 Execution Plan Analyzer (`app/diagnostics/plan_analyzer.py`)
- Generates execution plans using supported Oracle mechanics:
  `EXPLAIN PLAN SET STATEMENT_ID = '...' FOR <query>`
  `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', '...', 'ALL +PREDICATE'))`
- Extracts structured plan nodes from `PLAN_TABLE` and cleans up temporary statement rows immediately.
- Evaluates rule-based diagnostic observations (Full Table Scan heuristics, Index Full Scan, Hash Joins, Sort operations, and function-wrapped predicate columns).
- Clearly differentiates ESTIMATED cost-based optimizer plans from runtime cursor execution statistics.

### 2.4 Comparison Lab & Multiset Equivalence (`app/benchmarking/`)
- Conducts repeatable benchmark iterations across Baseline and Candidate query variants (configurable warm-up and measured runs).
- Equivalence verification: implements multiset frequency counting rather than naive positional matching, ensuring unordered SQL result sets are compared correctly.
- Statistical calculations: median, min, max, and interquartile range (IQR) to guard against transient outliers.
- Transparent reporting: explicitly documents measurement boundaries, caching influences, and caveats.

### 2.5 Error Diagnostics Knowledge Base (`app/diagnostics/error_analyzer.py`)
- Curated diagnostic engine for common Oracle error codes: `ORA-00942`, `ORA-00904`, `ORA-00001`, `ORA-01722`, `ORA-00933`.
- Returns plain-English explanations, kernel root-cause mechanics, recommended data dictionary checks (with exact copyable SQL), and side-by-side corrected SQL examples.
- Clearly flags diagnostic conclusions as confirmed root causes vs investigative hypotheses.

### 2.6 Investigation Governance & Technical Reports (`app/investigations/`, `app/reports/`)
- Persistent investigation cases with full audit timelines.
- Gated resolution criteria: an investigation cannot be marked `RESOLVED` without a documented root-cause explanation, proposed correction, and verification notes.
- Generates reproducible, self-contained HTML technical reports and RFC 4180 CSV exports.
