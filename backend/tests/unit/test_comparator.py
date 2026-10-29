"""Unit tests for Query Result Equivalence and Multiset Comparison."""

from app.benchmarking.comparator import compare_query_results


def test_identical_ordered_results():
    b_rows = [{"ID": 1, "VAL": "A"}, {"ID": 2, "VAL": "B"}]
    c_rows = [{"ID": 1, "VAL": "A"}, {"ID": 2, "VAL": "B"}]
    cols = ["ID", "VAL"]

    res = compare_query_results(b_rows, c_rows, cols, cols)
    assert res.is_equivalent is True
    assert res.status == "EQUIVALENT"


def test_unordered_rows_multiset_equivalence():
    # SQL sets without ORDER BY can return rows in different sequence
    b_rows = [{"ID": 1, "VAL": "A"}, {"ID": 2, "VAL": "B"}, {"ID": 3, "VAL": "C"}]
    c_rows = [{"ID": 3, "VAL": "C"}, {"ID": 1, "VAL": "A"}, {"ID": 2, "VAL": "B"}]
    cols = ["ID", "VAL"]

    res = compare_query_results(b_rows, c_rows, cols, cols)
    assert res.is_equivalent is True
    assert res.status == "EQUIVALENT"


def test_duplicate_rows_handling():
    # Duplicates in baseline must match exact frequency in candidate
    b_rows = [{"ID": 1, "VAL": "A"}, {"ID": 1, "VAL": "A"}]
    c_rows = [{"ID": 1, "VAL": "A"}]  # Missing one duplicate
    cols = ["ID", "VAL"]

    res = compare_query_results(b_rows, c_rows, cols, cols)
    assert res.is_equivalent is False
    assert res.status == "DIFFERENT"
    assert res.row_count_baseline == 2
    assert res.row_count_candidate == 1


def test_column_name_mismatch():
    b_rows = [{"ID": 1, "NAME": "Widget"}]
    c_rows = [{"ID": 1, "PRODUCT_NAME": "Widget"}]

    res = compare_query_results(b_rows, c_rows, ["ID", "NAME"], ["ID", "PRODUCT_NAME"])
    assert res.is_equivalent is False
    assert res.column_match is False
    assert "Column sets do not match" in res.reason


def test_float_precision_tolerance():
    # Float precision within 4 decimals should match
    b_rows = [{"PRICE": 19.9900001}]
    c_rows = [{"PRICE": 19.99}]
    cols = ["PRICE"]

    res = compare_query_results(b_rows, c_rows, cols, cols)
    assert res.is_equivalent is True
