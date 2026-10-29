"""Persistent Repository for Query Investigations and Timeline Audits."""

import uuid
from typing import Dict, List, Optional
from datetime import datetime, timezone

from app.schemas.investigation import (
    InvestigationResponse, InvestigationCreate, InvestigationUpdate, InvestigationStatus,
    InvestigationSeverity, TimelineEvent
)

# In-memory storage for investigations (backed by pre-seeded realistic cases)
_investigations: Dict[str, InvestigationResponse] = {}


def init_default_investigations():
    """Seed realistic investigation case studies."""
    if _investigations:
        return

    # Case 1: Slow Order History Report
    inv1_id = "INV-2025-001"
    now = datetime.now(timezone.utc)
    _investigations[inv1_id] = InvestigationResponse(
        id=inv1_id,
        title="Slow Customer Order History Report (Full Table Scan on Orders)",
        description="The customer portal order history query is experiencing high latency when filtering orders placed in Q3 2025.",
        category="PERFORMANCE",
        severity=InvestigationSeverity.HIGH,
        status=InvestigationStatus.RESOLVED,
        initial_hypothesis="Filtering by ORDER_DATE without a date-bounded index is causing an unselective Full Table Scan on ORDERS.",
        baseline_sql="SELECT o.order_id, o.order_date, o.total_amount, c.email FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_date >= '2025-06-01' ORDER BY o.order_date DESC FETCH FIRST 50 ROWS ONLY",
        candidate_sql="SELECT /*+ INDEX(o IDX_ORDERS_DATE) */ o.order_id, o.order_date, o.total_amount, c.email FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_date >= '2025-06-01' ORDER BY o.order_date DESC FETCH FIRST 50 ROWS ONLY",
        root_cause_explanation="Optimizer selected TABLE ACCESS FULL on ORDERS. Adding an index on (CUSTOMER_ID, ORDER_DATE) or utilizing IDX_ORDERS_DATE converts the access path to INDEX RANGE SCAN.",
        proposed_fix="Create composite index on ORDERS(ORDER_DATE, ORDER_ID) to support index-only range scans for date-filtered order reporting.",
        verification_notes="Benchmark demonstrated 3.4x faster median latency (2.1ms vs 7.2ms) with verified result equivalence across all returned rows.",
        timeline=[
            TimelineEvent(
                event_id="evt_01",
                event_type="CREATED",
                description="Investigation opened by database team following latency alerts on customer portal.",
                timestamp=now
            ),
            TimelineEvent(
                event_id="evt_02",
                event_type="PLAN_GENERATED",
                description="Generated EXPLAIN PLAN for baseline query. Observed TABLE ACCESS FULL on ORDERS with cost 18.",
                timestamp=now
            ),
            TimelineEvent(
                event_id="evt_03",
                event_type="COMPARISON_RUN",
                description="Query comparison benchmark executed across 5 runs. Equivalence confirmed (50/50 rows matching multiset).",
                timestamp=now
            ),
            TimelineEvent(
                event_id="evt_04",
                event_type="STATUS_CHANGE",
                description="Status transitioned to RESOLVED with verified benchmark evidence.",
                timestamp=now
            )
        ],
        created_at=now,
        updated_at=now,
        resolved_at=now
    )

    # Case 2: Implicit Type Conversion Error ORA-01722
    inv2_id = "INV-2025-002"
    _investigations[inv2_id] = InvestigationResponse(
        id=inv2_id,
        title="Batch Pricing Report Failing with ORA-01722: invalid number",
        description="Nightly pricing reconciliation script threw ORA-01722 after marketing imported legacy product codes.",
        category="ERROR",
        severity=InvestigationSeverity.CRITICAL,
        status=InvestigationStatus.FIX_PROPOSED,
        initial_hypothesis="A string filter comparing against UNIT_PRICE contains alphabetic prefix or formatting comma.",
        baseline_sql="SELECT product_id, sku, unit_price FROM products WHERE unit_price = '89.99'",
        candidate_sql="SELECT product_id, sku, unit_price FROM products WHERE unit_price = 89.99",
        related_error_code="ORA-01722",
        root_cause_explanation="Query was passing string literal 'N/A' in parameterized SKU unit price lookups, triggering implicit VARCHAR2 to NUMBER conversion failure.",
        proposed_fix="Pass numeric parameters as native NUMBER bind variables and validate input in application API before query submission.",
        timeline=[
            TimelineEvent(
                event_id="evt_11",
                event_type="CREATED",
                description="Investigation logged following batch reconciliation job failure.",
                timestamp=now
            ),
            TimelineEvent(
                event_id="evt_12",
                event_type="ERROR_CAPTURED",
                description="Captured ORA-01722 error in diagnostic module with position hint on predicate comparison.",
                timestamp=now
            )
        ],
        created_at=now,
        updated_at=now
    )


init_default_investigations()


def get_all_investigations() -> List[InvestigationResponse]:
    """Return all investigations sorted by last update."""
    return sorted(_investigations.values(), key=lambda x: x.updated_at, reverse=True)


def get_investigation_by_id(inv_id: str) -> Optional[InvestigationResponse]:
    """Retrieve single investigation by ID."""
    return _investigations.get(inv_id)


def create_investigation(data: InvestigationCreate) -> InvestigationResponse:
    """Create and persist a new investigation."""
    inv_id = f"INV-2025-{uuid.uuid4().hex[:4].upper()}"
    now = datetime.now(timezone.utc)
    initial_event = TimelineEvent(
        event_id=f"evt_{uuid.uuid4().hex[:6]}",
        event_type="CREATED",
        description=f"Investigation created: '{data.title}'",
        timestamp=now
    )
    inv = InvestigationResponse(
        id=inv_id,
        title=data.title,
        description=data.description,
        category=data.category,
        severity=data.severity,
        status=InvestigationStatus.OPEN,
        initial_hypothesis=data.initial_hypothesis,
        baseline_query_id=data.baseline_query_id,
        baseline_sql=data.baseline_sql,
        related_error_code=data.related_error_code,
        timeline=[initial_event],
        created_at=now,
        updated_at=now
    )
    _investigations[inv_id] = inv
    return inv


def update_investigation(inv_id: str, data: InvestigationUpdate) -> InvestigationResponse:
    """Update investigation fields and append status change events."""
    inv = _investigations.get(inv_id)
    if not inv:
        raise KeyError(f"Investigation {inv_id} not found")

    now = datetime.now(timezone.utc)
    # Check status change
    if data.status and data.status != inv.status:
        inv.timeline.append(TimelineEvent(
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            event_type="STATUS_CHANGE",
            description=f"Status transitioned from {inv.status.value} to {data.status.value}",
            timestamp=now
        ))
        inv.status = data.status
        if data.status in (InvestigationStatus.RESOLVED, InvestigationStatus.CLOSED_INCONCLUSIVE):
            inv.resolved_at = now

    if data.title is not None:
        inv.title = data.title
    if data.description is not None:
        inv.description = data.description
    if data.severity is not None:
        inv.severity = data.severity
    if data.initial_hypothesis is not None:
        inv.initial_hypothesis = data.initial_hypothesis
    if data.root_cause_explanation is not None:
        inv.root_cause_explanation = data.root_cause_explanation
    if data.proposed_fix is not None:
        inv.proposed_fix = data.proposed_fix
    if data.verification_notes is not None:
        inv.verification_notes = data.verification_notes
    if data.candidate_sql is not None:
        inv.candidate_sql = data.candidate_sql

    inv.updated_at = now
    return inv


def add_timeline_event(inv_id: str, event_type: str, description: str, metadata: Optional[Dict[str, Any]] = None):
    """Add a timeline event to an investigation."""
    inv = _investigations.get(inv_id)
    if inv:
        event = TimelineEvent(
            event_id=f"evt_{uuid.uuid4().hex[:6]}",
            event_type=event_type,
            description=description,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata or {}
        )
        inv.timeline.append(event)
        inv.updated_at = datetime.now(timezone.utc)
