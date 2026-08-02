---
title: "EP-0134: Semiring Namespace Refactoring & Categorical Sub-Modules"
description: "Refactor the monolithic semiring.py into a semiring/ namespace package with categorical sub-modules for discoverability, consistency, and maintainability."
icon: lucide/folder-tree
status: final
---

# EP-0134: Semiring Namespace Refactoring & Categorical Sub-Modules

| Field       | Value                                                          |
|:------------|:---------------------------------------------------------------|
| **EP**      | 0134                                                           |
| **Title**   | Semiring Namespace Refactoring & Categorical Sub-Modules       |
| **Author**  | Eran Rivlis & Antigravity                                      |
| **Status**  | Final                                                          |
| **Type**    | Standards Track                                                |
| **Created** | 2026-08-02                                                     |
| **Updated** | 2026-08-02                                                     |

## Abstract

This proposal refactors the monolithic `src/algebrax/semiring.py` (1,109 lines, 21 classes) into a
`src/algebrax/semiring/` namespace package with categorical sub-modules. It also consolidates the two
scattered semiring definitions (`CliffordSemiring` in `clifford.py`, `GaloisFieldSemiring` in `galois.py`)
into the unified namespace. All existing import paths remain fully backward compatible via re-exports in
`semiring/__init__.py`.

## Motivation

Two violations of the Council Framework drive this proposal:

### 1. Shannon Violation: The File Is Too Large

`semiring.py` contains 1,109 lines housing 21 distinct classes spanning 5 mathematical domains. This
violates Shannon's Efficiency principle — the cognitive load of navigating a single file exceeds the
information density of any one class.

### 2. Russell Violation: Semiring Definitions Are Scattered

Semiring classes are defined across three separate files:

| File          | Semiring Classes      |
|:--------------|:----------------------|
| `semiring.py` | 21 classes            |
| `clifford.py` | `CliffordSemiring`    |
| `galois.py`   | `GaloisFieldSemiring` |

A user looking for "all semirings" must search three files. This breaks Russell's Consistency — the
architecture contains a structural contradiction where semiring subclasses live outside the semiring module.

## Rationale

### Why This Specific Taxonomy?

The file already uses `# region` markers that reveal the author's original mental categories. These map
naturally to sub-modules:

| Existing `# region` Marker                  | Proposed Sub-Module | Classes                                                                                                                                                      |
|:--------------------------------------------|:--------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `# region Protocol`                         | `_base.py`          | `Semiring` Protocol, `catalog()`                                                                                                                             |
| `# region Arithmetic`                       | `arithmetic.py`     | `StandardSemiring`                                                                                                                                           |
| `# region Optimization`                     | `optimization.py`   | `TropicalSemiring`, `ArcticSemiring`, `ViterbiSemiring`, `ReliabilitySemiring`, `BottleneckSemiring`, `MinTimesSemiring`                                     |
| `# region Logic`                            | `logic.py`          | `BooleanSemiring`, `LukasiewiczSemiring`, `DigitalSemiring`                                                                                                  |
| `# region Probability & Statistics`         | `statistical.py`    | `LogSemiring`, `ExpectationSemiring`, `VarianceSemiring`, `DualNumberSemiring`                                                                               |
| `# region Structures`                       | `algebraic.py`      | `StringSemiring`, `KCollapsedSemiring`, `MonoidAlgebraSemiring`, `QuotientMonoidAlgebraSemiring`, `KnotSemiring`, `PolynomialSemiring`, `ProvenanceSemiring` |
| *(scattered in `clifford.py`, `galois.py`)* | `algebraic.py`      | `CliffordSemiring`, `GaloisFieldSemiring`                                                                                                                    |

### Council Framework Alignment

| Pillar                    | How This Proposal Aligns                                                         |
|:--------------------------|:---------------------------------------------------------------------------------|
| **Symmetry (Noether)**    | `_base.py` holds the protocol axis; all others orbit it symmetrically            |
| **Efficiency (Shannon)**  | Each file holds 1–8 related classes instead of 23 unrelated ones                 |
| **Clarity (Feynman)**     | A user can navigate to `semiring/optimization.py` to find path-problem semirings |
| **Consistency (Russell)** | All semiring definitions live under one namespace — no scatter                   |
| **Safety (Golem)**        | Zero breakage via `__init__.py` re-exports                                       |
| **Harmony (Steward)**     | Follows existing `# region` markers — minimal conceptual friction                |

## Specification

### Target Directory Layout

```text
src/algebrax/semiring/
├── __init__.py              Re-exports all classes (backward compatible)
├── _base.py                 Semiring Protocol + TypeVars + catalog()
├── arithmetic.py            StandardSemiring
├── optimization.py          Tropical, Arctic, Viterbi, Reliability, Bottleneck, MinTimes
├── logic.py                 Boolean, Lukasiewicz, Digital
├── statistical.py           Log, Expectation, Variance, DualNumber
└── algebraic.py             String, KCollapsed, MonoidAlgebra, QuotientMonoidAlgebra,
                             Polynomial, Knot, Provenance, Clifford, Galois
```

### `semiring/__init__.py` (Full Re-Export)

```python
"""Semiring namespace — all classes available from algebrax.semiring."""

from algebrax.semiring._base import Semiring
from algebrax.semiring.algebraic import (
    CliffordSemiring,
    GaloisFieldSemiring,
    KCollapsedSemiring,
    KnotSemiring,
    MonoidAlgebraSemiring,
    PolynomialSemiring,
    ProvenanceSemiring,
    QuotientMonoidAlgebraSemiring,
    StringSemiring,
)
from algebrax.semiring.arithmetic import StandardSemiring
from algebrax.semiring.logic import BooleanSemiring, DigitalSemiring, LukasiewiczSemiring
from algebrax.semiring.optimization import (
    ArcticSemiring,
    BottleneckSemiring,
    MinTimesSemiring,
    ReliabilitySemiring,
    TropicalSemiring,
    ViterbiSemiring,
)
from algebrax.semiring.statistical import (
    DualNumberSemiring,
    ExpectationSemiring,
    LogSemiring,
    VarianceSemiring,
)
```

### Impact on `clifford.py` and `galois.py`

`CliffordSemiring` and `GaloisFieldSemiring` move into `semiring/algebraic.py`. The existing
`src/algebrax/clifford.py` and `src/algebrax/galois.py` become thin application modules containing
only domain-specific helper functions:

| File          | Keeps                                     | Moves to `semiring/algebraic.py` |
|:--------------|:------------------------------------------|:---------------------------------|
| `clifford.py` | `geometric_product()`, `rotor_rotation()` | `CliffordSemiring`               |
| `galois.py`   | `gf_matrix_mul()`                         | `GaloisFieldSemiring`            |

These helpers import `CliffordSemiring` / `GaloisFieldSemiring` from the semiring namespace.

## Backwards Compatibility

**Zero breakage.** All existing import paths continue to work:

```python
# These all continue to work unchanged:
from algebrax.semiring import TropicalSemiring        # ✅ via __init__.py re-export
from algebrax.semiring import CliffordSemiring         # ✅ via __init__.py re-export
from algebrax import CliffordSemiring                  # ✅ via algebrax.__init__.py
from algebrax.clifford import CliffordSemiring         # ✅ via thin wrapper re-export
```

## Deliverables

1. **Namespace Package**: `src/algebrax/semiring/` directory with 7 sub-modules.
2. **Backward-Compatible Re-Exports**: `semiring/__init__.py` re-exporting all 23 semiring classes.
3. **Consolidated Clifford & Galois**: `CliffordSemiring` and `GaloisFieldSemiring` moved into
   `semiring/algebraic.py`; `clifford.py` and `galois.py` become thin application wrappers.
4. **Updated Tests**: All 249+ existing tests pass without modification.
5. **Linter Clean**: `ruff check` passes with 0 errors.

## Change Log

* **2026-08-02:**
    * Initial Draft.
