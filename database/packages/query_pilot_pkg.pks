-- ============================================================================
-- Package: QUERY_PILOT_PKG (Specification)
-- Purpose: Encapsulates database-side investigation state transitions, resolution
--          criteria enforcement, and timeline audit logging.
-- Transaction Owner: Caller owns transaction boundary (procedures do not commit).
-- ============================================================================

CREATE OR REPLACE PACKAGE QUERY_PILOT_PKG AS

    -- Custom Exception definitions
    e_invalid_transition    EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_invalid_transition, -20001);

    e_unmet_resolution_req  EXCEPTION;
    PRAGMA EXCEPTION_INIT(e_unmet_resolution_req, -20002);

    /*
     * Purpose: Transition investigation to a new status and record audit log entry.
     * Inputs:
     *   p_investigation_id - ID of the investigation to transition
     *   p_new_status       - Target status ('INVESTIGATING', 'FIX_PROPOSED', 'VALIDATION_REQUIRED', 'RESOLVED', 'CLOSED_INCONCLUSIVE')
     *   p_notes            - Optional transition or verification remarks
     * Validation:
     *   - Cannot resolve an investigation without root cause and verification notes.
     * Exceptions:
     *   - -20001: Invalid status transition
     *   - -20002: Resolution requirements not satisfied
     * Transaction: Caller issues COMMIT or ROLLBACK.
     */
    PROCEDURE transition_status (
        p_investigation_id IN VARCHAR2,
        p_new_status       IN VARCHAR2,
        p_notes            IN VARCHAR2 DEFAULT NULL
    );

    /*
     * Purpose: Record an investigation timeline event in QUERY_PILOT_AUDIT_LOG.
     * Inputs:
     *   p_investigation_id - Associated investigation ID
     *   p_event_type       - Event classification ('CREATED', 'QUERY_RUN', 'PLAN_ANALYSED', etc.)
     *   p_description      - Plain-text description of the event
     */
    PROCEDURE record_audit_event (
        p_investigation_id IN VARCHAR2,
        p_event_type       IN VARCHAR2,
        p_description      IN VARCHAR2
    );

END QUERY_PILOT_PKG;
/
