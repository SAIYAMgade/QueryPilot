-- ============================================================================
-- Package Body: QUERY_PILOT_PKG
-- Purpose: Implementation of database-side investigation state machine
-- ============================================================================

CREATE OR REPLACE PACKAGE BODY QUERY_PILOT_PKG AS

    PROCEDURE record_audit_event (
        p_investigation_id IN VARCHAR2,
        p_event_type       IN VARCHAR2,
        p_description      IN VARCHAR2
    ) IS
    BEGIN
        INSERT INTO QUERY_PILOT_AUDIT_LOG (
            INVESTIGATION_ID,
            EVENT_TYPE,
            EVENT_DESCRIPTION,
            EVENT_TIMESTAMP,
            USER_IDENTITY
        ) VALUES (
            p_investigation_id,
            p_event_type,
            p_description,
            SYSTIMESTAMP,
            USER
        );
    END record_audit_event;

    PROCEDURE transition_status (
        p_investigation_id IN VARCHAR2,
        p_new_status       IN VARCHAR2,
        p_notes            IN VARCHAR2 DEFAULT NULL
    ) IS
        v_current_status VARCHAR2(30);
        v_root_cause     VARCHAR2(4000);
        v_verification   VARCHAR2(4000);
    BEGIN
        -- Query existing investigation record
        SELECT STATUS, ROOT_CAUSE, VERIFICATION_NOTES
        INTO v_current_status, v_root_cause, v_verification
        FROM QUERY_PILOT_INVESTIGATIONS
        WHERE INVESTIGATION_ID = p_investigation_id;

        -- Check resolution requirements if transitioning to RESOLVED
        IF p_new_status = 'RESOLVED' THEN
            IF v_root_cause IS NULL OR LENGTH(TRIM(v_root_cause)) < 10 THEN
                RAISE_APPLICATION_ERROR(-20002, 'Cannot resolve investigation: Documented root cause is required.');
            END IF;
            IF v_verification IS NULL OR LENGTH(TRIM(v_verification)) < 10 THEN
                RAISE_APPLICATION_ERROR(-20002, 'Cannot resolve investigation: Verification evidence notes are required.');
            END IF;
        END IF;

        -- Update investigation status
        UPDATE QUERY_PILOT_INVESTIGATIONS
        SET STATUS = p_new_status,
            UPDATED_AT = SYSTIMESTAMP,
            RESOLVED_AT = CASE WHEN p_new_status IN ('RESOLVED', 'CLOSED_INCONCLUSIVE') THEN SYSTIMESTAMP ELSE NULL END
        WHERE INVESTIGATION_ID = p_investigation_id;

        -- Record audit event in transaction
        record_audit_event(
            p_investigation_id => p_investigation_id,
            p_event_type       => 'STATUS_TRANSITION',
            p_description      => 'Transitioned from ' || v_current_status || ' to ' || p_new_status || 
                                  CASE WHEN p_notes IS NOT NULL THEN ' Notes: ' || p_notes ELSE '' END
        );

    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20001, 'Investigation with ID ' || p_investigation_id || ' does not exist.');
    END transition_status;

END QUERY_PILOT_PKG;
/
