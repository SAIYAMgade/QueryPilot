"""Unit tests for Investigation State Machine and Resolution Criteria."""

import pytest
from app.schemas.investigation import (
    InvestigationCreate, InvestigationUpdate, InvestigationStatus, InvestigationSeverity
)
from app.investigations.repository import create_investigation, get_investigation_by_id
from app.investigations.service import update_investigation_with_validation
from app.core.exceptions import InvestigationError


def test_create_and_retrieve_investigation():
    data = InvestigationCreate(
        title="Excessive I/O on Monthly Invoice Generation",
        description="Invoice query is taking 45 seconds during end-of-month processing.",
        category="PERFORMANCE",
        severity=InvestigationSeverity.HIGH,
        initial_hypothesis="Missing index on PAYMENT_STATUS"
    )
    inv = create_investigation(data)
    assert inv.id.startswith("INV-2025-")
    assert inv.status == InvestigationStatus.OPEN
    assert len(inv.timeline) >= 1
    assert inv.timeline[0].event_type == "CREATED"

    fetched = get_investigation_by_id(inv.id)
    assert fetched is not None
    assert fetched.title == data.title


def test_reject_resolution_without_required_evidence():
    data = InvestigationCreate(
        title="Unverified Index Test",
        description="Testing resolution criteria guardrails",
        category="PERFORMANCE"
    )
    inv = create_investigation(data)

    # Attempting to mark as RESOLVED with empty root cause and verification notes
    with pytest.raises(InvestigationError) as exc_info:
        update_investigation_with_validation(inv.id, InvestigationUpdate(
            status=InvestigationStatus.RESOLVED
        ))
    assert "Missing resolution criteria" in str(exc_info.value)


def test_successful_resolution_with_verified_evidence():
    data = InvestigationCreate(
        title="Verified Index Optimization",
        description="Resolving with complete evidence",
        category="PERFORMANCE"
    )
    inv = create_investigation(data)

    updated = update_investigation_with_validation(inv.id, InvestigationUpdate(
        status=InvestigationStatus.RESOLVED,
        root_cause_explanation="Full table scan was executed on ORDERS table due to unindexed ORDER_DATE column.",
        proposed_fix="Create index IDX_ORDERS_DATE on ORDERS(ORDER_DATE).",
        verification_notes="Ran 5 benchmark runs: median latency improved from 8.4ms to 1.9ms with confirmed result equivalence."
    ))

    assert updated.status == InvestigationStatus.RESOLVED
    assert updated.resolved_at is not None
    timeline_types = [evt.event_type for evt in updated.timeline]
    assert "STATUS_CHANGE" in timeline_types
