"""Query Result Equivalence and Multiset Comparison Engine.

Evaluates whether two SQL queries return semantically equivalent results,
handling unordered row sets, duplicate rows, column alignment, and numeric precision.
"""

from collections import Counter
import json
from typing import List, Dict, Any, Tuple
from app.schemas.comparison import EquivalenceResult


def normalize_val(val: Any) -> str:
    """Normalize values for robust equivalence comparison."""
    if val is None:
        return "__NULL__"
    if isinstance(val, float):
        # Round to 4 decimal places to prevent floating point representation drift
        return str(round(val, 4))
    if isinstance(val, (int, bool)):
        return str(val)
    return str(val).strip()


def serialize_row_multiset(row: Dict[str, Any], sorted_cols: List[str]) -> Tuple[str, ...]:
    """Convert a row dictionary to a canonical tuple of normalized string values."""
    return tuple(normalize_val(row.get(col)) for col in sorted_cols)


def compare_query_results(
    baseline_rows: List[Dict[str, Any]],
    candidate_rows: List[Dict[str, Any]],
    baseline_cols: List[str],
    candidate_cols: List[str]
) -> EquivalenceResult:
    """
    Compare two query result sets for semantic equivalence.
    Uses multiset comparison so unordered rows without explicit ORDER BY are compared accurately.
    """
    b_count = len(baseline_rows)
    c_count = len(candidate_rows)

    # 1. Compare column names (case-insensitive)
    b_cols_upper = [c.upper() for c in baseline_cols]
    c_cols_upper = [c.upper() for c in candidate_cols]

    if set(b_cols_upper) != set(c_cols_upper):
        diff = set(b_cols_upper).symmetric_difference(set(c_cols_upper))
        return EquivalenceResult(
            is_equivalent=False,
            status="DIFFERENT",
            reason=f"Column sets do not match. Discrepant columns: {list(diff)}",
            row_count_baseline=b_count,
            row_count_candidate=c_count,
            column_match=False,
            columns_baseline=baseline_cols,
            columns_candidate=candidate_cols,
            diff_summary=f"Baseline returned columns {baseline_cols}; Candidate returned {candidate_cols}."
        )

    # 2. Compare row counts
    if b_count != c_count:
        return EquivalenceResult(
            is_equivalent=False,
            status="DIFFERENT",
            reason=f"Row counts differ: Baseline returned {b_count} rows, Candidate returned {c_count} rows.",
            row_count_baseline=b_count,
            row_count_candidate=c_count,
            column_match=True,
            columns_baseline=baseline_cols,
            columns_candidate=candidate_cols,
            diff_summary=f"Count mismatch: Baseline={b_count}, Candidate={c_count}."
        )

    # If both return 0 rows
    if b_count == 0 and c_count == 0:
        return EquivalenceResult(
            is_equivalent=True,
            status="EQUIVALENT",
            reason="Both queries returned 0 rows with matching column structures.",
            row_count_baseline=0,
            row_count_candidate=0,
            column_match=True,
            columns_baseline=baseline_cols,
            columns_candidate=candidate_cols
        )

    # 3. Canonical multiset comparison using frequency counting
    canonical_cols = sorted(list(set(b_cols_upper)))

    # Normalize key casing in rows
    norm_baseline_rows = [{k.upper(): v for k, v in r.items()} for r in baseline_rows]
    norm_candidate_rows = [{k.upper(): v for k, v in r.items()} for r in candidate_rows]

    baseline_counter = Counter(serialize_row_multiset(r, canonical_cols) for r in norm_baseline_rows)
    candidate_counter = Counter(serialize_row_multiset(r, canonical_cols) for r in norm_candidate_rows)

    if baseline_counter == candidate_counter:
        return EquivalenceResult(
            is_equivalent=True,
            status="EQUIVALENT",
            reason=f"All {b_count} rows and column values are identical under multiset comparison (order-independent).",
            row_count_baseline=b_count,
            row_count_candidate=c_count,
            column_match=True,
            columns_baseline=baseline_cols,
            columns_candidate=candidate_cols
        )

    # 4. Discrepancy found: compute sample difference
    diff_baseline_extra = baseline_counter - candidate_counter
    diff_candidate_extra = candidate_counter - baseline_counter

    sample_discrepancy = {}
    if diff_baseline_extra:
        sample_tuple = next(iter(diff_baseline_extra))
        sample_discrepancy["present_in_baseline_only"] = dict(zip(canonical_cols, sample_tuple))
    if diff_candidate_extra:
        sample_tuple = next(iter(diff_candidate_extra))
        sample_discrepancy["present_in_candidate_only"] = dict(zip(canonical_cols, sample_tuple))

    return EquivalenceResult(
        is_equivalent=False,
        status="DIFFERENT",
        reason="Row contents differ between baseline and candidate results.",
        row_count_baseline=b_count,
        row_count_candidate=c_count,
        column_match=True,
        columns_baseline=baseline_cols,
        columns_candidate=candidate_cols,
        diff_summary=f"Found {len(diff_baseline_extra)} discrepant row patterns in baseline and {len(diff_candidate_extra)} in candidate.",
        sample_discrepancy=sample_discrepancy
    )
