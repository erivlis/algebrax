---
title: "EP-0148: Formalized Micro-Benchmarking & Performance Regression Tracking"
description: "Standardized micro-benchmarking suite using pytest-benchmark and pytest-codspeed for statistical analysis and CI performance regression tracking."
icon: lucide/gauge
status: final
---

# EP-0148: Formalized Micro-Benchmarking & Performance Regression Tracking

| Field       | Value                                                           |
|:------------|:----------------------------------------------------------------|
| **EP**      | 0148                                                            |
| **Title**   | Formalized Micro-Benchmarking & Performance Regression Tracking |
| **Author**  | Eran Rivlis & Antigravity                                       |
| **Status**  | Final                                                           |
| **Type**    | Standards Track                                                 |
| **Created** | 2026-08-08                                                      |
| **Updated** | 2026-08-08                                                      |

## Abstract

This proposal establishes a standardized, reproducible micro-benchmarking infrastructure across `algebrax` using
`pytest-benchmark` and `pytest-codspeed`. It introduces statistical execution profiling (mean, median, IQR, ops/sec),
flamegraph analysis, and automated CI performance regression tracking on GitHub Pull Requests — ensuring zero-noise
performance auditing while preserving the 100% pure-Python zero-dependency core.

## Motivation

While manual time-delta scripts (`timeit.timeit()`) provide quick sanity checks, they lack statistical rigor and CI
regression prevention:

1. **Lack of Statistical Confidence**: Manual benchmark scripts do not record standard deviation, interquartile range
   (IQR), or iteration counts across runs.
2. **No Automated CI Regression Prevention**: Performance regressions introduced by refactoring can silently land in
   `main` without automated instruction-count gates.
3. **Inconsistent Workload Parameterization**: Benchmark workloads (sizes, densities, semirings) are scattered across
   manual scripts instead of being part of a structured test suite.

Integrating `pytest-benchmark` and `pytest-codspeed` solves all three issues cleanly within standard `pytest` workflows.

## Specification

### 1. Dependency Group Specification (`pyproject.toml`)

Add an isolated `benchmark` dependency group under `[dependency-groups]` in `pyproject.toml`:

```toml
[dependency-groups]
benchmark = [
    "pytest-benchmark>=4.0.0",
    "pytest-codspeed>=3.0.0",
    "hypothesis>=6.165.1",
    "numpy",
]
```

### 2. Standardized Benchmark Suite (`benchmarks/test_benchmarks.py`)

Implement `pytest-benchmark` parameterization for core mathematical operations across size ($N \in \{20, 80, 150\}$) and
density ($\text{density} \in \{0.05, 0.25, 0.50, 0.75\}$) spectrums:

- **Matrix Operations**: `ax.matrix.dot`, `ax.matrix.transpose`, `ax.matrix.power` (over Standard, Tropical, and Boolean
  semirings).
- **Tensor Operations**: `ax.tensor.einsum`, `ax.tensor.outer_product`.
- **Signal Transforms**: `ax.transforms.dft`, `ax.transforms.idft`, `ax.transforms.convolve`.
- **Topological Data Analysis**: `ax.homology.betti_numbers`, `ax.homology.coboundary`.
- **Trie Operations**: `AlgebraicTrie` insertion, key lookup, prefix traversal.

```python
import pytest
import algebrax as ax


@pytest.mark.benchmark(group="matrix-dot")
@pytest.mark.parametrize("density", [0.05, 0.25, 0.50, 0.75])
def test_benchmark_matrix_dot(benchmark, density):
    A = generate_sparse_matrix(100, 100, density)
    B = generate_sparse_matrix(100, 100, density)
    result = benchmark(ax.matrix.dot, A, B)
    assert result is not None
```

### 3. CodSpeed CI Workflow Integration (`.github/workflows/codspeed.yml`)

Configure GitHub Actions to run CPU instruction-count tracking via CodSpeed on every Pull Request:

```yaml
name: CodSpeed Performance Audit

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  benchmarks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - name: Install Dependencies
        run: uv sync --group benchmark
      - name: Run CodSpeed Benchmarks
        uses: CodSpeedHQ/action@v3
        with:
          run: uv run pytest benchmarks/ --codspeed
```

## Falsifiable Invariants

- Running `uv run --group benchmark pytest benchmarks/ --benchmark-only` outputs a complete statistical table with
  min/max/mean/median/IQR.
- Running `uv run pytest benchmarks/ --codspeed` measures deterministic instruction counts without flaky timing jitter.
- The `algebrax` core library retains zero runtime dependencies (benchmark dependencies remain strictly isolated in the
  `benchmark` group).
- Standard `pytest tests/` runs execute normal unit tests without benchmark overhead.

## Backwards Compatibility

100% backward-compatible. Benchmark tools are isolated in the `[dependency-groups] benchmark` table.

## Change Log

* **2026-08-08:** Initial Proposal drafted for formalized micro-benchmarking via `pytest-benchmark` and
  `pytest-codspeed`.
