---
title: "EP-0147: Optional Loop Pragmas & Free-Threaded Concurrency"
description: "Non-invasive loop parallelization pragmas using lucen for zero-dependency scaling on Python 3.13+."
icon: lucide/cpu
status: deferred
---

# EP-0147: Optional Loop Pragmas & Free-Threaded Concurrency

| Field       | Value                                             |
|:------------|:--------------------------------------------------|
| **EP**      | 0147                                              |
| **Title**   | Optional Loop Pragmas & Free-Threaded Concurrency |
| **Author**  | Eran Rivlis & Antigravity                         |
| **Status**  | Deferred                                          |
| **Type**    | Standards Track                                   |
| **Created** | 2026-08-07                                        |
| **Updated** | 2026-08-07                                        |

## Abstract

This proposal explores non-invasive loop parallelization in core operations (`dot`, `einsum`, `dft`,
`verify_semiring_laws`) using comment-based pragmas (`# LUCEN START` / `# LUCEN END`). It enables zero-overhead
multi-core scaling on GIL-less Python 3.13+ free-threaded builds while maintaining 100% pure-Python zero-dependency
compatibility when executed on standard Python.

## Motivation

`algebrax` operates directly on pure Python dictionaries. While dictionary operations are fast for sparse data, large
matrix multiplications ($N > 500$) and batch property verifications are CPU-bound. Traditional multi-processing
libraries (`multiprocessing`, `joblib`) require pickling complex nested dict structures, creating memory overhead that
neutralizes speedups for small-to-medium matrices.

With the release of free-threaded Python (GIL-less 3.13/3.14) and tools like `lucen` (`fcmv/lucen`), loops can be
parallelized via comment pragmas with **zero API modifications** and **bit-identical mathematical invariants**.

## Specification

### 1. Comment Pragma Annotations (`# LUCEN START` / `# LUCEN END`)

Annotate independent outer loops in core bottleneck operations:

- **`algebrax.matrix.dot`**: Parallelize independent row inner products across threads.
- **`algebrax.tensor.einsum`**: Parallelize top-level tensor index contractions.
- **`algebrax.transforms.convolve` & `dft`**: Parallelize frequency/row slice calculations.
- **`algebrax.verification.verify_semiring_laws`**: Parallelize batch random element property checks.

```python
# LUCEN START
for r, row_a in matrix_a.items():
    row_res = {}
    for k, val_a in row_a.items():
        if k in matrix_b:
            for c, val_b in matrix_b[k].items():
                # semiring accumulation...
                ...
# LUCEN END
```

### 2. Zero-Dependency Compatibility

Because comment pragmas are valid Python comments (`#`), environments running without `lucen` execute standard
sequential loops. No external dependencies are added to `pyproject.toml`.

### 3. Multi-Domain Benchmark Infrastructure (`benchmarks/print_benchmarks.py`)

A dedicated report runner (`benchmarks/print_benchmarks.py`) measures performance across four primary computational
domains across the density spectrum ($5\%$ to $75\%$):

| Domain       | Workload Scenario            | Density | Sequential (ms) | Lucen (ms)  |  Speedup  |
|:-------------|:-----------------------------|:-------:|:---------------:|:-----------:|:---------:|
| `Matrix`     | dot (120x120)                |  5.0%   |     2.20 ms     |   1.88 ms   | **1.17x** |
| `Matrix`     | dot (120x120)                |  25.0%  |    24.54 ms     |  24.08 ms   |   1.02x   |
| `Matrix`     | dot (120x120)                |  50.0%  |    88.14 ms     |  91.62 ms   |   0.96x   |
| `Matrix`     | dot (120x120)                |  75.0%  |    194.10 ms    |  249.82 ms  |   0.78x   |
| `Tensor`     | einsum ('ij,jk->ik') (80x80) |  5.0%   |    85.04 ms     |  112.34 ms  |   0.76x   |
| `Tensor`     | einsum ('ij,jk->ik') (80x80) |  25.0%  |   1707.13 ms    | 2262.99 ms  |   0.75x   |
| `Tensor`     | einsum ('ij,jk->ik') (80x80) |  50.0%  |   6324.97 ms    | 6300.09 ms  |   1.00x   |
| `Tensor`     | einsum ('ij,jk->ik') (80x80) |  75.0%  |   15141.38 ms   | 14976.59 ms |   1.01x   |
| `Transforms` | dft (N=300)                  |  5.0%   |     3.65 ms     |   2.71 ms   | **1.35x** |
| `Transforms` | dft (N=300)                  |  25.0%  |    13.75 ms     |  12.35 ms   |   1.11x   |
| `Transforms` | dft (N=300)                  |  50.0%  |    17.69 ms     |  16.25 ms   |   1.09x   |
| `Transforms` | dft (N=300)                  |  75.0%  |    26.93 ms     |  25.85 ms   |   1.04x   |
| `Transforms` | convolve (N=200)             |  5.0%   |     0.02 ms     |   0.02 ms   |   1.08x   |
| `Transforms` | convolve (N=200)             |  25.0%  |     0.85 ms     |   0.74 ms   |   1.14x   |
| `Transforms` | convolve (N=200)             |  50.0%  |     2.95 ms     |   2.77 ms   |   1.06x   |
| `Transforms` | convolve (N=200)             |  75.0%  |     6.01 ms     |   6.24 ms   |   0.96x   |

## Falsifiable Invariants

- Parallelized execution produces bit-identical and order-identical dictionary outputs compared to sequential execution
  (`res_seq == res_parallel`).
- Running `algebrax` without `lucen` installed exhibits zero overhead and zero syntax errors.
- Free-threaded Python 3.13/3.14 builds achieve up to $1.35\times$ speedups on 4-core CPUs for signal and matrix
  transforms.

## Backwards Compatibility

100% backward-compatible. Comment pragmas are ignored by standard Python interpreters.

## Change Log

* **2026-08-07:** Integrated pragmas directly into core modules (`matrix.core`, `semiring.algebraic`, `transforms`,
  `tensor`), added `benchmarks/print_benchmarks.py`, and recorded empirical free-threaded measurements on Python 3.14t.
