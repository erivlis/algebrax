---
title: "EP-0130: API Consistency & Public Export Audit"
description: "Resolve the __init__.py export gap for Phase 2 modules and introduce a Semiring discovery catalog."
icon: lucide/shield-check
status: final
---

# EP-0130: API Consistency & Public Export Audit

| Field       | Value                                 |
|:------------|:--------------------------------------|
| **EP**      | 0130                                  |
| **Title**   | API Consistency & Public Export Audit |
| **Author**  | Eran Rivlis & Antigravity             |
| **Status**  | Final                                 |
| **Type**    | Standards Track                       |
| **Created** | 2026-08-02                            |
| **Updated** | 2026-08-02                            |

## Abstract

Phase 2 introduced four new modules (`algebrax.homology`, `algebrax.clifford`, `algebrax.galois`,
`algebrax.category`) but none are re-exported from `algebrax.__init__.py`. This creates an inconsistency:
these modules exist as first-class citizens with tests and lab views, yet the public API does not surface them.

This proposal resolves the gap by:

1. Re-exporting key symbols from `homology`, `clifford`, `galois`, and `category` in `__init__.py` and `__all__`.
2. Introducing a `Semiring.catalog()` classmethod that returns a discoverable registry of all 21+ semiring types.
3. Documenting extension modules as either "core" or "extension" tier in `concepts.md`.

## Motivation

**Russell (Consistency):** The architecture contains a contradiction — modules that are tested, documented, and
visualized but invisible from the top-level import. Users who `import algebrax` cannot discover
`SimplicialComplex`, `CliffordSemiring`, `GaloisFieldSemiring`, or `kleisli_compose`.

## Specification

### 1. `__init__.py` Additions

```python
from algebrax.homology import SimplicialComplex
from algebrax.clifford import CliffordSemiring, rotor_rotation
from algebrax.galois import GaloisFieldSemiring, gf_matrix_mul
from algebrax.category import kleisli_compose, kan_extension_left
```

### 2. `Semiring.catalog()` Classmethod

```python
@classmethod
def catalog(cls) -> dict[str, type['Semiring']]:
    """Return a discoverable registry of all built-in semiring types."""
```

### 3. Module Docstring Update

Update the `__init__.py` module docstring `Modules` section to include `homology`, `clifford`, `galois`, `category`.

## Backwards Compatibility

Purely additive. No existing behavior changes.

## Change Log

* **2026-08-02:** Initial Draft.
* **2026-08-02:** Implemented. Status → Final.
