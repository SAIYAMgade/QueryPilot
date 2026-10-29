"""Query Execution, Saved Queries, and Execution History API Endpoints."""

import uuid
from typing import List, Dict, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from app.schemas.query import (
    QueryExecuteRequest, QueryExecutionResponse, QueryHistoryItem,
    SavedQueryCreate, SavedQueryUpdate, SavedQueryResponse
)
from app.database.executor import execute_query, get_query_history

router = APIRouter()

# In-memory saved queries with pre-seeded realistic retail scenarios
_saved_queries: Dict[str, SavedQueryResponse] = {}


def init_default_saved_queries():
    if _saved_queries:
        return
    now = datetime.now(timezone.utc)
    samples = [
        (
            "sq_01",
            "Customer Purchase History with Item Totals",
            "Retrieves customer orders joined with order items and product descriptions.",
            """SELECT c.customer_id, c.first_name || ' ' || c.last_name AS customer_name,
       o.order_id, o.order_date, p.product_name, oi.quantity, oi.unit_price, oi.line_total
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'COMPLETED'
ORDER BY o.order_date DESC
FETCH FIRST 25 ROWS ONLY""",
            ["reporting", "joins"]
        ),
        (
            "sq_02",
            "Monthly Revenue and Order Volume Summary",
            "Aggregates total revenue and order count grouped by order status.",
            """SELECT o.status,
       COUNT(o.order_id) AS total_orders,
       ROUND(SUM(o.total_amount), 2) AS total_revenue,
       ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM orders o
GROUP BY o.status
ORDER BY total_revenue DESC""",
            ["aggregation", "revenue"]
        ),
        (
            "sq_03",
            "Delayed Shipments Tracking",
            "Identifies shipments that experienced transit delays or unfulfilled deliveries.",
            """SELECT s.shipment_id, s.order_id, s.carrier, s.tracking_number,
       s.shipped_at, s.delivered_at, s.status AS shipment_status,
       o.total_amount, c.email AS customer_email
FROM shipments s
JOIN orders o ON s.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE s.status != 'DELIVERED'
ORDER BY s.shipped_at ASC
FETCH FIRST 20 ROWS ONLY""",
            ["fulfillment", "logistics"]
        ),
        (
            "sq_04",
            "Low Stock Products with Active Catalog Status",
            "Filters inventory for active products falling below safety stock threshold.",
            """SELECT p.product_id, p.sku, p.product_name, c.category_name,
       p.stock_quantity, p.unit_price, p.cost_price,
       ROUND(p.unit_price - p.cost_price, 2) AS gross_margin
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE p.status = 'ACTIVE' AND p.stock_quantity < 50
ORDER BY p.stock_quantity ASC""",
            ["inventory", "products"]
        ),
        (
            "sq_05",
            "Top Customers by Repeat Purchase Frequency",
            "Identifies highest value loyalty customers with more than 3 completed orders.",
            """SELECT c.customer_id, c.first_name, c.last_name, c.loyalty_tier,
       COUNT(o.order_id) AS total_orders_placed,
       ROUND(SUM(o.total_amount), 2) AS lifetime_spend
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'COMPLETED'
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_tier
HAVING COUNT(o.order_id) >= 2
ORDER BY lifetime_spend DESC
FETCH FIRST 15 ROWS ONLY""",
            ["customers", "loyalty"]
        ),
        (
            "sq_06",
            "Payment Settlement vs Order Total Reconciliation",
            "Validates payment ledger settled amount against order total to find discrepancies.",
            """SELECT o.order_id, o.order_date, o.total_amount AS order_total,
       p.payment_id, p.payment_method, p.amount AS payment_amount, p.status AS payment_status
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.total_amount != p.amount OR p.status != 'SETTLED'
ORDER BY o.order_date DESC""",
            ["audit", "reconciliation"]
        ),
        (
            "sq_07",
            "Order Date Filter - Baseline (Unindexed Scan)",
            "Baseline reporting query filtering orders by date range without index hint.",
            """SELECT o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2025-06-01'
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY""",
            ["investigation", "baseline"]
        ),
        (
            "sq_08",
            "Order Date Filter - Candidate (Indexed Scan)",
            "Optimized query utilizing index range scan for order date filtering.",
            """SELECT /*+ INDEX(o IDX_ORDERS_DATE) */ o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2025-06-01'
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY""",
            ["investigation", "candidate"]
        )
    ]
    for q_id, title, desc, sql, tags in samples:
        _saved_queries[q_id] = SavedQueryResponse(
            id=q_id,
            title=title,
            description=desc,
            sql=sql,
            parameters={},
            tags=tags,
            investigation_id=None,
            created_at=now,
            updated_at=now
        )


init_default_saved_queries()


@router.post("/execute", response_model=QueryExecutionResponse)
def run_query(request: QueryExecuteRequest):
    """Execute permitted read-only SQL query against the database."""
    # Let SecurityViolationError and StatementValidationError propagate to exception handlers (403, 422)
    return execute_query(
        sql=request.sql,
        parameters=request.parameters,
        max_rows=request.max_rows,
        timeout_sec=request.timeout_sec
    )


@router.get("/history", response_model=List[QueryHistoryItem])
def list_history(limit: int = Query(default=50, le=200)):
    """Retrieve execution history ring buffer."""
    return get_query_history(limit=limit)


@router.get("/saved", response_model=List[SavedQueryResponse])
def list_saved_queries():
    """List all saved queries."""
    return list(_saved_queries.values())


@router.post("/saved", response_model=SavedQueryResponse)
def save_query(data: SavedQueryCreate):
    """Save a query to the library."""
    q_id = f"sq_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    item = SavedQueryResponse(
        id=q_id,
        title=data.title,
        description=data.description or "",
        sql=data.sql,
        parameters=data.parameters or {},
        tags=data.tags,
        investigation_id=data.investigation_id,
        created_at=now,
        updated_at=now
    )
    _saved_queries[q_id] = item
    return item


@router.delete("/saved/{query_id}")
def delete_saved_query(query_id: str):
    """Delete a saved query."""
    if query_id not in _saved_queries:
        raise HTTPException(status_code=404, detail="Saved query not found")
    del _saved_queries[query_id]
    return {"deleted": True, "id": query_id}
