---
title: "EP-0191: Rings, Fields, Modules & Exact Matrix Solvers"
description: "Introduce first-class Ring, Field, and Module protocols and generalize matrix solvers to exact rational and Galois arithmetic."
icon: lucide/box
status: draft
---

# EP-0191: Rings, Fields, Modules & Exact Matrix Solvers

| Field        | Value                                                        |
|:-------------|:-------------------------------------------------------------|
| **EP**       | 0191                                                         |
| **Title**    | Rings, Fields, Modules & Exact Matrix Solvers                |
| **Author**   | Eran Rivlis & Antigravity                                    |
| **Sponsor**  | Council Framework                                            |
| **Delegate** | ⚖️ Noether (Symmetry & Invariants) & ⚡ Shannon (Efficiency) |
| **Status**   | Draft                                                        |
| **Type**     | Standards Track                                              |
| **Created**  | 2026-10-25                                                   |
| **Updated**  | 2026-10-25                                                   |

## Abstract

This proposal extends the algebraic hierarchy initiated
in [EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md) to two-operation and two-sorted structures:
**Rings**, **Commutative Rings**, **Division Rings** (Skew Fields), **Fields**, **Semimodules**, and **Modules**. By
elevating `Ring` and `Field` to first-class protocols, AlgebraX can cleanly re-root `Semiring` into the hierarchy,
support additive negation (`neg`, `-`) and multiplicative division (`inv`, `/`), and generalize sparse matrix algorithms
(`lu_decompose`, `inv`, `det`, `solve_triangular`) to execute identically over exact rational fractions
(`Field[Fraction]`), Galois finite fields (`Field[GF(p)]`), and floating-point numbers without code duplication.

## Motivation

Currently, AlgebraX's matrix decomposition and inversion routines (`lu_decompose`, `cholesky_decompose`, `qr_decompose`
in `algebrax.matrix.decompose`) rely implicitly on Python's built-in floating-point division `/` and subtraction `-`.

This presents major algebraic shortcomings:

1. **Inability to Solve Exactly over $\mathbb{Q}$**: Solving $A x = b$ with exact rational fractions
   (`fractions.Fraction`) often fails or produces approximate floats because solvers cannot query a formal `Field[V]`
   interface for exact division and additive negation.
2. **Duplication in Finite Field Linear Algebra**: `algebrax.galois` implements finite field matrix operations
   (`gf_matrix_mul`, `gf_matrix_inv`), but these are standalone functions that duplicate matrix logic rather than
   running through polymorphic matrix decomposition pipelines.
3. **Absence of True Ring Structures**: Structures with additive inverses (such as polynomials, Laurent series, Clifford
   multivectors, and integer matrices) are true **Rings**, but are forced to mask as `Semiring` where subtraction is
   unsupported or undefined.
4. **Lack of Abstract Scalar-Vector Actions**: In linear algebra, a vector space is a set $V$ acted upon by a field $F$
   via scalar multiplication $\cdot: F \times V \to V$. In `algebrax`, scalar actions (`vec_scale`) are hardcoded to
   numeric multiplication rather than an abstract **Module** or **Semimodule** action.

## Rationale

### Council Alignment

- **⚖️ Noether (Algebraic Invariants & Symmetry)**: Formally captures additive inverses ($a \oplus (-a) = \mathbf{0}$)
  and multiplicative division ($a \otimes a^{-1} = \mathbf{1}$), ensuring that linear algebra solvers preserve exact
  invariants without floating-point drift.
- **⚡ Shannon (Zero Bloat & Unified Algorithms)**: Eliminates code duplication across `algebrax.matrix`,
  `algebrax.galois`, and rational arithmetic. A single Gaussian elimination or LU decomposition solver operates
  generically over any carrier satisfying `Field[V]`.
- **🛡️ Golem (Contract Hardening)**: Type signatures for linear solvers declare `field: Field[V]`, providing static
  compiler guarantees that division by non-zero elements is algebraically valid.
- **🧩 Russell (Categorical Precision)**: Re-roots `Semiring` as an `AddCommMonoid` + `Monoid` with distributivity, while
  `Ring` adds `AddGroup` negation, completing the Lean 4 / Bourbaki hierarchy.

## Specification

### 1. Two-Operation Protocols (`src/algebrax/algebra/_ring.py`, `_field.py`)

#### Ring and Commutative Ring

```python
from typing import Protocol, TypeVar, runtime_checkable
from algebrax.algebra._monoid import AddCommMonoid, Monoid
from algebrax.algebra._group import AddCommGroup

V = TypeVar('V')


@runtime_checkable
class Ring(AddCommGroup[V], Monoid[V], Protocol[V]):
    """A mathematical Ring (R, +, *, 0, 1) with additive negation and distributivity."""

    def neg(self, a: V) -> V: ...

    def sub(self, a: V, b: V) -> V: ...

    def mul(self, a: V, b: V) -> V: ...


@runtime_checkable
class CommutativeRing(Ring[V], Protocol[V]):
    """A ring whose multiplication is commutative: mul(a, b) == mul(b, a)."""
    ...
```

#### Division Ring (Skew Field) and Field

```python
@runtime_checkable
class DivisionRing(Ring[V], Protocol[V]):
    """A non-zero ring where every non-zero element has a multiplicative inverse."""

    def inv(self, a: V) -> V: ...

    def div(self, a: V, b: V) -> V: ...


@runtime_checkable
class Field(DivisionRing[V], CommutativeRing[V], Protocol[V]):
    """A field is a commutative division ring (e.g. Q, R, C, GF(p))."""
    ...
```

### 2. Two-Sorted Action Protocols (`src/algebrax/algebra/_module.py`)

```python
R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class Semimodule(AddCommMonoid[M], Protocol[R, M]):
    """A commutative additive monoid M with scalar action by semiring R: R x M -> M."""

    def smul(self, r: R, m: M) -> M: ...


@runtime_checkable
class Module(Semimodule[R, M], AddCommGroup[M], Protocol[R, M]):
    """An abelian group M with scalar action by ring R."""
    ...


@runtime_checkable
class VectorSpace(Module[R, M], Protocol[R, M]):
    """A module over a field R."""
    ...


@runtime_checkable
class Algebra(Module[R, M], Ring[M], Protocol[R, M]):
    """A ring M that is also an R-module such that scalar multiplication associates with ring multiplication."""
    ...
```

### 3. Re-rooting `Semiring` in `src/algebrax/semiring/_base.py`

`Semiring` is updated to inherit from `AddCommMonoid[V]` and `Protocol[V]`:

```python
from algebrax.algebra import AddCommMonoid


class Semiring(AddCommMonoid[V], Protocol[V]):
    @property
    def one(self) -> V: ...

    def mul(self, a: V, b: V) -> V: ...

    def nsum(self, a: V, n: int) -> V: ...

    def power(self, a: V, n: int) -> V: ...

    def star(self, a: V) -> V: ...
```

### 4. Generalizing Matrix Decompositions & Solvers

In `algebrax.matrix.decompose` and `algebrax.matrix.solve`:

```python
def lu_decompose(
        matrix: SparseMatrix[R, V],
        *,
        field: Field[V] | None = None,
        tol: float = 1e-14,
) -> tuple[SparseMatrix[R, V], SparseMatrix[R, V], SparseMatrix[R, V]]:
    """Compute PA = LU decomposition generically over any Field (float, Fraction, GF(p))."""
    ...


def solve_triangular(
        matrix: SparseMatrix[R, V],
        rhs: SparseVector[R, V],
        *,
        field: Field[V] | None = None,
        lower: bool = True,
) -> SparseVector[R, V]:
    """Solve L x = b or U x = b using forward/backward substitution via field.div()."""
    ...
```

When `field` is omitted, defaults to `StandardField(float)`. When `field=StandardField(Fraction)` is passed, computation
runs in exact rational arithmetic with zero rounding error.

## Backwards Compatibility

100% backwards-compatible:

- Existing code calling `lu_decompose(A)` with floating-point matrices continues to work identically with zero
  behavioral changes.
- All existing `Semiring` classes remain functional and unchanged.
- `StandardSemiring(float)` and `ModularSemiring(p)` naturally satisfy `Field` and `Ring` protocols.

## How to Teach This / Documentation Plan

1. **User Guide**: Add `docs/guide/algebra/rings_and_fields.md` showcasing exact rational Gaussian elimination and
   finite field matrix inversion.
2. **Verification Suite**: Add property-based axiom tests in `algebrax.verification` for `Ring`, `Field`, and `Module`
   laws.
3. **Recipes**: Add a recipe demonstrating exact linear system solving over $\mathbb{Q}$ and $\operatorname{GF} (2^8)$
   (AES cryptographic S-box matrix inversion).

## Reference Implementation

A complete analysis and architectural blueprint is provided in
[EXP-0004](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0004-pure-algebraic-hierarchy/README.md).

## Rejected Ideas

1. **Python Operator Overloading for Abstract Fields**:
    - *Rejected*: Requiring values to override `__add__` and `__mul__` would preclude using primitive types like `int`,
      `float`, and `tuple` directly as field elements. The dictionary/carrier-passing style (`field.add(a, b)`,
      `field.div(a, b)`) preserves zero-wrapping purity.
2. **Separate Solver Functions for Fractions (`lu_decompose_exact`)**:
    - *Rejected*: Violates the Shannon and Noether principles of polymorphic linear algebra. A single parameter
      `field=...` unifies all numeric representations under one tested implementation.

## Open Questions

- [ ] Should `Field` provide a `char` (characteristic) property?
- [ ] Should `Matrix` inversion default to exact arithmetic when elements are `fractions.Fraction` or `sympy.Rational`?

## Change Log

* **2026-10-25:** Initial Draft.
