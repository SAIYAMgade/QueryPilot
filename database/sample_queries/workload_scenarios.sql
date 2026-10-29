-- ============================================================================
-- QueryPilot Approved Workload Scenarios (Retail Operations Domain)
-- Each scenario demonstrates specific access paths, join methods, aggregations,
-- or error diagnostics for database performance engineering.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- Scenario 1: Customer Purchase History (Joins and Row Limiting)
-- Demonstrates: Multi-table join (CUSTOMERS -> ORDERS -> ORDER_ITEMS -> PRODUCTS)
-- ----------------------------------------------------------------------------
SELECT c.customer_id,
       c.first_name || ' ' || c.last_name AS customer_name,
       o.order_id,
       o.order_date,
       p.product_name,
       oi.quantity,
       oi.unit_price,
       oi.line_total
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.status = 'COMPLETED'
ORDER BY o.order_date DESC
FETCH FIRST 25 ROWS ONLY;

-- ----------------------------------------------------------------------------
-- Scenario 2: Monthly Revenue Summary (Aggregations and Group By)
-- Demonstrates: HASH GROUP BY vs SORT GROUP BY, PGA workarea memory usage
-- ----------------------------------------------------------------------------
SELECT o.status,
       COUNT(o.order_id) AS total_orders,
       ROUND(SUM(o.total_amount), 2) AS total_revenue,
       ROUND(AVG(o.total_amount), 2) AS avg_order_value
FROM orders o
GROUP BY o.status
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- Scenario 3: Orders by Date and Status (Index Range Scan vs Full Table Scan)
-- Baseline: Unindexed scan / potential FTS
-- Candidate: Indexed range scan using composite index
-- ----------------------------------------------------------------------------
-- Baseline:
SELECT o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= TO_TIMESTAMP('2025-06-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS')
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY;

-- Candidate (Index Hint):
SELECT /*+ INDEX(o IDX_ORDERS_DATE) */ o.order_id, o.order_date, o.total_amount, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= TO_TIMESTAMP('2025-06-01 00:00:00', 'YYYY-MM-DD HH24:MI:SS')
ORDER BY o.order_date DESC
FETCH FIRST 50 ROWS ONLY;

-- ----------------------------------------------------------------------------
-- Scenario 4: Products with Low Inventory (Selective Filter)
-- Demonstrates: Index range scan on STOCK_QUANTITY
-- ----------------------------------------------------------------------------
SELECT p.product_id, p.sku, p.product_name, c.category_name,
       p.stock_quantity, p.unit_price, p.cost_price,
       ROUND(p.unit_price - p.cost_price, 2) AS gross_margin
FROM products p
JOIN categories c ON p.category_id = c.category_id
WHERE p.status = 'ACTIVE' AND p.stock_quantity < 50
ORDER BY p.stock_quantity ASC;

-- ----------------------------------------------------------------------------
-- Scenario 5: Repeat Purchase Customers (HAVING Clause and Subquery)
-- Demonstrates: Aggregation filter selectivity
-- ----------------------------------------------------------------------------
SELECT c.customer_id, c.first_name, c.last_name, c.loyalty_tier,
       COUNT(o.order_id) AS total_orders_placed,
       ROUND(SUM(o.total_amount), 2) AS lifetime_spend
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.status = 'COMPLETED'
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_tier
HAVING COUNT(o.order_id) >= 2
ORDER BY lifetime_spend DESC
FETCH FIRST 15 ROWS ONLY;

-- ----------------------------------------------------------------------------
-- Scenario 6: Delayed Shipments Tracking (Outer Join / Null checks)
-- Demonstrates: Non-delivered order identification
-- ----------------------------------------------------------------------------
SELECT s.shipment_id, s.order_id, s.carrier, s.tracking_number,
       s.shipped_at, s.delivered_at, s.status AS shipment_status,
       o.total_amount, c.email AS customer_email
FROM shipments s
JOIN orders o ON s.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE s.status != 'DELIVERED'
ORDER BY s.shipped_at ASC
FETCH FIRST 20 ROWS ONLY;

-- ----------------------------------------------------------------------------
-- Scenario 7: Payment Ledger Reconciliation (Equivalence & Anomaly Detection)
-- Demonstrates: Finding discrepancy between payments settled and orders placed
-- ----------------------------------------------------------------------------
SELECT o.order_id, o.order_date, o.total_amount AS order_total,
       p.payment_id, p.payment_method, p.amount AS payment_amount, p.status AS payment_status
FROM orders o
JOIN payments p ON o.order_id = p.order_id
WHERE o.total_amount != p.amount OR p.status != 'SETTLED'
ORDER BY o.order_date DESC;

-- ----------------------------------------------------------------------------
-- Scenario 8: Aggregated Order Summary by Category (Multi-Table Aggregation)
-- Demonstrates: Multi-level join with GROUP BY and rollup totals
-- ----------------------------------------------------------------------------
SELECT c.category_name,
       COUNT(DISTINCT o.order_id) AS orders_count,
       SUM(oi.quantity) AS total_units_sold,
       ROUND(SUM(oi.line_total), 2) AS gross_sales
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'COMPLETED'
GROUP BY c.category_name
ORDER BY gross_sales DESC;
