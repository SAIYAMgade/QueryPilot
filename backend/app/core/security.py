"""SQL Security Guardrails and Defense-in-Depth Validation.

Ensures only permitted, read-only SELECT queries can be executed.
Rejects all DML, DDL, DCL, TCL, multi-statement payloads, and dangerous PL/SQL blocks.
"""

import re
from typing import Tuple, List, Optional
import sqlparse
from sqlparse.sql import Statement, Token
from sqlparse.tokens import Keyword, DML, DDL, Punctuation

from app.core.exceptions import SecurityViolationError, StatementValidationError
from app.core.logging import logger

# Explicitly blocked top-level or embedded keywords
DISALLOWED_KEYWORDS = {
    # DML
    "INSERT", "UPDATE", "DELETE", "MERGE", "UPSERT",
    # DDL
    "CREATE", "ALTER", "DROP", "TRUNCATE", "RENAME", "COMMENT",
    # DCL / Admin
    "GRANT", "REVOKE", "AUDIT", "NOAUDIT",
    # TCL
    "COMMIT", "ROLLBACK", "SAVEPOINT", "SET TRANSACTION",
    # Session / System
    "ALTER SYSTEM", "ALTER SESSION", "SHUTDOWN", "STARTUP",
    # Dangerous Execution
    "EXECUTE", "EXEC", "CALL", "DECLARE", "BEGIN",
    # File / Network / Dangerous Oracle Packages
    "UTL_FILE", "UTL_HTTP", "UTL_TCP", "UTL_SMTP", "DBMS_SCHEDULER",
    "DBMS_LOB.LOADFROMFILE", "DBMS_SYS_SQL", "DBMS_JAVA", "DBMS_BACKUP_RESTORE"
}

DISALLOWED_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(kw) for kw in sorted(DISALLOWED_KEYWORDS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE
)


def sanitize_sql(sql: str) -> str:
    """Trim whitespace and trailing semicolons safely for driver execution."""
    cleaned = sql.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    return cleaned


def validate_read_only_query(sql_text: str) -> str:
    """
    Validate that the given SQL string is a single, safe, read-only SELECT statement.
    
    Raises:
        StatementValidationError: If SQL is empty or syntactically invalid.
        SecurityViolationError: If SQL contains forbidden keywords, multiple statements, or destructive intent.
    
    Returns:
        Sanitized single-statement SQL string ready for execution.
    """
    if not sql_text or not sql_text.strip():
        raise StatementValidationError("SQL query text cannot be empty.")

    raw_sql = sql_text.strip()

    # Step 1: Detect multiple statements via sqlparse
    statements = [stmt for stmt in sqlparse.split(raw_sql) if stmt.strip()]
    if len(statements) > 1:
        logger.warning("Rejected multi-statement execution attempt: %d statements detected", len(statements))
        raise SecurityViolationError(
            "Multi-statement execution is strictly prohibited. Exactly one SELECT statement is permitted."
        )

    parsed_list = sqlparse.parse(raw_sql)
    if not parsed_list or len(parsed_list) == 0:
        raise StatementValidationError("Failed to parse SQL statement.")

    stmt: Statement = parsed_list[0]

    # Step 2: Strip comments and extract meaningful tokens to inspect the statement type
    non_ws_tokens: List[Token] = [
        t for t in stmt.flatten()
        if not t.is_whitespace and t.ttype not in (sqlparse.tokens.Comment, sqlparse.tokens.Comment.Single, sqlparse.tokens.Comment.Multiline)
    ]

    if not non_ws_tokens:
        raise StatementValidationError("Query contains only comments or whitespace.")

    first_token_val = non_ws_tokens[0].value.upper()

    # Must start with SELECT or WITH (Common Table Expressions)
    if first_token_val not in ("SELECT", "WITH"):
        logger.warning("Security violation: Rejected non-SELECT leading token '%s'", first_token_val)
        raise SecurityViolationError(
            f"Only read-only SELECT or WITH statements are allowed. Found: '{first_token_val}'"
        )

    # Step 3: Check for semicolon in the middle of the statement (SQL smuggling attempt)
    # Check if a punctuation semicolon exists before the end of the non-whitespace tokens
    for i, tok in enumerate(non_ws_tokens[:-1]):
        if tok.ttype is Punctuation and tok.value == ";":
            raise SecurityViolationError(
                "Semicolon detected within the query body. Semicolons are only permitted at the very end of a statement."
            )

    # Step 4: Scan statement text (without comments) against disallowed keywords
    # Flatten without comments for rigorous keyword matching
    code_only_text = " ".join(t.value for t in non_ws_tokens)
    forbidden_match = DISALLOWED_PATTERN.search(code_only_text)
    if forbidden_match:
        matched_kw = forbidden_match.group(0).upper()
        # Allow SELECT ... FOR UPDATE? NO: FOR UPDATE locks rows and modifies lock state!
        if matched_kw in ("UPDATE", "DELETE", "INSERT", "MERGE", "DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"):
            logger.warning("Security violation: Disallowed keyword detected '%s'", matched_kw)
            raise SecurityViolationError(
                f"Disallowed operation detected: '{matched_kw}'. QueryPilot only permits read-only SELECT queries."
            )
        elif matched_kw in ("EXECUTE", "EXEC", "CALL", "BEGIN", "DECLARE"):
            logger.warning("Security violation: PL/SQL execution detected '%s'", matched_kw)
            raise SecurityViolationError(
                f"PL/SQL block execution is not permitted in read-only query mode: '{matched_kw}'"
            )
        elif any(pkg in matched_kw for pkg in ("UTL_", "DBMS_")):
            logger.warning("Security violation: Restricted package call detected '%s'", matched_kw)
            raise SecurityViolationError(
                f"Reference to restricted system package is blocked: '{matched_kw}'"
            )

    # Step 5: Check for SELECT ... FOR UPDATE (Row locking construct)
    if re.search(r"\bFOR\s+UPDATE\b", code_only_text, re.IGNORECASE):
        raise SecurityViolationError("SELECT ... FOR UPDATE is rejected because it acquires row exclusive locks.")

    # Step 6: Return sanitized single query
    return sanitize_sql(raw_sql)
