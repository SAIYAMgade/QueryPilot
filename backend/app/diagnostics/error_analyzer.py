"""Oracle Error Categorization and Diagnostic Knowledge Base Engine.

Categorizes Oracle ORA- error codes, provides curated diagnostic explanations,
suggests checks, and separates confirmed root causes from hypotheses.
"""

import re
import uuid
from typing import Dict, Any, List, Optional
from app.schemas.diagnostic import ErrorAnalysisResponse, KnowledgeBaseEntry

# Curated Oracle Diagnostic Knowledge Base
KNOWLEDGE_BASE: Dict[str, KnowledgeBaseEntry] = {
    "ORA-00942": KnowledgeBaseEntry(
        oracle_code="ORA-00942",
        category="OBJECT_NOT_FOUND_OR_INACCESSIBLE",
        official_title="table or view does not exist",
        plain_english="Oracle cannot find the referenced table, view, or synonym in the current schema or public namespace, or the executing user lacks SELECT permission on it.",
        common_scenarios=[
            "Typo in the table name (e.g., 'CUSTOMER' instead of 'CUSTOMERS')",
            "Table belongs to another schema and was not prefixed with '<schema>.<table_name>'",
            "Executing user lacks SELECT grant on the specified table or view",
            "Table was created with case-sensitive quoted identifier (e.g., CREATE TABLE \"my_table\")"
        ],
        root_cause_analysis="Oracle's data dictionary resolver searches the executing user's private schema first, then public synonyms. If neither matches or permissions are lacking, Oracle returns ORA-00942 deliberately without revealing whether the table exists to prevent unauthorized schema enumeration.",
        recommended_checks=[
            "Verify table spelling against ALL_TABLES or USER_TABLES: SELECT table_name FROM user_tables WHERE table_name = UPPER('table_name');",
            "Check if table is owned by another schema: SELECT owner, table_name FROM all_tables WHERE table_name = UPPER('table_name');",
            "Check current user grants: SELECT table_name, privilege FROM user_tab_privs WHERE table_name = UPPER('table_name');",
            "Check whether private or public synonyms exist: SELECT synonym_name, table_owner, table_name FROM all_synonyms WHERE synonym_name = UPPER('table_name');"
        ],
        resolution_steps=[
            "Correct table spelling or prefix the table with the owner schema: <owner>.<table_name>",
            "Have the DBA grant SELECT on <owner>.<table_name> to the application user",
            "Create a synonym if cross-schema transparency is desired: CREATE SYNONYM table_name FOR owner.table_name"
        ],
        sample_problematic_sql="SELECT * FROM customer_orders WHERE status = 'PENDING';",
        sample_corrected_sql="SELECT * FROM qp_app_user.orders WHERE status = 'PENDING';"
    ),
    "ORA-00904": KnowledgeBaseEntry(
        oracle_code="ORA-00904",
        category="INVALID_IDENTIFIER",
        official_title="invalid identifier",
        plain_english="A column name, alias, or expression specified in the SELECT list, WHERE clause, or ORDER BY clause does not exist in any referenced table.",
        common_scenarios=[
            "Typo in column name (e.g. 'order_datetime' instead of 'order_date')",
            "Table alias ambiguity or omitted alias prefix in multi-table join",
            "Using a column alias in the WHERE clause (which is evaluated before SELECT)",
            "Enclosing a string literal in double quotes instead of single quotes"
        ],
        root_cause_analysis="In Oracle SQL, double quotes denote case-sensitive identifiers, whereas single quotes denote string literals. Writing WHERE status = \"ACTIVE\" causes Oracle to look for a column named ACTIVE.",
        recommended_checks=[
            "Inspect column definitions in ALL_TAB_COLUMNS: SELECT column_name, data_type FROM all_tab_columns WHERE table_name = UPPER('table_name');",
            "Ensure string literals use single quotes: 'ACTIVE' not \"ACTIVE\"",
            "Verify that column aliases defined in SELECT are not referenced in the WHERE clause (use a subquery/CTE or repeat the expression)"
        ],
        resolution_steps=[
            "Fix column name spelling to match the physical schema column",
            "Change double quotes to single quotes for literal values",
            "Move alias references from WHERE to HAVING or wrap within a WITH CTE block"
        ],
        sample_problematic_sql="SELECT order_id, total_amount FROM orders WHERE \"status\" = \"COMPLETED\";",
        sample_corrected_sql="SELECT order_id, total_amount FROM orders WHERE status = 'COMPLETED';"
    ),
    "ORA-00001": KnowledgeBaseEntry(
        oracle_code="ORA-00001",
        category="UNIQUE_CONSTRAINT_VIOLATION",
        official_title="unique constraint violated",
        plain_english="An attempt was made to insert or update a record with a key that already exists in a unique index or primary key constraint.",
        common_scenarios=[
            "Inserting a customer with an email address that is already registered",
            "Re-executing an INSERT without checking primary key sequence generation",
            "Batch load with duplicate rows within the source dataset"
        ],
        root_cause_analysis="Oracle's B-tree unique index prevents duplicate entries across the indexed columns. The error message indicates the exact constraint name violated.",
        recommended_checks=[
            "Identify the violated constraint: SELECT constraint_name, table_name, constraint_type FROM all_constraints WHERE constraint_name = UPPER('constraint_name');",
            "Query the conflicting existing row: SELECT * FROM <table> WHERE <unique_column> = :value;"
        ],
        resolution_steps=[
            "Use MERGE INTO ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT (UPSERT pattern)",
            "Ensure primary key generation utilizes an Oracle IDENTITY column or SEQUENCE.NEXTVAL"
        ]
    ),
    "ORA-01722": KnowledgeBaseEntry(
        oracle_code="ORA-01722",
        category="TYPE_CONVERSION_ERROR",
        official_title="invalid number",
        plain_english="Oracle attempted an implicit or explicit conversion from a character string to a number, but the string contained non-numeric characters.",
        common_scenarios=[
            "Comparing a NUMBER column with a string containing letters, currency symbols, or commas",
            "Implicit data type conversion where Oracle converts VARCHAR2 to NUMBER due to operator precedence",
            "Null or empty string treated as invalid number in older conversion logic"
        ],
        root_cause_analysis="In expressions combining NUMBER and VARCHAR2 (e.g. number_col = varchar_col), Oracle converts VARCHAR2 to NUMBER according to type precedence. If a single row contains a non-numeric string, ORA-01722 is thrown at runtime during execution.",
        recommended_checks=[
            "Identify non-numeric values in character column: SELECT col FROM tbl WHERE NOT REGEXP_LIKE(col, '^-?[0-9]+(\\.[0-9]+)?$');",
            "Check explicit CAST or TO_NUMBER calls in the query"
        ],
        resolution_steps=[
            "Use TO_NUMBER with DEFAULT ON CONVERSION ERROR in Oracle 12.2+: TO_NUMBER(col DEFAULT NULL ON CONVERSION ERROR)",
            "Align data types between join keys and filter predicates to avoid implicit conversions"
        ],
        sample_problematic_sql="SELECT * FROM products WHERE unit_price = 'N/A';",
        sample_corrected_sql="SELECT * FROM products WHERE unit_price = 89.99;"
    ),
    "ORA-00933": KnowledgeBaseEntry(
        oracle_code="ORA-00933",
        category="SYNTAX_ERROR",
        official_title="SQL command not properly ended",
        plain_english="The SQL statement contains syntax that is invalid in Oracle, misplaced clauses, or clauses from other SQL dialects (such as LIMIT instead of FETCH FIRST).",
        common_scenarios=[
            "Using MySQL/PostgreSQL 'LIMIT n' instead of Oracle's 'FETCH FIRST n ROWS ONLY'",
            "Order of clauses is wrong (e.g., HAVING before GROUP BY, or WHERE after GROUP BY)",
            "Unclosed quotes or unmatched parentheses"
        ],
        root_cause_analysis="Oracle SQL parser encountered an unexpected token at the end or within the statement body. Oracle 12c+ supports ANSI standard 'OFFSET n ROWS FETCH NEXT m ROWS ONLY', but does NOT support the MySQL 'LIMIT' keyword.",
        recommended_checks=[
            "Verify clause ordering: SELECT ... FROM ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... FETCH FIRST ...",
            "Check for non-Oracle keywords such as LIMIT, ILIKE, or TOP"
        ],
        resolution_steps=[
            "Replace 'LIMIT n' with 'FETCH FIRST n ROWS ONLY'",
            "Replace 'ILIKE' with 'UPPER(col) LIKE UPPER(pattern)' or REGEXP_LIKE"
        ],
        sample_problematic_sql="SELECT * FROM orders ORDER BY order_date DESC LIMIT 10;",
        sample_corrected_sql="SELECT * FROM orders ORDER BY order_date DESC FETCH FIRST 10 ROWS ONLY;"
    )
}


def extract_oracle_error_code(error_message: str) -> Optional[str]:
    """Extract standard ORA-XXXXX error code from text if present."""
    match = re.search(r"\b(ORA-\d{5})\b", error_message)
    return match.group(1) if match else None


def analyze_oracle_error(
    error_message: str,
    error_code: Optional[str] = None,
    query_text: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None
) -> ErrorAnalysisResponse:
    """Analyze an Oracle SQL error and provide evidence-backed diagnostic guidance."""
    analysis_id = f"err_{uuid.uuid4().hex[:8]}"
    detected_code = error_code or extract_oracle_error_code(error_message) or "ORA-UNKNOWN"

    kb_entry = KNOWLEDGE_BASE.get(detected_code)

    if kb_entry:
        category = kb_entry.category
        likely_causes = kb_entry.common_scenarios
        recommended_checks = kb_entry.recommended_checks
        evidence_status = "CONFIRMED"
    else:
        # Heuristic classification for uncatalogued errors
        if "syntax" in error_message.lower() or "command not properly ended" in error_message.lower():
            category = "SYNTAX_ERROR"
        elif "timeout" in error_message.lower() or "cancel" in error_message.lower():
            category = "TIMEOUT_OR_CANCEL"
        elif "permission" in error_message.lower() or "privilege" in error_message.lower():
            category = "PERMISSION_DENIED"
        elif "connection" in error_message.lower() or "network" in error_message.lower():
            category = "CONNECTION_FAILURE"
        else:
            category = "UNKNOWN_ORACLE_ERROR"

        likely_causes = [
            f"Oracle returned error code {detected_code}. Check Oracle Database documentation for official parameters.",
            "Verify statement syntax, object existence, and user privileges."
        ]
        recommended_checks = [
            f"Review Oracle Database Error Reference for {detected_code}.",
            "Inspect user session privileges and schema object status."
        ]
        evidence_status = "HYPOTHESIS"

    # Contextual hint based on query text
    position_hint = None
    if query_text:
        if detected_code == "ORA-00933" and re.search(r"\bLIMIT\b", query_text, re.IGNORECASE):
            position_hint = "Detected 'LIMIT' keyword in SQL. Oracle uses 'FETCH FIRST <n> ROWS ONLY' for row limiting."
        elif detected_code == "ORA-00904" and re.search(r'="[^"]+"', query_text):
            position_hint = "Detected double-quoted string in comparison. Use single quotes for string literals: 'value'."

    return ErrorAnalysisResponse(
        analysis_id=analysis_id,
        oracle_error_code=detected_code,
        category=category,
        sanitized_message=error_message,
        likely_causes=likely_causes,
        recommended_checks=recommended_checks,
        knowledge_base=kb_entry,
        position_hint=position_hint,
        is_confirmed_cause=(evidence_status == "CONFIRMED"),
        evidence_status=evidence_status
    )
