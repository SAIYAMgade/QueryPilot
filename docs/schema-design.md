# QueryPilot Retail Demonstration Schema Design

QueryPilot includes a deterministic, realistic relational dataset simulating a modern retail operations platform. It demonstrates one-to-many parent-child relationships, status transitions, selective filters, and optimizer access paths.

---

## 1. Entity-Relationship Diagram

```
+------------------+         +--------------------+         +------------------+
|    CATEGORIES    | 1     * |      PRODUCTS      | 1     * |   ORDER_ITEMS    |
|------------------|<-------+|--------------------|<-------+|------------------|
| PK CATEGORY_ID   |         | PK PRODUCT_ID      |         | PK ITEM_ID       |
|    CATEGORY_NAME |         | FK CATEGORY_ID     |         | FK ORDER_ID      |
|    SLUG (UQ)     |         |    SKU (UQ)        |         | FK PRODUCT_ID    |
|    IS_ACTIVE     |         |    UNIT_PRICE      |         |    QUANTITY      |
+------------------+         |    STOCK_QUANTITY  |         |    UNIT_PRICE    |
                             |    STATUS          |         |    LINE_TOTAL    |
                             +--------------------+         +--------+---------+
                                                                     | *
                                                                     |
+------------------+         +--------------------+                  | 1
|    CUSTOMERS     | 1     * |       ORDERS       | <----------------+
|------------------|<-------+|--------------------+
| PK CUSTOMER_ID   |         | PK ORDER_ID        | 1     * +------------------+
|    FIRST_NAME    |         | FK CUSTOMER_ID     |-------->|     PAYMENTS     |
|    LAST_NAME     |         |    ORDER_DATE (IDX)|         |------------------|
|    EMAIL (UQ)    |         |    TOTAL_AMOUNT    |         | PK PAYMENT_ID    |
|    LOYALTY_TIER  |         |    STATUS (IDX)    |         | FK ORDER_ID      |
|    CREATED_AT    |         |    PAYMENT_STATUS  |         |    AMOUNT        |
+--------+---------+         +---------+----------+         |    STATUS        |
         | 1                           | 1                  +------------------+
         |                             |
         | *                           | *
+--------v---------+         +---------v----------+
|  SUPPORT_TICKETS |         |     SHIPMENTS      |
|------------------|         |--------------------|
| PK TICKET_ID     |         | PK SHIPMENT_ID     |
| FK CUSTOMER_ID   |         | FK ORDER_ID        |
| FK ORDER_ID      |         |    TRACKING_NO (UQ)|
|    SUBJECT       |         |    STATUS          |
+------------------+         +--------------------+
```

---

## 2. Table Specifications

1. **CATEGORIES**: 8 taxonomy classifications (`Electronics`, `Computers`, `Audio`, etc.).
2. **PRODUCTS**: 40+ catalog items with unit prices, cost prices, and stock inventory.
3. **CUSTOMERS**: 100 customer records across loyalty tiers (`STANDARD`, `SILVER`, `GOLD`, `PLATINUM`).
4. **ORDERS**: 300 orders with temporal spread across 2025, total amounts, and fulfillment statuses (`COMPLETED`, `SHIPPED`, `PROCESSING`, `CANCELLED`).
5. **ORDER_ITEMS**: 800+ line items with quantities, discounts, and line totals.
6. **PAYMENTS**: Financial transactions linked 1:1 or 1:M to orders.
7. **SHIPMENTS**: Logistics carrier tracking records (`FEDEX`, `UPS`, `DHL`).
8. **SUPPORT_TICKETS**: Customer service tickets linked to customers and specific order IDs.
9. **QUERY_PILOT_INVESTIGATIONS**: Application table persisting problem statements, hypotheses, baseline/candidate SQL, root causes, and verification notes.
10. **QUERY_PILOT_AUDIT_LOG**: Immutable event timeline capturing all investigation lifecycle actions.
