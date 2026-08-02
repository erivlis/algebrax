---
title: "EP-0131: Algebraic Law Verification Engine"
description: "Property-based testing framework that automatically verifies semiring axioms across all 23 semiring types."
icon: lucide/flask-conical
status: final
---

# EP-0131: Algebraic Law Verification Engine

| Field       | Value                             |
|:------------|:----------------------------------|
| **EP**      | 0131                              |
| **Title**   | Algebraic Law Verification Engine |
| **Author**  | Eran Rivlis & Antigravity         |
| **Status**  | Final                             |
| **Type**    | Standards Track                   |
| **Created** | 2026-08-02                        |
| **Updated** | 2026-08-02                        |

## Abstract

The library provides 23 semiring implementations, each claiming to satisfy specific algebraic axioms (associativity,
distributivity, identity, annihilation). Currently, these axioms are tested implicitly through application-level tests.
This proposal introduces an **Algebraic Law Verification Engine** that systematically and automatically tests every
axiom for every semiring type.

## Motivation

**Popper (Falsifiability):** *"Assume the happy path is a lie."* The library *claims* algebraic correctness but does not
have a systematic mechanism to *prove* it across all semiring types with random inputs.

## Specification

### 1. `verify_semiring_laws(semiring, samples)` Function

```python
def verify_semiring_laws(
    semiring: Semiring[T],
    samples: list[T],
) -> dict[str, bool]:
    """
    Test all semiring axioms with the given sample elements.

    Returns a dict mapping axiom name to pass/fail:
      - 'add_associativity'
      - 'add_commutativity'
      - 'add_identity'
      - 'mul_associativity'
      - 'mul_identity'
      - 'left_distributivity'
      - 'right_distributivity'
      - 'left_annihilation'
      - 'right_annihilation'
    """
```

### 2. Parametrized Test Suite

A `pytest` parametrized test that iterates over all semiring types from `Semiring.catalog()` and verifies all axioms
with type-appropriate random samples.

### 3. Runtime Auditor (Optional)

A `python -m algebrax.verify` CLI entry point that runs the law verification and prints a pass/fail report.

## Backwards Compatibility

Purely additive. No existing behavior changes.

## Change Log

* **2026-08-02:** Initial Draft.
* **2026-08-02:** Implemented `verification.py`, CLI runner `verify.py`, `ModularSemiring` fix, and parametrized test suite (274 tests passing). Status → Final.
