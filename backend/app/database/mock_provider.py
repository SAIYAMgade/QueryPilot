"""Deterministic Offline Simulation Sandbox Provider for QueryPilot.

Activated when live Oracle Database is not reachable.
Provides a full in-memory simulation of the Retail Operations demonstration schema:
CUSTOMERS, CATEGORIES, PRODUCTS, ORDERS, ORDER_ITEMS, PAYMENTS, SHIPMENTS, SUPPORT_TICKETS.
"""

import sqlite3
import time
import uuid
import re
from datetime import datetime, timedelta, timezone
import random
from typing import List, Dict, Any, Optional

from app.core.security import validate_read_only_query
from app.schemas.query import QueryExecutionResponse, QueryResultColumn
from app.schemas.schema_explorer import (
    TableSummary, TableDetail, ColumnMetadata, IndexMetadata, ConstraintMetadata, Relationship
)
from app.schemas.plan import PlanOperation, DiagnosticObservation, ExecutionPlanResponse


class MockDatabaseProvider:
    """In-memory SQLite-backed simulation of Oracle Retail demonstration schema."""

    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        self._seed_data()

    def _init_schema(self):
        cur = self.conn.cursor()
        cur.executescript("""
        CREATE TABLE CATEGORIES (
            CATEGORY_ID INTEGER PRIMARY KEY,
            CATEGORY_NAME TEXT NOT NULL,
            SLUG TEXT NOT NULL UNIQUE,
            IS_ACTIVE INTEGER DEFAULT 1
        );

        CREATE TABLE PRODUCTS (
            PRODUCT_ID INTEGER PRIMARY KEY,
            CATEGORY_ID INTEGER NOT NULL REFERENCES CATEGORIES(CATEGORY_ID),
            SKU TEXT NOT NULL UNIQUE,
            PRODUCT_NAME TEXT NOT NULL,
            UNIT_PRICE REAL NOT NULL,
            COST_PRICE REAL NOT NULL,
            STOCK_QUANTITY INTEGER NOT NULL,
            STATUS TEXT DEFAULT 'ACTIVE'
        );

        CREATE TABLE CUSTOMERS (
            CUSTOMER_ID INTEGER PRIMARY KEY,
            FIRST_NAME TEXT NOT NULL,
            LAST_NAME TEXT NOT NULL,
            EMAIL TEXT NOT NULL UNIQUE,
            PHONE TEXT,
            LOYALTY_TIER TEXT DEFAULT 'STANDARD',
            STATUS TEXT DEFAULT 'ACTIVE',
            CREATED_AT TEXT NOT NULL
        );

        CREATE TABLE ORDERS (
            ORDER_ID INTEGER PRIMARY KEY,
            CUSTOMER_ID INTEGER NOT NULL REFERENCES CUSTOMERS(CUSTOMER_ID),
            ORDER_DATE TEXT NOT NULL,
            TOTAL_AMOUNT REAL NOT NULL,
            STATUS TEXT DEFAULT 'COMPLETED',
            PAYMENT_STATUS TEXT DEFAULT 'PAID',
            SHIPPING_STATUS TEXT DEFAULT 'DELIVERED'
        );

        CREATE TABLE ORDER_ITEMS (
            ITEM_ID INTEGER PRIMARY KEY,
            ORDER_ID INTEGER NOT NULL REFERENCES ORDERS(ORDER_ID),
            PRODUCT_ID INTEGER NOT NULL REFERENCES PRODUCTS(PRODUCT_ID),
            QUANTITY INTEGER NOT NULL,
            UNIT_PRICE REAL NOT NULL,
            DISCOUNT REAL DEFAULT 0.0,
            LINE_TOTAL REAL NOT NULL
        );

        CREATE TABLE PAYMENTS (
            PAYMENT_ID INTEGER PRIMARY KEY,
            ORDER_ID INTEGER NOT NULL REFERENCES ORDERS(ORDER_ID),
            PAYMENT_METHOD TEXT NOT NULL,
            AMOUNT REAL NOT NULL,
            STATUS TEXT DEFAULT 'SETTLED',
            TRANSACTION_TIME TEXT NOT NULL
        );

        CREATE TABLE SHIPMENTS (
            SHIPMENT_ID INTEGER PRIMARY KEY,
            ORDER_ID INTEGER NOT NULL REFERENCES ORDERS(ORDER_ID),
            CARRIER TEXT NOT NULL,
            TRACKING_NUMBER TEXT UNIQUE,
            SHIPPED_AT TEXT,
            DELIVERED_AT TEXT,
            STATUS TEXT DEFAULT 'DELIVERED'
        );

        CREATE TABLE SUPPORT_TICKETS (
            TICKET_ID INTEGER PRIMARY KEY,
            CUSTOMER_ID INTEGER NOT NULL REFERENCES CUSTOMERS(CUSTOMER_ID),
            ORDER_ID INTEGER REFERENCES ORDERS(ORDER_ID),
            SUBJECT TEXT NOT NULL,
            STATUS TEXT DEFAULT 'CLOSED',
            PRIORITY TEXT DEFAULT 'MEDIUM',
            CREATED_AT TEXT NOT NULL
        );

        -- Synthetic indexes representing Oracle indexes
        CREATE INDEX IDX_CUST_EMAIL ON CUSTOMERS(EMAIL);
        CREATE INDEX IDX_ORDERS_CUST ON ORDERS(CUSTOMER_ID);
        CREATE INDEX IDX_ORDERS_DATE ON ORDERS(ORDER_DATE);
        CREATE INDEX IDX_ORDERS_STATUS ON ORDERS(STATUS);
        CREATE INDEX IDX_ITEMS_ORDER ON ORDER_ITEMS(ORDER_ID);
        CREATE INDEX IDX_ITEMS_PROD ON ORDER_ITEMS(PRODUCT_ID);
        CREATE INDEX IDX_PAY_ORDER ON PAYMENTS(ORDER_ID);
        CREATE INDEX IDX_SHIP_ORDER ON SHIPMENTS(ORDER_ID);
        """)
        self.conn.commit()

    def _seed_data(self):
        """Populate deterministic synthetic retail records (Seed=42)."""
        rng = random.Random(42)
        cur = self.conn.cursor()

        # 1. Categories
        cats = [
            (1, "Electronics", "electronics", 1),
            (2, "Computers & Accessories", "computers", 1),
            (3, "Home Office", "home-office", 1),
            (4, "Audio & Sound", "audio", 1),
            (5, "Photography", "photography", 1),
            (6, "Wearables", "wearables", 1),
            (7, "Storage & Networking", "storage-networking", 1),
            (8, "Gaming Accessories", "gaming", 1)
        ]
        cur.executemany("INSERT INTO CATEGORIES VALUES (?,?,?,?)", cats)

        # 2. Products
        products = []
        prod_names = [
            ("Ergonomic Keyboard", 89.99, 45.00), ("Wireless Mouse", 34.50, 15.00),
            ("UltraWide 34in Monitor", 499.00, 310.00), ("Noise Cancelling Headphones", 199.99, 90.00),
            ("USB-C Thunderbolt Dock", 159.00, 75.00), ("HD Webcam 1080p", 69.99, 28.00),
            ("Standing Desk Mat", 45.00, 18.00), ("Studio Microphone", 129.50, 60.00),
            ("External SSD 1TB", 109.99, 52.00), ("Mechanical Keycaps Set", 29.99, 10.00),
            ("Smart Fitness Band", 79.99, 32.00), ("Gaming Mousepad XL", 24.99, 8.00),
            ("Wi-Fi 6 Router", 139.00, 65.00), ("Cat8 Ethernet Cable 10m", 15.99, 4.50),
            ("Bluetooth Speaker Mini", 49.99, 20.00), ("LED Monitor Light Bar", 59.99, 22.00)
        ]
        p_id = 1
        for cat_id in range(1, 9):
            for name, price, cost in prod_names[:4]:
                sku = f"SKU-C{cat_id:02d}-P{p_id:03d}"
                qty = rng.randint(5, 250)
                products.append((p_id, cat_id, sku, f"{name} {cat_id}", price, cost, qty, "ACTIVE"))
                p_id += 1
        cur.executemany("INSERT INTO PRODUCTS VALUES (?,?,?,?,?,?,?,?)", products)

        # 3. Customers
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Casey", "Riley", "Cameron", "Jesse", "Pat", "Quinn"]
        last_names = ["Chen", "Smith", "Patel", "Garcia", "Johnson", "Kim", "Miller", "Davis", "Wilson", "Martinez", "Anderson", "Taylor"]
        customers = []
        base_date = datetime(2025, 1, 1)
        for c_id in range(1, 101):
            fn = rng.choice(first_names)
            ln = rng.choice(last_names)
            email = f"{fn.lower()}.{ln.lower()}{c_id}@example.com"
            phone = f"+1-555-01{c_id:02d}"
            tier = rng.choice(["STANDARD", "STANDARD", "SILVER", "GOLD", "PLATINUM"])
            created_at = (base_date + timedelta(days=rng.randint(0, 300))).strftime("%Y-%m-%d %H:%M:%S")
            customers.append((c_id, fn, ln, email, phone, tier, "ACTIVE", created_at))
        cur.executemany("INSERT INTO CUSTOMERS VALUES (?,?,?,?,?,?,?,?)", customers)

        # 4. Orders & Items
        orders = []
        items = []
        payments = []
        shipments = []
        tickets = []
        item_id = 1
        pay_id = 1
        ship_id = 1
        ticket_id = 1

        order_base_date = datetime(2025, 3, 1)
        for o_id in range(1, 301):
            cust_id = rng.randint(1, 100)
            order_dt = (order_base_date + timedelta(days=rng.randint(0, 240), hours=rng.randint(1, 23))).strftime("%Y-%m-%d %H:%M:%S")
            status = rng.choice(["COMPLETED", "COMPLETED", "COMPLETED", "SHIPPED", "PROCESSING", "CANCELLED", "PENDING"])
            pay_status = "REFUNDED" if status == "CANCELLED" else ("PAID" if status in ("COMPLETED", "SHIPPED") else "PENDING")
            ship_status = "DELIVERED" if status == "COMPLETED" else ("IN_TRANSIT" if status == "SHIPPED" else "PENDING")

            # 1 to 4 items per order
            num_items = rng.randint(1, 4)
            order_total = 0.0
            for _ in range(num_items):
                prod = rng.choice(products)
                pr_id = prod[0]
                u_price = prod[4]
                qty = rng.randint(1, 3)
                discount = 0.0 if rng.random() > 0.25 else round(u_price * 0.1, 2)
                line_total = round((u_price - discount) * qty, 2)
                order_total += line_total
                items.append((item_id, o_id, pr_id, qty, u_price, discount, line_total))
                item_id += 1

            order_total = round(order_total, 2)
            orders.append((o_id, cust_id, order_dt, order_total, status, pay_status, ship_status))

            # Payment
            p_method = rng.choice(["CREDIT_CARD", "PAYPAL", "WIRE_TRANSFER", "APPLE_PAY"])
            payments.append((pay_id, o_id, p_method, order_total, "SETTLED" if pay_status == "PAID" else pay_status, order_dt))
            pay_id += 1

            # Shipment (if shipped or delivered)
            if status in ("COMPLETED", "SHIPPED"):
                carrier = rng.choice(["FEDEX", "UPS", "DHL", "USPS"])
                track_no = f"TRK-{o_id:05d}-{carrier[:2]}"
                shipped_at = order_dt
                deliv_at = (datetime.strptime(order_dt, "%Y-%m-%d %H:%M:%S") + timedelta(days=rng.randint(2, 6))).strftime("%Y-%m-%d %H:%M:%S") if status == "COMPLETED" else None
                shipments.append((ship_id, o_id, carrier, track_no, shipped_at, deliv_at, ship_status))
                ship_id += 1

            # Support tickets (randomly on some orders)
            if rng.random() < 0.2:
                subject = rng.choice(["Delayed shipment inquiry", "Damaged box on arrival", "Return request", "Invoice copy requested"])
                t_status = rng.choice(["RESOLVED", "RESOLVED", "IN_PROGRESS", "OPEN"])
                tickets.append((ticket_id, cust_id, o_id, subject, t_status, "MEDIUM", order_dt))
                ticket_id += 1

        cur.executemany("INSERT INTO ORDERS VALUES (?,?,?,?,?,?,?)", orders)
        cur.executemany("INSERT INTO ORDER_ITEMS VALUES (?,?,?,?,?,?,?)", items)
        cur.executemany("INSERT INTO PAYMENTS VALUES (?,?,?,?,?,?)", payments)
        cur.executemany("INSERT INTO SHIPMENTS VALUES (?,?,?,?,?,?,?)", shipments)
        cur.executemany("INSERT INTO SUPPORT_TICKETS VALUES (?,?,?,?,?,?,?)", tickets)
        self.conn.commit()

    def execute_query(
        self,
        sql: str,
        parameters: Optional[Dict[str, Any]] = None,
        max_rows: Optional[int] = 1000,
        timeout_sec: Optional[int] = 30
    ) -> QueryExecutionResponse:
        """Execute a read-only query in simulation mode."""
        query_id = f"sim_{uuid.uuid4().hex[:10]}"
        sanitized_sql = validate_read_only_query(sql)
        params = parameters or {}
        limit = min(max_rows or 1000, 1000)

        # Adapt Oracle specific syntax for SQLite compatibility in simulation mode
        sim_sql = sanitized_sql
        # Handle FETCH FIRST N ROWS ONLY -> LIMIT N
        fetch_match = re.search(r"FETCH\s+FIRST\s+(\d+)\s+ROWS?\s+ONLY", sim_sql, re.IGNORECASE)
        if fetch_match:
            limit_val = fetch_match.group(1)
            sim_sql = re.sub(r"FETCH\s+FIRST\s+(\d+)\s+ROWS?\s+ONLY", f"LIMIT {limit_val}", sim_sql, flags=re.IGNORECASE)
        elif not re.search(r"\bLIMIT\b", sim_sql, re.IGNORECASE):
            sim_sql = f"{sim_sql} LIMIT {limit + 1}"

        # Replace Oracle NVL -> IFNULL
        sim_sql = re.sub(r"\bNVL\(", "IFNULL(", sim_sql, flags=re.IGNORECASE)
        # Replace Oracle SYSDATE -> CURRENT_TIMESTAMP
        sim_sql = re.sub(r"\bSYSDATE\b", "CURRENT_TIMESTAMP", sim_sql, flags=re.IGNORECASE)

        cur = self.conn.cursor()
        t_start = time.perf_counter()
        try:
            # Map bind params :param to ? or named
            sqlite_params = {}
            for k, v in params.items():
                sqlite_params[k.lstrip(":")] = v

            cur.execute(sim_sql, sqlite_params)
            t_exec = time.perf_counter()
            exec_duration_ms = round((t_exec - t_start) * 1000.0, 3)

            columns = []
            if cur.description:
                for d in cur.description:
                    columns.append(QueryResultColumn(name=d[0], data_type="VARCHAR2/NUMBER", nullable=True))

            rows_raw = cur.fetchall()
            t_fetch = time.perf_counter()
            fetch_duration_ms = round((t_fetch - t_exec) * 1000.0, 3)

            truncated = len(rows_raw) > limit
            rows = [dict(r) for r in rows_raw[:limit]]

            return QueryExecutionResponse(
                query_id=query_id,
                sql=sanitized_sql,
                status="SUCCESS",
                duration_ms=exec_duration_ms,
                fetch_duration_ms=fetch_duration_ms,
                rows_returned=len(rows),
                truncated=truncated,
                columns=columns,
                rows=rows,
                environment="Offline Simulation Sandbox (Oracle at localhost:1521 unreachable)",
                executed_at=datetime.now(timezone.utc)
            )
        except Exception as exc:
            return QueryExecutionResponse(
                query_id=query_id,
                sql=sanitized_sql,
                status="ERROR",
                duration_ms=0.0,
                rows_returned=0,
                truncated=False,
                columns=[],
                rows=[],
                error={
                    "code": "ORA-00942" if "no such table" in str(exc) else "ORA-00904",
                    "message": str(exc),
                    "category": "SYNTAX_OR_EXECUTION_ERROR"
                },
                environment="Offline Simulation Sandbox (Oracle at localhost:1521 unreachable)",
                executed_at=datetime.now(timezone.utc)
            )
        finally:
            cur.close()

    def get_tables(self) -> List[TableSummary]:
        """List tables in the simulation schema."""
        tables_meta = [
            ("CATEGORIES", 8, 4),
            ("PRODUCTS", 32, 8),
            ("CUSTOMERS", 100, 8),
            ("ORDERS", 300, 7),
            ("ORDER_ITEMS", 750, 7),
            ("PAYMENTS", 300, 6),
            ("SHIPMENTS", 240, 7),
            ("SUPPORT_TICKETS", 60, 7)
        ]
        return [
            TableSummary(
                owner="QP_APP_USER",
                table_name=t[0],
                num_rows=t[1],
                is_estimated_rows=True,
                column_count=t[2],
                last_analyzed=datetime.now(timezone.utc)
            )
            for t in tables_meta
        ]

    def get_table_detail(self, table_name: str) -> TableDetail:
        """Return detail metadata for a simulation table."""
        t_name = table_name.upper()
        cur = self.conn.cursor()
        cur.execute(f"PRAGMA table_info({t_name})")
        cols_info = cur.fetchall()
        if not cols_info:
            raise KeyError(f"Table {t_name} not found")

        columns = []
        for c in cols_info:
            cid, cname, ctype, notnull, dflt, pk = c
            columns.append(ColumnMetadata(
                name=cname,
                data_type="NUMBER" if "INT" in ctype or "REAL" in ctype else "VARCHAR2(100)",
                nullable=(notnull == 0),
                is_primary_key=bool(pk),
                column_id=cid + 1
            ))

        # Preview rows
        cur.execute(f"SELECT * FROM {t_name} LIMIT 10")
        preview = [dict(r) for r in cur.fetchall()]
        cur.close()

        # Indexes
        indexes = [
            IndexMetadata(index_name=f"PK_{t_name}", uniqueness="UNIQUE", columns=[columns[0].name], status="VALID")
        ]

        # Constraints
        constraints = [
            ConstraintMetadata(
                constraint_name=f"PK_{t_name}",
                constraint_type="P",
                type_display="PRIMARY KEY",
                columns=[columns[0].name]
            )
        ]

        return TableDetail(
            owner="QP_APP_USER",
            table_name=t_name,
            num_rows=len(preview) * 10,
            is_estimated_rows=True,
            last_analyzed=datetime.now(timezone.utc),
            columns=columns,
            indexes=indexes,
            constraints=constraints,
            preview_rows=preview
        )

    def get_relationships(self) -> List[Relationship]:
        """Return relationships for foreign keys in the retail schema."""
        return [
            Relationship(constraint_name="FK_PROD_CAT", from_table="PRODUCTS", from_column="CATEGORY_ID", to_table="CATEGORIES", to_column="CATEGORY_ID"),
            Relationship(constraint_name="FK_ORDERS_CUST", from_table="ORDERS", from_column="CUSTOMER_ID", to_table="CUSTOMERS", to_column="CUSTOMER_ID"),
            Relationship(constraint_name="FK_ITEMS_ORDER", from_table="ORDER_ITEMS", from_column="ORDER_ID", to_table="ORDERS", to_column="ORDER_ID"),
            Relationship(constraint_name="FK_ITEMS_PROD", from_table="ORDER_ITEMS", from_column="PRODUCT_ID", to_table="PRODUCTS", to_column="PRODUCT_ID"),
            Relationship(constraint_name="FK_PAY_ORDER", from_table="PAYMENTS", from_column="ORDER_ID", to_table="ORDERS", to_column="ORDER_ID"),
            Relationship(constraint_name="FK_SHIP_ORDER", from_table="SHIPMENTS", from_column="ORDER_ID", to_table="ORDERS", to_column="ORDER_ID"),
            Relationship(constraint_name="FK_TICKET_CUST", from_table="SUPPORT_TICKETS", from_column="CUSTOMER_ID", to_table="CUSTOMERS", to_column="CUSTOMER_ID"),
            Relationship(constraint_name="FK_TICKET_ORDER", from_table="SUPPORT_TICKETS", from_column="ORDER_ID", to_table="ORDERS", to_column="ORDER_ID"),
        ]

    def generate_simulated_plan(self, sql: str) -> ExecutionPlanResponse:
        """
        Generate realistic Oracle execution plan tree matching the cost-based optimizer model.
        """
        stmt_id = f"PLAN_{uuid.uuid4().hex[:8].upper()}"
        sql_upper = sql.upper()

        ops: List[PlanOperation] = []
        obs: List[DiagnosticObservation] = []
        raw_lines = [
            "Plan hash value: 2849104822",
            "",
            "-------------------------------------------------------------------------------------------------",
            "| Id  | Operation                     | Name            | Rows  | Bytes | Cost (%CPU)| Time     |",
            "-------------------------------------------------------------------------------------------------"
        ]

        # Detect joins, scans, aggregations
        has_join = "JOIN" in sql_upper or ("," in sql_upper and "FROM" in sql_upper and "WHERE" in sql_upper)
        has_agg = any(kw in sql_upper for kw in ("GROUP BY", "SUM(", "COUNT(", "AVG(", "ORDER BY"))
        has_date_filter = "ORDER_DATE" in sql_upper or "CREATED_AT" in sql_upper
        has_cust_filter = "CUSTOMER_ID" in sql_upper or "EMAIL" in sql_upper

        plan_id = 0
        if has_agg:
            ops.append(PlanOperation(
                id=plan_id, parent_id=None, operation="SELECT STATEMENT", options=None,
                cost=14, cardinality=25, bytes=1200, depth=0
            ))
            raw_lines.append(f"|   0 | SELECT STATEMENT              |                 |    25 |  1200 |    14   (8)| 00:00:01 |")
            plan_id += 1

            ops.append(PlanOperation(
                id=plan_id, parent_id=0, operation="SORT", options="GROUP BY",
                cost=14, cardinality=25, bytes=1200, depth=1
            ))
            raw_lines.append(f"|   1 |  SORT GROUP BY                |                 |    25 |  1200 |    14   (8)| 00:00:01 |")
            parent_join_id = plan_id
            plan_id += 1
        else:
            ops.append(PlanOperation(
                id=plan_id, parent_id=None, operation="SELECT STATEMENT", options=None,
                cost=8, cardinality=50, bytes=2400, depth=0
            ))
            raw_lines.append(f"|   0 | SELECT STATEMENT              |                 |    50 |  2400 |     8   (0)| 00:00:01 |")
            parent_join_id = 0
            plan_id += 1

        if has_join:
            ops.append(PlanOperation(
                id=plan_id, parent_id=parent_join_id, operation="HASH JOIN", options=None,
                cost=8, cardinality=150, bytes=6000, depth=2 if has_agg else 1
            ))
            raw_lines.append(f"|   {plan_id} |   HASH JOIN                   |                 |   150 |  6000 |     8   (0)| 00:00:01 |")
            hash_id = plan_id
            plan_id += 1

            # Left child: Customers or Categories table scan
            ops.append(PlanOperation(
                id=plan_id, parent_id=hash_id, operation="TABLE ACCESS", options="FULL",
                object_name="CUSTOMERS", object_type="TABLE", cost=3, cardinality=100, bytes=2800, depth=3 if has_agg else 2,
                filter_predicates="STATUS='ACTIVE'" if "STATUS" in sql_upper else None
            ))
            raw_lines.append(f"|   {plan_id} |    TABLE ACCESS FULL          | CUSTOMERS       |   100 |  2800 |     3   (0)| 00:00:01 |")
            plan_id += 1

            # Right child: Orders
            if has_date_filter and "INDEX" in sql_upper:
                ops.append(PlanOperation(
                    id=plan_id, parent_id=hash_id, operation="TABLE ACCESS", options="BY INDEX ROWID",
                    object_name="ORDERS", object_type="TABLE", cost=4, cardinality=75, bytes=3200, depth=3 if has_agg else 2,
                    access_predicates="ORDER_DATE >= TO_DATE('2025-01-01')"
                ))
                raw_lines.append(f"|   {plan_id} |    TABLE ACCESS BY INDEX ROWID| ORDERS          |    75 |  3200 |     4   (0)| 00:00:01 |")
            else:
                ops.append(PlanOperation(
                    id=plan_id, parent_id=hash_id, operation="TABLE ACCESS", options="FULL",
                    object_name="ORDERS", object_type="TABLE", cost=5, cardinality=300, bytes=9000, depth=3 if has_agg else 2,
                    filter_predicates="ORDER_DATE >= '2025-01-01'" if has_date_filter else None
                ))
                raw_lines.append(f"|   {plan_id} |    TABLE ACCESS FULL          | ORDERS          |   300 |  9000 |     5   (0)| 00:00:01 |")
            plan_id += 1
        else:
            # Single table scan or index lookup
            target_table = "CUSTOMERS" if "CUSTOMERS" in sql_upper else ("ORDERS" if "ORDERS" in sql_upper else "PRODUCTS")
            if has_cust_filter:
                ops.append(PlanOperation(
                    id=plan_id, parent_id=parent_join_id, operation="TABLE ACCESS", options="BY INDEX ROWID",
                    object_name=target_table, object_type="TABLE", cost=2, cardinality=1, bytes=80, depth=1,
                    access_predicates="EMAIL=:B1"
                ))
                raw_lines.append(f"|   {plan_id} |  TABLE ACCESS BY INDEX ROWID  | {target_table:<15} |     1 |    80 |     2   (0)| 00:00:01 |")
            else:
                ops.append(PlanOperation(
                    id=plan_id, parent_id=parent_join_id, operation="TABLE ACCESS", options="FULL",
                    object_name=target_table, object_type="TABLE", cost=4, cardinality=100, bytes=2800, depth=1
                ))
                raw_lines.append(f"|   {plan_id} |  TABLE ACCESS FULL            | {target_table:<15} |   100 |  2800 |     4   (0)| 00:00:01 |")

        raw_lines.append("-------------------------------------------------------------------------------------------------")
        raw_lines.append("")
        raw_lines.append("Predicate Information (identified by operation id):")
        raw_lines.append("---------------------------------------------------")
        raw_lines.append(f"   {plan_id - 1} - filter(\"STATUS\"='ACTIVE')")

        # Build Diagnostic Observations according to rule-based engine
        for op in ops:
            if op.operation == "TABLE ACCESS" and op.options == "FULL":
                obs.append(DiagnosticObservation(
                    id=f"obs_{uuid.uuid4().hex[:6]}",
                    category="FULL_TABLE_SCAN",
                    severity="INFO" if (op.cardinality or 0) < 500 else "INVESTIGATE",
                    title=f"Full Table Scan on {op.object_name}",
                    what_observed=f"Oracle optimizer selected TABLE ACCESS FULL on table '{op.object_name}' (Cost: {op.cost}).",
                    where_observed=f"Operation Id {op.id}: TABLE ACCESS FULL [{op.object_name}]",
                    why_it_matters="A full table scan reads every block up to the high-water mark. For small reference tables (<1,000 rows), this is often optimal due to multi-block I/O. For large tables filtered by selective criteria, an index access path may reduce I/O.",
                    evidence_needed="Check table row count, index presence, filter selectivity, and physical I/O waits.",
                    suggested_step=f"Verify if columns in the WHERE clause on {op.object_name} have a supporting B-tree index.",
                    confidence="HEURISTIC"
                ))

        if has_agg:
            obs.append(DiagnosticObservation(
                id=f"obs_{uuid.uuid4().hex[:6]}",
                category="SORT_AGGREGATION",
                severity="INFO",
                title="Sort / Group By Aggregation in Plan",
                what_observed="Plan includes SORT GROUP BY operation.",
                where_observed="Operation Id 1: SORT GROUP BY",
                why_it_matters="Sort operations consume PGA (Program Global Area) memory. If workarea_size_policy limits are exceeded, sorts spill to TEMP tablespace.",
                evidence_needed="Compare PGA memory allocation against actual temp spills during high concurrency.",
                suggested_step="Ensure indexes cover group-by keys if presorted index scans are desired.",
                confidence="EVIDENCED"
            ))

        return ExecutionPlanResponse(
            query_id=f"qry_{uuid.uuid4().hex[:8]}",
            statement_id=stmt_id,
            plan_type="ESTIMATED",
            is_actual=False,
            operations=ops,
            observations=obs,
            raw_plan_text="\n".join(raw_lines),
            optimizer_cost=ops[0].cost,
            limitations_note="Simulated Oracle Plan: Reflects Oracle cost-based optimizer mechanics on the Retail demo schema.",
            generated_at=datetime.now(timezone.utc)
        )


mock_db = MockDatabaseProvider()
