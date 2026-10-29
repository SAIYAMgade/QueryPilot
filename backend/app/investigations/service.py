"""Investigation Lifecycle Service with Workflow Resolution Verification."""

from app.core.exceptions import InvestigationError
from app.schemas.investigation import (
    InvestigationResponse, InvestigationCreate, InvestigationUpdate, InvestigationStatus
)
from app.investigations.repository import (
    create_investigation, update_investigation, get_investigation_by_id, get_all_investigations, add_timeline_event
)


def validate_resolution_criteria(inv: InvestigationResponse, update_data: InvestigationUpdate):
    """
    Enforce strict resolution criteria before marking an investigation as RESOLVED.
    Requirements:
    1. A documented root cause explanation or limitation.
    2. A proposed or completed correction.
    3. Verification notes or evidence.
    """
    if update_data.status == InvestigationStatus.RESOLVED:
        effective_root_cause = update_data.root_cause_explanation or inv.root_cause_explanation
        effective_proposed_fix = update_data.proposed_fix or inv.proposed_fix
        effective_verification = update_data.verification_notes or inv.verification_notes

        missing_criteria = []
        if not effective_root_cause or len(effective_root_cause.strip()) < 10:
            missing_criteria.append("Documented root cause explanation (minimum 10 characters)")
        if not effective_proposed_fix or len(effective_proposed_fix.strip()) < 5:
            missing_criteria.append("Proposed or completed fix description")
        if not effective_verification or len(effective_verification.strip()) < 10:
            missing_criteria.append("Verification evidence or benchmark test notes")

        if missing_criteria:
            raise InvestigationError(
                f"Cannot mark investigation as RESOLVED. Missing resolution criteria: {'; '.join(missing_criteria)}. "
                "Investigations must be backed by documented evidence or closed as CLOSED_INCONCLUSIVE.",
                details={"missing": missing_criteria}
            )


def update_investigation_with_validation(inv_id: str, data: InvestigationUpdate) -> InvestigationResponse:
    """Validate status transitions and update investigation."""
    inv = get_investigation_by_id(inv_id)
    if not inv:
        raise KeyError(f"Investigation {inv_id} not found")

    validate_resolution_criteria(inv, data)
    return update_investigation(inv_id, data)
