"""Deterministic Synthetic Retail Data Generator for Oracle Database.

Generates reproducible retail dataset records (Customers, Orders, Items, Payments, Shipments)
with configurable profiles: 'small' (fast local testing) and 'performance' (optimizer cardinality workload).
"""

import sys
import argparse
import random
from datetime import datetime, timedelta
from typing import List, Tuple

PROFILES = {
    "small": {
        "categories": 8,
        "products": 40,
        "customers": 100,
        "orders": 300,
        "items_per_order": (1, 4),
        "seed": 42
    },
    "performance": {
        "categories": 12,
        "products": 250,
        "customers": 1500,
        "orders": 10000,
        "items_per_order": (1, 6),
        "seed": 42
    }
}


def generate_sql_inserts(profile_name: str = "small", output_file: str = "seed_data.sql"):
    cfg = PROFILES.get(profile_name, PROFILES["small"])
    rng = random.Random(cfg["seed"])
    lines: List[str] = [
        "-- ============================================================================",
        f"-- QueryPilot Synthetic Data Seed (Profile: {profile_name}, Seed: {cfg['seed']})",
        f"-- Generated at: {datetime.utcnow().isoformat()}",
        "-- ============================================================================\n",
        "SET DEFINE OFF;",
        "ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS';",
        "ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS';\n"
    ]

    # Categories
    cat_names = [
        "Electronics", "Computers", "Home Office", "Audio", "Photography",
        "Wearables", "Storage", "Gaming", "Networking", "Accessories", "Smart Home", "Printers"
    ][:cfg["categories"]]

    lines.append("-- 1. Categories")
    for i, name in enumerate(cat_names, 1):
        slug = name.lower().replace(" ", "-")
        lines.append(f"INSERT INTO CATEGORIES (CATEGORY_ID, CATEGORY_NAME, SLUG, IS_ACTIVE) VALUES ({i}, '{name}', '{slug}', 1);")

    # Products
    lines.append("\n-- 2. Products")
    prod_bases = [
        ("Ergonomic Keyboard", 89.99, 45.00), ("Wireless Mouse", 34.50, 15.00),
        ("UltraWide Monitor 34in", 499.00, 310.00), ("Noise Cancelling Headphones", 199.99, 90.00),
        ("Thunderbolt 4 Dock", 159.00, 75.00), ("HD Webcam 1080p", 69.99, 28.00),
        ("Standing Desk Mat", 45.00, 18.00), ("Cardioid Microphone", 129.50, 60.00),
        ("External NVMe SSD 1TB", 109.99, 52.00), ("Mechanical Keycaps", 29.99, 10.00),
        ("Smart Fitness Watch", 79.99, 32.00), ("Desk Mousepad XL", 24.99, 8.00)
    ]
    prod_list = []
    p_id = 1
    for cat_id in range(1, cfg["categories"] + 1):
        for base_name, price, cost in prod_bases:
            if p_id > cfg["products"]:
                break
            sku = f"SKU-C{cat_id:02d}-P{p_id:04d}"
            p_name = f"{base_name} Model-{p_id}"
            qty = rng.randint(10, 400)
            lines.append(
                f"INSERT INTO PRODUCTS (PRODUCT_ID, CATEGORY_ID, SKU, PRODUCT_NAME, UNIT_PRICE, COST_PRICE, STOCK_QUANTITY, STATUS) "
                f"VALUES ({p_id}, {cat_id}, '{sku}', '{p_name}', {price}, {cost}, {qty}, 'ACTIVE');"
            )
            prod_list.append((p_id, price))
            p_id += 1

    # Customers
    lines.append("\n-- 3. Customers")
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Sam", "Chris", "Casey", "Riley", "Cameron", "Jesse", "Pat", "Quinn"]
    last_names = ["Chen", "Smith", "Patel", "Garcia", "Johnson", "Kim", "Miller", "Davis", "Wilson", "Martinez"]
    base_date = datetime(2025, 1, 1)

    for c_id in range(1, cfg["customers"] + 1):
        fn = rng.choice(first_names)
        ln = rng.choice(last_names)
        email = f"{fn.lower()}.{ln.lower()}{c_id}@example.com"
        tier = rng.choice(["STANDARD", "STANDARD", "SILVER", "GOLD", "PLATINUM"])
        c_date = (base_date + timedelta(days=rng.randint(0, 300))).strftime("%Y-%m-%d %H:%M:%S")
        lines.append(
            f"INSERT INTO CUSTOMERS (CUSTOMER_ID, FIRST_NAME, LAST_NAME, EMAIL, LOYALTY_TIER, STATUS, CREATED_AT) "
            f"VALUES ({c_id}, '{fn}', '{ln}', '{email}', '{tier}', 'ACTIVE', TO_TIMESTAMP('{c_date}', 'YYYY-MM-DD HH24:MI:SS'));"
        )

    # Orders & Items
    lines.append("\n-- 4. Orders, Order Items, Payments & Shipments")
    order_base = datetime(2025, 3, 1)
    item_id = 1
    pay_id = 1
    ship_id = 1

    for o_id in range(1, cfg["orders"] + 1):
        cust_id = rng.randint(1, cfg["customers"])
        ord_dt = (order_base + timedelta(days=rng.randint(0, 240), hours=rng.randint(0, 23))).strftime("%Y-%m-%d %H:%M:%S")
        status = rng.choice(["COMPLETED", "COMPLETED", "COMPLETED", "SHIPPED", "PROCESSING", "CANCELLED"])
        pay_status = "REFUNDED" if status == "CANCELLED" else ("PAID" if status in ("COMPLETED", "SHIPPED") else "PENDING")
        ship_status = "DELIVERED" if status == "COMPLETED" else ("IN_TRANSIT" if status == "SHIPPED" else "PENDING")

        num_items = rng.randint(cfg["items_per_order"][0], cfg["items_per_order"][1])
        total_amt = 0.0
        item_inserts = []

        for _ in range(num_items):
            pr_id, u_price = rng.choice(prod_list)
            qty = rng.randint(1, 3)
            discount = 0.0 if rng.random() > 0.2 else round(u_price * 0.1, 2)
            line_tot = round((u_price - discount) * qty, 2)
            total_amt += line_tot
            item_inserts.append(
                f"INSERT INTO ORDER_ITEMS (ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, DISCOUNT, LINE_TOTAL) "
                f"VALUES ({item_id}, {o_id}, {pr_id}, {qty}, {u_price}, {discount}, {line_tot});"
            )
            item_id += 1

        total_amt = round(total_amt, 2)
        lines.append(
            f"INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, TOTAL_AMOUNT, STATUS, PAYMENT_STATUS, SHIPPING_STATUS) "
            f"VALUES ({o_id}, {cust_id}, TO_TIMESTAMP('{ord_dt}', 'YYYY-MM-DD HH24:MI:SS'), {total_amt}, '{status}', '{pay_status}', '{ship_status}');"
        )
        lines.extend(item_inserts)

        # Payment
        p_method = rng.choice(["CREDIT_CARD", "PAYPAL", "WIRE_TRANSFER", "APPLE_PAY"])
        lines.append(
            f"INSERT INTO PAYMENTS (PAYMENT_ID, ORDER_ID, PAYMENT_METHOD, AMOUNT, STATUS, TRANSACTION_TIME) "
            f"VALUES ({pay_id}, {o_id}, '{p_method}', {total_amt}, '{'SETTLED' if pay_status == 'PAID' else pay_status}', TO_TIMESTAMP('{ord_dt}', 'YYYY-MM-DD HH24:MI:SS'));"
        )
        pay_id += 1

        # Shipment
        if status in ("COMPLETED", "SHIPPED"):
            carrier = rng.choice(["FEDEX", "UPS", "DHL", "USPS"])
            track = f"TRK-{o_id:06d}-{carrier[:2]}"
            deliv_dt = (datetime.strptime(ord_dt, "%Y-%m-%d %H:%M:%S") + timedelta(days=rng.randint(2, 5))).strftime("%Y-%m-%d %H:%M:%S") if status == "COMPLETED" else "NULL"
            deliv_clause = f"TO_TIMESTAMP('{deliv_dt}', 'YYYY-MM-DD HH24:MI:SS')" if status == "COMPLETED" else "NULL"
            lines.append(
                f"INSERT INTO SHIPMENTS (SHIPMENT_ID, ORDER_ID, CARRIER, TRACKING_NUMBER, SHIPPED_AT, DELIVERED_AT, STATUS) "
                f"VALUES ({ship_id}, {o_id}, '{carrier}', '{track}', TO_TIMESTAMP('{ord_dt}', 'YYYY-MM-DD HH24:MI:SS'), {deliv_clause}, '{ship_status}');"
            )
            ship_id += 1

    lines.append("\nCOMMIT;")
    lines.append("-- Refresh Oracle Optimizer Statistics")
    lines.append("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS(ownname => USER, cascade => TRUE); END;\n/\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Generated {len(lines)} lines of SQL seed data ({profile_name} profile) into '{output_file}'.")


if __name__ == "__main__":
    profile = sys.argv[1] if len(sys.argv) > 1 else "small"
    out = sys.argv[2] if len(sys.argv) > 2 else "database/seed/seed_data.sql"
    generate_sql_inserts(profile, out)
