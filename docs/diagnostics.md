# Oracle Error Diagnostics Knowledge Base

QueryPilot includes a curated diagnostic engine that maps Oracle runtime error codes to plain-English explanations, kernel mechanisms, recommended catalog checks, and remediation examples.

---

## 1. Curated Error Catalog

### ORA-00942: table or view does not exist
- **Category**: `OBJECT_NOT_FOUND_OR_INACCESSIBLE`
- **Root Cause**: The data dictionary resolver could not locate the table in the current schema or public synonyms, or the executing user lacks `SELECT` privileges. Oracle intentionally returns ORA-00942 for missing privileges to prevent unauthorized schema enumeration.
- **Recommended Checks**:
  ```sql
  SELECT table_name FROM all_tables WHERE table_name = UPPER('table_name');
  SELECT table_name, privilege FROM user_tab_privs WHERE table_name = UPPER('table_name');
  ```
- **Remediation**: Prefix table with owner (`<owner>.<table_name>`) or grant `SELECT`.

### ORA-00904: invalid identifier
- **Category**: `INVALID_IDENTIFIER`
- **Root Cause**: A column name or expression does not exist in any joined table. Often caused by enclosing string literals in double quotes (e.g. `WHERE status = "ACTIVE"`, where Oracle treats `"ACTIVE"` as a column name).
- **Recommended Checks**:
  ```sql
  SELECT column_name, data_type FROM all_tab_columns WHERE table_name = UPPER('table_name');
  ```
- **Remediation**: Use single quotes for string literals (`'ACTIVE'`) and verify column spelling.

### ORA-00001: unique constraint violated
- **Category**: `UNIQUE_CONSTRAINT_VIOLATION`
- **Root Cause**: Attempted to insert or update a record that duplicates an existing key in a unique index or primary key constraint.
- **Recommended Checks**:
  ```sql
  SELECT constraint_name, table_name, constraint_type FROM all_constraints WHERE constraint_name = UPPER('constraint_name');
  ```
- **Remediation**: Utilize Oracle `MERGE INTO ... WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT`.

### ORA-01722: invalid number
- **Category**: `TYPE_CONVERSION_ERROR`
- **Root Cause**: Implicit or explicit conversion from `VARCHAR2` to `NUMBER` failed because string contained non-numeric characters.
- **Recommended Checks**:
  ```sql
  SELECT col FROM tbl WHERE NOT REGEXP_LIKE(col, '^-?[0-9]+(\.[0-9]+)?$');
  ```
- **Remediation**: Use `TO_NUMBER(col DEFAULT NULL ON CONVERSION ERROR)` in Oracle 12.2+.

### ORA-00933: SQL command not properly ended
- **Category**: `SYNTAX_ERROR`
- **Root Cause**: Encountered syntax invalid in Oracle SQL, such as using MySQL/Postgres `LIMIT n` instead of Oracle's `FETCH FIRST n ROWS ONLY`.
- **Remediation**: Use standard Oracle clause: `ORDER BY col DESC FETCH FIRST 10 ROWS ONLY`.
