---
title: "EP-0144: Testing & Falsifiability Hardening"
description: "Strengthens the test suite with property-based testing, edge-case coverage, and numerical stability verification."
icon: lucide/test-tubes
status: final
---

# EP-0144: Testing & Falsifiability Hardening

| Field       | Value                                  |
|:------------|:---------------------------------------|
| **EP**      | 0144                                   |
| **Title**   | Testing & Falsifiability Hardening     |
| **Author**  | Eran Rivlis & Antigravity              |
| **Status**  | Final                                  |
| **Type**    | Standards Track                        |
| **Created** | 2026-08-02                             |
| **Updated** | 2026-08-05                             |

## Abstract

The Grand Council Assessment (Popper) identified gaps in edge-case coverage, absence of property-based
testing, and untested numerical stability boundaries. This proposal hardens the test suite to ensure
every mathematical claim is falsifiable.

## Motivation

The existing test suite (279 tests, 23 files) is broadly effective but relies entirely on hand-crafted
fixtures. The verification engine (`verify_semiring_laws`) provides excellent algebraic axiom coverage
for semirings, but matrix operations, decompositions, and automata lack equivalent systematic edge-case
and property-based testing.

## Specification

### 1. Property-Based Testing Infrastructure

- Added `hypothesis` as an optional test dependency (`[test]` extra in `pyproject.toml`).
- Created `hypothesis` strategies for generating:
  - Random sparse vectors of configurable density and key/value types.
  - Random sparse matrices (nested dict) of configurable dimensions and density.
  - Random `AlgebraicTrie` instances.
- Applied property-based tests to core matrix operations:
  - `add(A, B) == add(B, A)` (commutativity)
  - `transpose(transpose(A)) == A` (involution)
  - `dot(I, A) == A` (identity)
  - `trace(transpose(A)) == trace(A)` (trace invariance)

### 2. Edge-Case Test Coverage

Added explicit tests for:

| Operation | Edge Case | Expected Behavior |
|:---|:---|:---|
| `determinant({})` | Empty matrix | Returns `1` |
| `inverse({})` | Empty matrix | Returns `{}` |
| `lu({})`, `qr({})`, `svd({})` | Empty matrix | Returns empty factor tuples |
| `cholesky(non_pd)` | Non-positive-definite input | Raises `ValueError` |
| `inverse(singular)` | Singular matrix | Raises `ValueError` |
| `AlgebraicTrie` | `pickle.dumps` / `pickle.loads` round-trip | `__getstate__`/`__setstate__` serialization |
| All decompositions | 1×1 matrix `{0: {0: v}}` | Correct trivial factorization |

### 3. Numerical Stability Tests

- Added ill-conditioned matrix tests (Hilbert matrices of size 3×3, 5×5) for `lu`, `qr`, `svd`.
- Verified decomposition accuracy degrades gracefully with increasing condition number.
- Documented expected accuracy bounds as test assertions with appropriate tolerances.

### 4. Automata Edge Cases

- Tested with unreachable states, empty transition tables, empty input strings.
- Tested DFA/NFA simulation with single-state accepting machines.

### 5. Cross-Semiring Matrix Stress Tests

- Tested `dot()` with `TropicalSemiring` on 10×10 and 30×30 sparse graphs.
- Verified `power()` convergence with `BooleanSemiring` transitive closure on random sparse graphs.

## Falsifiable Invariants

- `hypothesis` property-based tests discover no property violations in random examples.
- All edge-case tests produce well-defined behavior (correct result or explicit exception).
- Numerical stability tests document expected accuracy bounds per condition number range.

## Backwards Compatibility

Test-only changes. `AlgebraicTrie` gained `__getstate__`/`__setstate__` for pickle support.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Popper).
* **2026-08-05:** Fully implemented property-based tests (`test_properties.py`), edge-case suite (`test_edge_cases.py`), numerical stability suite (`test_numerical_stability.py`), added `hypothesis` dependency, and added `__getstate__`/`__setstate__` to `AlgebraicTrie`. Status → Final.

