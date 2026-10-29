"""Benchmark Runner and Statistical Performance Engine.

Conducts repeatable query benchmark iterations with warm-up runs,
calculates median, min, max, and IQR statistics, and produces evidence-based interpretations.
"""

import statistics
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.database.executor import execute_query
from app.benchmarking.comparator import compare_query_results
from app.schemas.comparison import (
    ComparisonRequest, ComparisonResponse, VariantStatistics, RunMeasurement, EquivalenceResult
)


def calculate_statistics(label: str, durations: List[float], rows: int, failed_count: int) -> VariantStatistics:
    """Calculate summary statistics from measured run durations."""
    if not durations:
        return VariantStatistics(
            label=label, runs=0, median_ms=0.0, min_ms=0.0, max_ms=0.0,
            iqr_ms=0.0, successful_runs=0, failed_runs=failed_count, rows=0
        )

    durations_sorted = sorted(durations)
    median_val = round(statistics.median(durations_sorted), 3)
    min_val = round(min(durations_sorted), 3)
    max_val = round(max(durations_sorted), 3)

    if len(durations_sorted) >= 4:
        # Quartiles
        q1 = statistics.median(durations_sorted[:len(durations_sorted)//2])
        q3 = statistics.median(durations_sorted[(len(durations_sorted)+1)//2:])
        iqr_val = round(q3 - q1, 3)
    else:
        iqr_val = round(max_val - min_val, 3)

    return VariantStatistics(
        label=label,
        runs=len(durations_sorted),
        median_ms=median_val,
        min_ms=min_val,
        max_ms=max_val,
        iqr_ms=iqr_val,
        successful_runs=len(durations_sorted),
        failed_runs=failed_count,
        rows=rows
    )


def run_benchmark_comparison(req: ComparisonRequest) -> ComparisonResponse:
    """
    Run warm-up and measured benchmarking iterations for baseline and candidate queries.
    """
    comp_id = f"cmp_{uuid.uuid4().hex[:10]}"

    # Warm-up phase (prime buffer cache and cursors)
    for _ in range(req.warmup_runs):
        execute_query(req.baseline.sql, req.baseline.parameters)
        execute_query(req.candidate.sql, req.candidate.parameters)

    # Measured runs
    baseline_durations: List[float] = []
    candidate_durations: List[float] = []
    runs_data: List[RunMeasurement] = []

    last_baseline_res = None
    last_candidate_res = None
    baseline_failed = 0
    candidate_failed = 0

    for i in range(1, req.measured_runs + 1):
        # Run baseline
        b_res = execute_query(req.baseline.sql, req.baseline.parameters)
        last_baseline_res = b_res
        if b_res.status == "SUCCESS":
            baseline_durations.append(b_res.duration_ms)
        else:
            baseline_failed += 1

        # Run candidate
        c_res = execute_query(req.candidate.sql, req.candidate.parameters)
        last_candidate_res = c_res
        if c_res.status == "SUCCESS":
            candidate_durations.append(c_res.duration_ms)
        else:
            candidate_failed += 1

        runs_data.append(RunMeasurement(
            run_index=i,
            baseline_duration_ms=b_res.duration_ms,
            candidate_duration_ms=c_res.duration_ms,
            baseline_rows=b_res.rows_returned,
            candidate_rows=c_res.rows_returned
        ))

    # Calculate statistics
    b_rows = last_baseline_res.rows_returned if last_baseline_res else 0
    c_rows = last_candidate_res.rows_returned if last_candidate_res else 0
    baseline_stats = calculate_statistics(req.baseline.label or "Baseline", baseline_durations, b_rows, baseline_failed)
    candidate_stats = calculate_statistics(req.candidate.label or "Candidate", candidate_durations, c_rows, candidate_failed)

    # Evaluate Result Equivalence
    if req.compare_equivalence and last_baseline_res and last_candidate_res:
        b_cols = [c.name for c in last_baseline_res.columns]
        c_cols = [c.name for c in last_candidate_res.columns]
        equivalence = compare_query_results(
            last_baseline_res.rows, last_candidate_res.rows, b_cols, c_cols
        )
    else:
        equivalence = EquivalenceResult(
            is_equivalent=False,
            status="INCONCLUSIVE",
            reason="Equivalence checking was skipped or one of the queries failed to execute.",
            row_count_baseline=b_rows,
            row_count_candidate=c_rows,
            column_match=False,
            columns_baseline=[],
            columns_candidate=[]
        )

    # Compute speedup ratio
    speedup = None
    if baseline_stats.median_ms > 0 and candidate_stats.median_ms > 0:
        speedup = round(baseline_stats.median_ms / candidate_stats.median_ms, 2)

    # Generate factual improvement summary
    if speedup and speedup > 1.05:
        improvement_summary = f"Candidate query was {speedup}x faster (median {candidate_stats.median_ms}ms vs {baseline_stats.median_ms}ms)."
    elif speedup and speedup < 0.95:
        improvement_summary = f"Candidate query was slower ({round(1/speedup, 2)}x slower, median {candidate_stats.median_ms}ms vs {baseline_stats.median_ms}ms)."
    else:
        improvement_summary = f"Measured execution durations were statistically indistinguishable ({candidate_stats.median_ms}ms vs {baseline_stats.median_ms}ms)."

    caveat = (
        "Timing measurements reflect local execution interval across repeated runs. Results are subject to "
        "local buffer cache state, I/O caching, and CPU concurrency, and should not be treated as a direct production performance guarantee."
    )

    env = last_baseline_res.environment if last_baseline_res else "Oracle Database Free"

    return ComparisonResponse(
        comparison_id=comp_id,
        hypothesis=req.hypothesis,
        equivalence=equivalence,
        baseline_stats=baseline_stats,
        candidate_stats=candidate_stats,
        runs_data=runs_data,
        speedup_ratio=speedup,
        improvement_summary=improvement_summary,
        caveat=caveat,
        environment=env,
        created_at=datetime.now(timezone.utc)
    )
