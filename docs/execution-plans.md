# Oracle Execution Plan Analysis & Diagnostics

Understanding how Oracle Database executes a SQL query is fundamental to query performance engineering. QueryPilot provides a structured execution plan analyzer built on Oracle's cost-based optimizer (CBO).

---

## 1. Plan Extraction Workflow

QueryPilot uses standard, supported Oracle Database APIs:

```sql
-- Step 1: Compute estimated plan with unique statement ID
EXPLAIN PLAN SET STATEMENT_ID = 'QP_A1B2C3D4E5' FOR
SELECT o.order_id, o.order_date, c.email
FROM orders o JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2025-06-01';

-- Step 2: Extract formatted plan text via DBMS_XPLAN
SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY('PLAN_TABLE', 'QP_A1B2C3D4E5', 'ALL +PREDICATE'));

-- Step 3: Extract structured hierarchical operations from PLAN_TABLE
SELECT id, parent_id, operation, options, object_name, cost, cardinality, bytes,
       access_predicates, filter_predicates, depth
FROM plan_table
WHERE statement_id = 'QP_A1B2C3D4E5'
ORDER BY id;

-- Step 4: Clean up temporary plan table rows
DELETE FROM plan_table WHERE statement_id = 'QP_A1B2C3D4E5';
COMMIT;
```

---

## 2. Estimated Plans vs Runtime Cursor Statistics

QueryPilot strictly distinguishes plan formats:

- **ESTIMATED PLAN (Explain Plan)**: Computed by Oracle's cost-based optimizer based on current data dictionary statistics (table row counts, index heights, histogram buckets). **The query is NOT executed.** Runtime cardinality, bind peeking variations, and temp spills are not measured.
- **ACTUAL STATS (V$SQL_PLAN_STATISTICS / GATHER_PLAN_STATISTICS)**: Collected when the query is actually executed with `/*+ GATHER_PLAN_STATISTICS */` enabled and the user holds appropriate `SELECT_CATALOG_ROLE` or `V$` privileges.

QueryPilot never labels an estimated plan as actual runtime execution statistics.

---

## 3. Rule-Based Diagnostic Observations

QueryPilot applies evidence-based diagnostic rules to plan operations:

### Rule 1: Full Table Scan (FTS)
- **Heuristic**: Evaluates whether `TABLE ACCESS FULL` is optimal.
- **Principle**: A full table scan is NOT automatically a defect! For small reference tables (<1,000 rows) or queries returning >15% of table blocks, multi-block I/O (`db_file_multiblock_read_count`) makes full scans faster than single-block index lookups.
- **Severity**: Marked `INFO` for small tables, and `INVESTIGATE` for large tables with selective predicates.

### Rule 2: Index Full Scan vs Range Scan
- **Heuristic**: Detects when an entire B-tree index is scanned leaf-by-leaf.
- **Principle**: Indicates that an `ORDER BY` clause matched the index sequence, or an inequality filter prevented a bounded range scan.

### Rule 3: Hash Join on High Cardinality
- **Heuristic**: Evaluates build and probe inputs in hash joins.
- **Principle**: Hash joins excel for large, unordered datasets but require Program Global Area (PGA) memory. If workarea limits are exceeded, hashes spill to temporary tablespace.

### Rule 4: Function Applied to Predicate Column
- **Heuristic**: Detects functions like `UPPER(col)`, `LOWER(col)`, or `TRUNC(col)` in `WHERE` clauses.
- **Principle**: Standard B-tree indexes cannot be traversed if a function alters column values. Recommends either query rewrite or an Oracle Function-Based Index (`CREATE INDEX idx ON tbl(UPPER(col))`).
