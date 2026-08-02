---
title: "EP-0144: Testing & Falsifiability Hardening"
description: "Strengthens the test suite with property-based testing, edge-case coverage, and numerical stability verification."
icon: lucide/test-tubes
status: draft
---

# EP-0144: Testing & Falsifiability Hardening

| Field       | Value                                  |
|:------------|:---------------------------------------|
| **EP**      | 0144                                   |
| **Title**   | Testing & Falsifiability Hardening     |
| **Author**  | Eran Rivlis & Antigravity              |
| **Status**  | Draft                                  |
| **Type**    | Standards Track                        |
| **Created** | 2026-08-02                             |
| **Updated** | 2026-08-02                             |

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

- Add `hypothesis` as an optional test dependency (`[test]` extra in `pyproject.toml`).
- Create `hypothesis` strategies for generating:
  - Random sparse vectors of configurable density and key/value types.
  - Random sparse matrices (nested dict) of configurable dimensions and density.
  - Random `AlgebraicTrie` instances.
- Apply property-based tests to core matrix operations:
  - `add(A, B) == add(B, A)` (commutativity)
  - `transpose(transpose(A)) == A` (involution)
  - `dot(I, A) == A` (identity)
  - `trace(transpose(A)) == trace(A)` (trace invariance)

### 2. Edge-Case Test Coverage

Add explicit tests for:

| Operation | Edge Case | Expected Behavior |
|:---|:---|:---|
| `determinant({})` | Empty matrix | Returns `0` or `1` (convention) |
| `inverse({})` | Empty matrix | Returns `{}` or raises `ValueError` |
| `lu({})`, `qr({})`, `svd({})` | Empty matrix | Returns empty factor tuples |
| `cholesky(non_pd)` | Non-positive-definite input | Raises `ValueError` |
| `inverse(singular)` | Singular matrix | Raises `ValueError` |
| `AlgebraicTrie` | `pickle.dumps` / `pickle.loads` round-trip | Sentinel identity preserved |
| All decompositions | 1×1 matrix `{0: {0: v}}` | Correct trivial factorization |

### 3. Numerical Stability Tests

- Add ill-conditioned matrix tests (Hilbert matrices of size 5×5, 10×10) for `lu`, `qr`, `svd`.
- Verify decomposition accuracy degrades gracefully with increasing condition number.
- Document expected accuracy bounds as test assertions with appropriate tolerances.

### 4. Automata Edge Cases

- Test with unreachable states, empty transition tables, empty input strings.
- Test DFA/NFA simulation with single-state accepting machines.

### 5. Cross-Semiring Matrix Stress Tests

- Test `dot()` with `TropicalSemiring` on 10×10 and 50×50 sparse graphs.
- Verify `power()` convergence with `BooleanSemiring` transitive closure on random sparse graphs.

## Falsifiable Invariants

- `hypothesis` tests discover no property violations in 10,000 random examples per property.
- All edge-case tests produce well-defined behavior (correct result or explicit exception).
- Numerical stability tests document expected accuracy bounds per condition number range.

## Backwards Compatibility

Test-only changes. No API modifications.

## Change Log

* **2026-08-02:** Initial Draft from Grand Council Assessment (Popper).
