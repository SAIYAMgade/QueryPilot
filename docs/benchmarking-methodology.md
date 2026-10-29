# Query Comparison & Benchmarking Methodology

This document outlines the statistical principles, measurement boundaries, and result-equivalence verification rules implemented in QueryPilot.

---

## 1. Result Equivalence: Multiset Comparison

SQL tables represent mathematical relations. In the absence of an explicit `ORDER BY` clause, relational database theory dictates that returned rows have **no guaranteed order**.

Comparing two query variants by row position (index-by-index) produces false negatives whenever Oracle’s optimizer alters the execution path (e.g. switching from an index scan to a hash join or sorting differently).

### Algorithm: Order-Independent Multiset Equivalence

QueryPilot applies multiset comparison with frequency counting:

1. **Column Alignment**: Verifies that both baseline and candidate result sets return the exact same set of column names (case-insensitive).
2. **Cardinality Match**: Compares total row counts ($N_{baseline} == N_{candidate}$).
3. **Value Normalization**:
   - Numeric values are normalized to 4 decimal places to prevent floating-point representation drift.
   - `NULL` representations are canonicalized (`"__NULL__"`).
   - Strings are trimmed.
4. **Frequency Counting**: Converts each row dictionary into a canonical tuple ordered by column names and computes frequency counters:
   $$\text{BaselineCounter} == \text{CandidateCounter}$$
5. **Sample Discrepancy Generation**: If equivalence fails, the algorithm computes symmetric set differences to isolate the exact rows present in one variant but missing in the other.

---

## 2. Statistical Benchmark Execution

A single execution run is insufficient to assess query performance due to:
- Operating system page caching and Oracle Database buffer cache state (cold vs warm cache).
- Hard vs soft parsing overhead in the library cache.
- Client driver networking and serialization latency.

### Benchmark Protocol

1. **Warm-Up Phase**: Executes configurable warm-up runs (default 1) for both baseline and candidate queries to prime buffer caches and cursor parsing. Measurements from warm-up runs are excluded from statistics.
2. **Measured Runs**: Executes $K$ repeated iterations (default 3 to 5 runs) alternating between baseline and candidate queries.
3. **Summary Statistics**:
   - **Median**: Primary central tendency metric (resistant to transient system spikes).
   - **Minimum & Maximum**: Measures dispersion and best-case/worst-case behavior.
   - **Interquartile Range (IQR)**: Measures variability across the middle 50% of runs.
   - **Speedup Factor**: Computed strictly from median observed durations:
     $$\text{Speedup} = \frac{\text{Median}_{\text{Baseline}}}{\text{Median}_{\text{Candidate}}}$$

---

## 3. Transparency & Caveats

QueryPilot adheres to strict engineering rules:
- **Never fabricates execution times**: Timings are derived from actual high-resolution wall-clock intervals (`time.perf_counter()`).
- **Never fabricates performance improvements**: If a candidate rewrite is slower or indistinguishable, QueryPilot reports that outcome honestly.
- **Environment Caveats**: Local developer workstations differ from production hardware (storage tier, concurrent sessions, RAC cluster topology). Benchmark results should be treated as local comparative evidence, not production performance guarantees.
