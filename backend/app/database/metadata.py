"""Oracle Data Dictionary Metadata Inspector.

Queries ALL_TABLES, ALL_TAB_COLUMNS, ALL_CONSTRAINTS, ALL_INDEXES, and ALL_IND_COLUMNS
using least-privilege view access without requiring SYSDBA.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import oracledb
from app.core.logging import logger
from app.core.exceptions import OracleConnectionError, ObjectNotFoundError
from app.schemas.schema_explorer import (
    TableSummary, TableDetail, ColumnMetadata, IndexMetadata, ConstraintMetadata, Relationship
)


def get_tables_oracle(conn: oracledb.Connection, owner_filter: Optional[str] = None) -> List[TableSummary]:
    """Retrieve all accessible tables and their estimated row counts."""
    cursor = conn.cursor()
    try:
        sql = """
        SELECT owner, table_name, num_rows, last_analyzed
        FROM all_tables
        WHERE owner = UPPER(:owner)
        ORDER BY table_name
        """
        target_owner = owner_filter.upper() if owner_filter else conn.username.upper()
        cursor.execute(sql, {"owner": target_owner})
        
        tables = []
        for row in cursor.fetchall():
            owner, name, num_rows, last_analyzed = row
            # Count columns
            col_cur = conn.cursor()
            col_cur.execute(
                "SELECT COUNT(*) FROM all_tab_columns WHERE owner = :owner AND table_name = :tname",
                {"owner": owner, "tname": name}
            )
            col_count = col_cur.fetchone()[0]
            col_cur.close()

            tables.append(TableSummary(
                owner=owner,
                table_name=name,
                num_rows=num_rows,
                is_estimated_rows=True,
                column_count=col_count,
                last_analyzed=last_analyzed
            ))
        return tables
    finally:
        cursor.close()


def get_table_detail_oracle(conn: oracledb.Connection, table_name: str, owner: Optional[str] = None) -> TableDetail:
    """Retrieve in-depth columns, indexes, constraints, and preview rows for a table."""
    cursor = conn.cursor()
    target_owner = owner.upper() if owner else conn.username.upper()
    target_table = table_name.upper()

    try:
        # Check table existence
        cursor.execute(
            "SELECT num_rows, last_analyzed FROM all_tables WHERE owner = :owner AND table_name = :tname",
            {"owner": target_owner, "tname": target_table}
        )
        t_row = cursor.fetchone()
        if not t_row:
            raise ObjectNotFoundError(f"Table '{target_owner}.{target_table}' not found in Oracle data dictionary.")
        num_rows, last_analyzed = t_row

        # Get Columns
        col_sql = """
        SELECT column_name, data_type, nullable, data_length, data_precision, data_scale, column_id, num_distinct, density, histogram
        FROM all_tab_columns
        WHERE owner = :owner AND table_name = :tname
        ORDER BY column_id
        """
        cursor.execute(col_sql, {"owner": target_owner, "tname": target_table})
        columns = []
        for c in cursor.fetchall():
            columns.append(ColumnMetadata(
                name=c[0],
                data_type=c[1],
                nullable=(c[2] == 'Y'),
                data_length=c[3],
                data_precision=c[4],
                data_scale=c[5],
                column_id=c[6],
                num_distinct=c[7],
                density=c[8],
                histogram=c[9]
            ))

        # Get Constraints
        cons_sql = """
        SELECT c.constraint_name, c.constraint_type, c.search_condition, c.r_constraint_name,
               (SELECT r.table_name FROM all_constraints r WHERE r.owner = c.r_owner AND r.constraint_name = c.r_constraint_name) AS r_table_name,
               cc.column_name
        FROM all_constraints c
        JOIN all_cons_columns cc ON c.owner = cc.owner AND c.constraint_name = cc.constraint_name
        WHERE c.owner = :owner AND c.table_name = :tname
        ORDER BY c.constraint_name, cc.position
        """
        cursor.execute(cons_sql, {"owner": target_owner, "tname": target_table})
        cons_map = {}
        for row in cursor.fetchall():
            c_name, c_type, search_cond, r_cname, r_tname, col_name = row
            if c_name not in cons_map:
                type_display = {
                    'P': 'PRIMARY KEY',
                    'R': 'FOREIGN KEY',
                    'U': 'UNIQUE',
                    'C': 'CHECK'
                }.get(c_type, c_type)
                cons_map[c_name] = {
                    "constraint_name": c_name,
                    "constraint_type": c_type,
                    "type_display": type_display,
                    "search_condition": search_cond,
                    "r_constraint_name": r_cname,
                    "r_table_name": r_tname,
                    "columns": []
                }
            cons_map[c_name]["columns"].append(col_name)

        constraints = [ConstraintMetadata(**val) for val in cons_map.values()]

        # Annotate primary and foreign keys in columns
        pk_cols = set()
        fk_map = {}
        for c in constraints:
            if c.constraint_type == 'P':
                pk_cols.update(c.columns)
            elif c.constraint_type == 'R':
                for col in c.columns:
                    fk_map[col] = (c.r_table_name, None)

        for col in columns:
            if col.name in pk_cols:
                col.is_primary_key = True
            if col.name in fk_map:
                col.is_foreign_key = True
                col.fk_ref_table = fk_map[col.name][0]

        # Get Indexes
        idx_sql = """
        SELECT i.index_name, i.uniqueness, i.status, i.index_type, i.distinct_keys, ic.column_name
        FROM all_indexes i
        JOIN all_ind_columns ic ON i.owner = ic.index_owner AND i.index_name = ic.index_name
        WHERE i.table_owner = :owner AND i.table_name = :tname
        ORDER BY i.index_name, ic.column_position
        """
        cursor.execute(idx_sql, {"owner": target_owner, "tname": target_table})
        idx_map = {}
        for row in cursor.fetchall():
            i_name, uniqueness, status, itype, dist_keys, col_name = row
            if i_name not in idx_map:
                idx_map[i_name] = {
                    "index_name": i_name,
                    "uniqueness": uniqueness,
                    "status": status,
                    "index_type": itype,
                    "distinct_keys": dist_keys,
                    "columns": []
                }
            idx_map[i_name]["columns"].append(col_name)

        indexes = [IndexMetadata(**val) for val in idx_map.values()]

        # Bounded Preview Rows (First 15 rows)
        preview_sql = f"SELECT * FROM \"{target_owner}\".\"{target_table}\" FETCH FIRST 15 ROWS ONLY"
        cursor.execute(preview_sql)
        col_names = [desc[0] for desc in cursor.description]
        preview_rows = []
        for r in cursor.fetchall():
            row_dict = {}
            for col_idx, col_val in enumerate(r):
                # Convert date/clob to string for JSON serialization
                if hasattr(col_val, "read"):
                    col_val = col_val.read()
                elif isinstance(col_val, (datetime, )):
                    col_val = col_val.isoformat()
                row_dict[col_names[col_idx]] = col_val
            preview_rows.append(row_dict)

        return TableDetail(
            owner=target_owner,
            table_name=target_table,
            num_rows=num_rows,
            is_estimated_rows=True,
            last_analyzed=last_analyzed,
            columns=columns,
            indexes=indexes,
            constraints=constraints,
            preview_rows=preview_rows
        )
    finally:
        cursor.close()


def get_relationships_oracle(conn: oracledb.Connection, owner: Optional[str] = None) -> List[Relationship]:
    """Retrieve actual Foreign Key relationships from Oracle ALL_CONSTRAINTS."""
    cursor = conn.cursor()
    target_owner = owner.upper() if owner else conn.username.upper()
    try:
        sql = """
        SELECT
            c.constraint_name,
            c.table_name AS from_table,
            cc.column_name AS from_column,
            r.table_name AS to_table,
            rc.column_name AS to_column
        FROM all_constraints c
        JOIN all_cons_columns cc ON c.owner = cc.owner AND c.constraint_name = cc.constraint_name
        JOIN all_constraints r ON c.r_owner = r.owner AND c.r_constraint_name = r.constraint_name
        JOIN all_cons_columns rc ON r.owner = rc.owner AND r.constraint_name = rc.constraint_name AND cc.position = rc.position
        WHERE c.owner = :owner AND c.constraint_type = 'R'
        ORDER BY c.table_name, c.constraint_name
        """
        cursor.execute(sql, {"owner": target_owner})
        rels = []
        for row in cursor.fetchall():
            rels.append(Relationship(
                constraint_name=row[0],
                from_table=row[1],
                from_column=row[2],
                to_table=row[3],
                to_column=row[4]
            ))
        return rels
    finally:
        cursor.close()
