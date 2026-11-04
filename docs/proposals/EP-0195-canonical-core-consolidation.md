---
title: "EP-0195: Canonical Core Consolidation & Verification Suite Alignment"
description: "Purge all backward-compatibility aliases, re-export shims, and legacy facades from the core algebraic engine and align all test suites with canonical Lean 4 Mathlib naming."
icon: lucide/shield-check
status: draft
---

# EP-0195: Canonical Core Consolidation & Verification Suite Alignment

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0195                                                                              |
| **Title**         | Canonical Core Consolidation & Verification Suite Alignment                       |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Council Framework                                                                 |
| **Delegate**      | 🧩 Russell (Taxonomy & Rigor), ✂️ Shannon (Parsimony), 🧪 Popper (Falsifiability) |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-11-04                                                                        |
| **Updated**       | 2026-11-04                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

## Abstract

This proposal enacts the recommendations of **EXP-0007: Canonical Surface Consolidation & Zero-Alias Purge** across the
core engine (`src/algebrax/`) and verification test suite (`tests/`). It purges all 14 identified backward-compatibility
aliases, duplicate re-exports, and legacy facade modules, establishing a strict **One Concept = One Canonical Symbol =
One Canonical Module** invariant. Concurrently, all 622 tests in `tests/algebrax/` and `tests/verifications/` are
refactored to exercise canonical symbols directly, ensuring 100% green CI test execution without relying on transitional
shims.

## Motivation

During Phases 1 through 6, rapid promotions of algebraic structures left behind compatibility sediment:

1. **Multi-Protocol Structures under Multiple Aliases**: `DualNumberAlgebra`, `PolynomialAlgebra`, and `CliffordAlgebra`
   are currently re-exported as `*Semiring` and `*Ring`, confusing users as to whether these are distinct types.
2. **Protocol Synonym Duplication**: `CommGroup`, `CommMonoid`, and `CommRing` coexist with English synonyms
   (`AbelianGroup`, `CommutativeMonoid`, `AbelianRing`, `CommutativeRing`), diluting our commitment to Lean 4 Mathlib
   nomenclature.
3. **Ghost Facades**: `src/algebrax/homology.py` exists solely as a 92-line duplicate facade over `algebrax.topology`,
   causing 15 test files to bypass the canonical `algebrax.topology` package.
4. **Tooling Redundancy**: `src/algebrax/verify.py` duplicates functionality already provided by `algebrax.verification`
   and `algebrax.__main__`.

Because `algebrax` is in pre-v1.0 development, backward compatibility shims serve only our own internal test suite.
Maintaining them creates technical drag before embarking on Phase 7 (Categorical Foundations & Enriched Matrices).

## Rationale & Council Alignment

- **Bertrand Russell (Unique Designation)**: Rejects linguistic synonyms in a formal system. A mathematical structure
  must have a unique identifier.
- **Claude Shannon (Minimal Entropy)**: Removing redundant aliases eliminates cognitive and computational noise from
  module namespaces and autocomplete indexes.
- **Karl Popper (Strict Verification)**: Tests must exercise the canonical public interface, not backward-compatibility
  scaffolding.
- **The Golem (Defensive Execution)**: Pre-v1.0 is the only window for zero-debt breaking cleanups without external
  disruption.

## Specification

### 1. Engine Cleanups (`src/algebrax/`)

The following aliases and files will be removed or consolidated:

| Target File                            | Removed Alias / File                                       | Canonical Replacement                               |
|:---------------------------------------|:-----------------------------------------------------------|:----------------------------------------------------|
| `src/algebrax/clifford.py`             | `CliffordSemiring = CliffordAlgebra`                       | `CliffordAlgebra`                                   |
| `src/algebrax/clifford.py`             | `GeneralizedCliffordSemiring = GeneralizedCliffordAlgebra` | `GeneralizedCliffordAlgebra`                        |
| `src/algebrax/clifford.py`             | `QuantumCliffordSemiring = QuantumCliffordAlgebra`         | `QuantumCliffordAlgebra`                            |
| `src/algebrax/algebra/_dual.py`        | `DualNumberRing = DualNumberAlgebra`                       | `DualNumberAlgebra`                                 |
| `src/algebrax/algebra/_dual.py`        | `DualNumberSemiring = DualNumberAlgebra`                   | `DualNumberAlgebra`                                 |
| `src/algebrax/algebra/_polynomial.py`  | `PolynomialRing = PolynomialAlgebra`                       | `PolynomialAlgebra`                                 |
| `src/algebrax/algebra/_polynomial.py`  | `PolynomialSemiring = PolynomialAlgebra`                   | `PolynomialAlgebra`                                 |
| `src/algebrax/algebra/_group.py`       | `AbelianGroup = CommGroup`                                 | `CommGroup`                                         |
| `src/algebrax/algebra/_monoid.py`      | `CommutativeMonoid = CommMonoid`                           | `CommMonoid`                                        |
| `src/algebrax/algebra/_ring.py`        | `AbelianRing = CommRing`                                   | `CommRing`                                          |
| `src/algebrax/algebra/_ring.py`        | `CommutativeRing = CommRing`                               | `CommRing`                                          |
| `src/algebrax/algebra/_mixins.py`      | `HasSMul = HasScale`                                       | `HasScale`                                          |
| `src/algebrax/semiring/statistical.py` | `BivariateCovarianceSemiring = BivariateVarianceSemiring`  | `BivariateVarianceSemiring`                         |
| `src/algebrax/matrix/decompose.py`     | `lu = lu_decompose`                                        | `lu_decompose`                                      |
| `src/algebrax/homology.py`             | Entire facade file deleted                                 | `algebrax.topology`                                 |
| `src/algebrax/verify.py`               | Standalone script deleted                                  | Use `python -m algebrax` or `algebrax.verification` |
| `src/algebrax/__init__.py`             | Purge `homology` and `verify` from root `__all__`          | `algebrax.topology`                                 |

### 2. Semiring Catalog Invariant

In `algebrax.semiring.Semiring.catalog()`:

- Ensure each of the 34 semirings maps to a single canonical key.
- `'BivariateCovariance'` alias entry removed; `'BivariateVariance'` remains the unique registration for
  `BivariateVarianceSemiring`.

### 3. Verification Suite Refactoring (`tests/`)

Every test file currently importing or asserting alias names will be mechanically updated:

1. `tests/algebrax/test_homology.py`: Change all imports from `algebrax.homology` to `algebrax.topology`.
2. `tests/algebrax/test_domain_unification.py`: Remove assertions that check identity between aliases
   (`assert PolynomialRing is PolynomialAlgebra`). Assert canonical classes directly.
3. `tests/algebrax/test_type_safety.py`, `tests/algebrax/test_algebra.py`, `tests/algebrax/test_rings_fields.py`: Update
   `AbelianGroup`, `CommutativeRing`, `CommutativeMonoid`, `HasSMul` to `CommGroup`, `CommRing`, `CommMonoid`,
   `HasScale`.
4. `tests/algebrax/test_clifford.py`, `tests/algebrax/test_lie.py`: Update `CliffordSemiring` $\to$ `CliffordAlgebra`.
5. `tests/algebrax/test_verification.py`: Remove tests for `algebrax.verify` CLI script, redirecting verification tests
   to `algebrax.verification`.
6. `tests/verifications/test_differential_statistical_semirings.py`: Update `BivariateCovarianceSemiring` $\to$
   `BivariateVarianceSemiring`.
7. `tests/algebrax/test_matrix_decompose.py`, `tests/algebrax/test_numerical_stability.py`: Ensure `lu_decompose` is
   called directly.

## Backwards Compatibility

This is an intentional, breaking cleanup of pre-release internal aliases. By executing this before Phase 7 and v1.0, we
establish a permanent, immutable public API contract. External consumers targeting v1.0 will have a single, unambiguous
way to import and use every mathematical construct.

## How to Teach This / Documentation Plan

- No deprecation warnings or migration guides are needed in user docs, in accordance with the principle that user-facing
  docs remain clean, self-contained, and free of planning-time artifacts.
- Code examples in docs already utilize canonical forms; this EP aligns internal implementation and test suites with
  that ideal.

## Reference Implementation

1. Purge alias definitions in `src/algebrax/`.
2. Delete `src/algebrax/homology.py` and `src/algebrax/verify.py`.
3. Update `src/algebrax/__init__.py` exports.
4. Update `tests/` imports via AST/regex refactoring.
5. Execute `uv run pytest` to achieve 622 passed tests with 0 warnings.

## Rejected Ideas

- **Retain Runtime Deprecation Warnings**: Rejected because `algebrax` has no external v0 production dependents.
  Emitting warnings creates log noise in internal benchmarks and test suites without providing value.
- **Defer Purge to Post-v1.0**: Strongly rejected. Once v1.0 is released, breaking aliases requires a full major version
  deprecation cycle (v2.0). Doing it now is cheap and clean.

## Open Questions

- None. Consensus reached during EXP-0007.

## Change Log

- **2026-11-04**: Draft authored following EXP-0007 Council consensus.
