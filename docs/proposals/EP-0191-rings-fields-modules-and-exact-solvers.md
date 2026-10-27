---
title: "EP-0191: Rings, Fields, Modules & Exact Matrix Solvers"
description: "Introduce first-class Ring, Field, and Module protocols and generalize matrix solvers to exact rational and Galois arithmetic."
icon: lucide/box
status: final
---

# EP-0191: Rings, Fields, Modules & Exact Matrix Solvers

| Field | Value |
| :--- | :--- |
| **EP** | 0191 |
| **Title** | Rings, Fields, Modules & Exact Matrix Solvers |
| **Author** | Eran Rivlis & Antigravity |
| **Sponsor** | Council Framework |
| **Delegate** | ⚖️ Noether (Symmetry & Invariants) & ⚡ Shannon (Efficiency) |
| **Status** | Final |
| **Type** | Standards Track |
| **Created** | 2026-10-25 |
| **Updated** | 2026-10-27 |

## Abstract

This proposal extends the algebraic hierarchy initiated in [EP-0190](EP-0190-granular-algebraic-hierarchy-magmas-monoids-groups.md) to two-operation and two-sorted structures: **Rings**, **Commutative Rings**, **Non-Associative Rings/Algebras**, **Division Rings** (Skew Fields), **Fields**, **Semimodules**, and **Modules**. By defining the foundational `Semiring` protocol in `algebrax.algebra._semiring` and elevating `Ring` and `Field` to first-class protocols, AlgebraX cleanly resolves circular imports, supports additive negation (`neg`, `-`) and multiplicative division (`inv`, `/`), and generalizes sparse matrix algorithms (`lu_decompose`, `inv`, `det`, `solve_triangular`) to execute identically over exact rational fractions (`Field[Fraction]`), Galois finite fields (`Field[GF(p)]`), and floating-point numbers directly on native sparse dictionary carriers without code duplication.

## Motivation

Currently, AlgebraX's matrix decomposition and inversion routines (`lu_decompose`, `cholesky_decompose`, `qr_decompose` in `algebrax.matrix.decompose`) rely implicitly on Python's built-in floating-point division `/` and subtraction `-`.

This presents major algebraic shortcomings:

1. **Inability to Solve Exactly over $\mathbb{Q}$**: Solving $A x = b$ with exact rational fractions (`fractions.Fraction`) fails or produces approximate floats because solvers cannot query a formal `Field[V]` interface for exact division and additive negation.
2. **Duplication in Finite Field Linear Algebra**: `algebrax.galois` implements finite field matrix operations (`gf_matrix_mul`, `gf_matrix_inv`), but these duplicate matrix logic rather than running through polymorphic matrix decomposition pipelines.
3. **Absence of True Ring Structures**: Structures with additive inverses (such as polynomials, Laurent series, Clifford multivectors, and integer matrices) are true **Rings**, but are forced to mask as `Semiring` where subtraction is unsupported or undefined.
4. **Lack of Abstract Scalar-Vector Actions**: In linear algebra, a vector space is a set $V$ acted upon by a field $F$ via scalar multiplication $\cdot: F \times V \to V$. In `algebrax`, scalar actions (`vec_scale`) are hardcoded to numeric multiplication rather than an abstract **Module** or **Semimodule** action.

### The Mental Model (The Freshman Test)

- **`Ring` (Arithmetic with Negative Numbers)**: A system where you can add, subtract, and multiply (e.g. integers $\mathbb{Z}$, polynomials $\mathbb{R}[x]$, matrix rings $M_n(\mathbb{R})$). You can always cancel terms ($a - a = 0$).
- **`Field` (The Complete Arithmetic Toolbox)**: A ring where you can also divide by any non-zero element (e.g. rational numbers $\mathbb{Q}$, real numbers $\mathbb{R}$, complex numbers $\mathbb{C}$, finite Galois fields $\mathbb{F}_p$). A field is the **exact requirement for Gaussian elimination and linear algebra**.
- **`Module` (Vectors with General Weights)**: A generalization of vector spaces where the scalars come from a ring instead of a field. For example, sparse vectors with integer coefficients form a $\mathbb{Z}$-module.

## Rationale & Council Alignment

- **⚖️ Noether (Algebraic Invariants & Symmetry)**: Formally captures additive inverses ($a \oplus (-a) = \mathbf{0}$) and multiplicative division ($a \otimes a^{-1} = \mathbf{1}$). Solvers check exact zero via `not field.is_zero(pivot)` rather than floating-point thresholds (`abs(p) > 1e-14`), preserving exact rational and finite-field invariants.
- **⚡ Shannon (Zero Bloat & Performance)**:
  - *Native Float Fast-Path*: When `field is None`, solvers bypass protocol dispatch and execute native CPython floating-point bytecode directly.
  - *Inversion Hoisting*: Solvers compute `inv_p = field.inv(pivot)` once per pivot row, replacing $N$ division operations with $N$ multiplications.
  - *Inner Zero-Skipping*: Guard row updates with `if factor == field_zero: continue`, eliminating over 90% of arithmetic in sparse matrices.
- **🛡️ The Golem (Safety & Contract Hardening)**: Division by zero (`field.div(a, field.zero)` or `field.inv(field.zero)`) unconditionally raises `ZeroDivisionError`. Singular matrices during decomposition raise `SingularMatrixError` instead of returning silent corruptions.
- **🧩 Russell (Taxonomy & Circular-Import Prevention)**: The abstract `Semiring` protocol is defined canonically in `src/algebrax/algebra/_semiring.py` (which only imports from `_monoid.py`), and re-exported in `algebrax.semiring`. `algebrax.algebra` contains zero imports from `algebrax.semiring`.
- **🧭 The Explorer (Non-Associative Horizons)**: Supports `NonAssocRing` and `NonAssocAlgebra` so Lie algebras (Jacobi bracket) and octonions slot into the taxonomy naturally without forcing false associativity.

## Specification

### 1. Two-Operation Protocols (`src/algebrax/algebra/_ring.py`, `_field.py`, `_semiring.py`)

#### Base Semiring Protocol (`_semiring.py`)

```python
from typing import Protocol, TypeVar, runtime_checkable
from algebrax.algebra._monoid import AddCommMonoid, Monoid

V = TypeVar('V')


@runtime_checkable
class Semiring(AddCommMonoid[V], Monoid[V], Protocol[V]):
    r"""A mathematical Semiring $(S, \oplus, \otimes, \mathbf{0}, \mathbf{1})$."""

    def nsum(self, a: V, n: int) -> V: ...
    def power(self, a: V, n: int) -> V: ...
    def star(self, a: V) -> V: ...
```

#### Ring and Commutative Ring (`_ring.py`)

```python
from algebrax.algebra._magma import Magma
from algebrax.algebra._group import AddCommGroup


@runtime_checkable
class NonAssocRing(AddCommGroup[V], Magma[V], Protocol[V]):
    r"""Ring with possibly non-associative multiplication satisfying distributivity (e.g. Lie algebras)."""

    ...


@runtime_checkable
class Ring(NonAssocRing[V], Monoid[V], Protocol[V]):
    r"""An associative unital ring $(R, +, \cdot, 0, 1)$ with additive negation."""

    def neg(self, a: V) -> V: ...
    def sub(self, a: V, b: V) -> V:
        return self.add(a, self.neg(b))


@runtime_checkable
class CommRing(Ring[V], Protocol[V]):
    r"""A ring with commutative multiplication: $a \cdot b = b \cdot a$."""

    is_commutative: bool = True


CommutativeRing = CommRing
```

#### Division Ring (`_ring.py`) and Field (`_field.py`)

*Note*: Following Emmy Noether's guidance, `DivisionRing` is defined canonically in `_ring.py` and inherits from `Ring`, **not** `Group`, because $\mathbf{0}$ has no multiplicative inverse. Its non-zero elements form the group of units $R^\times = R \setminus \{\mathbf{0}\}$. `Field` in `_field.py` is the commutative specialization of `DivisionRing`.

```python
@runtime_checkable
class DivisionRing(Ring[V], Protocol[V]):
    r"""A non-zero ring where every non-zero element has a multiplicative inverse."""

    def inv(self, a: V) -> V: ...
    def div(self, a: V, b: V) -> V:
        return self.mul(a, self.inv(b))

    def is_zero(self, a: V) -> bool:
        return a == self.zero


@runtime_checkable
class Field(DivisionRing[V], CommRing[V], Protocol[V]):
    r"""A commutative division ring $(F, +, \cdot, 0, 1, ^{-1})$ (e.g. $\mathbb{Q}, \mathbb{R}, \mathbb{C}, \mathbb{F}_p$)."""

    ...
```

*Contract Invariant*: If `is_zero(b)` is true, `div(a, b)` and `inv(b)` MUST raise `ZeroDivisionError`.

### 2. Two-Sorted Action Protocols (`src/algebrax/algebra/_module.py`)

```python
R = TypeVar('R')
M = TypeVar('M')


@runtime_checkable
class Semimodule(AddCommMonoid[M], Protocol[R, M]):
    r"""A commutative additive monoid M with scalar action by semiring R: $R \times M \to M$."""

    def smul(self, r: R, m: M) -> M: ...


@runtime_checkable
class Module(Semimodule[R, M], AddCommGroup[M], Protocol[R, M]):
    r"""An abelian group M with scalar action by ring R."""

    ...


@runtime_checkable
class VectorSpace(Module[R, M], Protocol[R, M]):
    r"""A module over a field R."""

    ...


@runtime_checkable
class NonAssocAlgebra(Module[R, M], NonAssocRing[M], Protocol[R, M]):
    r"""A module M that is also a non-associative ring satisfying scalar bilinearity."""

    ...


@runtime_checkable
class Algebra(NonAssocAlgebra[R, M], Ring[M], Protocol[R, M]):
    r"""An associative ring M that is also an R-module: $r \cdot (a \cdot b) = (r \cdot a) \cdot b = a \cdot (r \cdot b)$."""

    ...
```

### 3. Native Sparse Dictionary Carriers

AlgebraX upholds the fundamental principle: **the sparse dictionary is the carrier**.
- Sparse Vectors: `SparseVector[K, V] = dict[K, V]`
- Sparse Matrices: `SparseMatrix[K, V] = dict[K, dict[K, V]]`

Linear algebra solvers never box numbers into wrapper classes. The `Field[V]` operator instance is passed as an optional typeclass argument.

### 4. Generalizing Matrix Decompositions & Solvers

In `algebrax.matrix.decompose` and `solve`:

```python
class SingularMatrixError(ArithmeticError, ValueError):
    """Raised when a matrix is singular or has no unique inverse/decomposition."""

    pass


def lu_decompose(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-14,
) -> tuple[SparseMatrix[K, V], SparseMatrix[K, V], SparseMatrix[K, V]]:
    """Compute PA = LU decomposition generically over any Field (float, Fraction, GF(p)).

    Performance Guarantees:
    - Native float fast-path when field is None.
    - Pivot inversion hoisting: computes inv_pivot = field.inv(pivot) once per row.
    - Inner zero-skipping: if factor == field.zero, skip column elimination.
    - Decoupled singularity: checks not field.is_zero(pivot), never corrupting exact fractions.
    """
    ...


def solve_triangular(
    matrix: SparseMatrix[K, V],
    rhs: SparseVector[K, V],
    *,
    field: Field[V] | None = None,
    lower: bool = True,
) -> SparseVector[K, V]:
    """Solve L x = b or U x = b using forward/backward substitution via field.div()."""
    ...
```

### 5. Runnable Example: Exact Rational Arithmetic vs. Floating-Point Drift

```python
from fractions import Fraction
from algebrax.matrix.decompose import lu_decompose
from algebrax.algebra import StandardField

# 2x2 Hilbert matrix:
# [ 1/2   1/3 ]
# [ 1/3   1/4 ]
hilbert_2 = {
    0: {0: Fraction(1, 2), 1: Fraction(1, 3)},
    1: {0: Fraction(1, 3), 1: Fraction(1, 4)},
}

# Exact LU decomposition over Q:
P, L, U = lu_decompose(hilbert_2, field=StandardField(Fraction))

# U[1][1] is exactly Fraction(1, 36), det(A) = 1/2 * 1/36 = 1/72 (Exact!)
# Floating point arithmetic gives 0.013888888888888881 with trailing rounding errors.
```

## Backwards Compatibility

100% backwards-compatible:
- Existing code calling `lu_decompose(A)` with floating-point matrices continues to work identically with zero behavioral changes or performance loss.
- `from algebrax.semiring import Semiring` continues to work seamlessly via re-export.
- `StandardSemiring(float)` and `ModularSemiring(p)` naturally satisfy `Field` and `Ring` protocols.

## How to Teach This / Documentation Plan

1. **User Guide**: Author `docs/guide/algebra/rings_and_fields.md` showcasing exact rational Gaussian elimination and finite field matrix inversion.
2. **Verification Suite**: Add property-based axiom tests in `algebrax.verification` for `Ring`, `Field`, and `Module` laws.
3. **Recipes**: Add a recipe demonstrating exact linear system solving over $\mathbb{Q}$ and $\operatorname{GF}(2^8)$ (AES cryptographic S-box matrix inversion).

## Reference Implementation

A complete analysis and architectural blueprint is provided in
[EXP-0004](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0004-pure-algebraic-hierarchy/README.md).

## Rejected Ideas

1. **`DivisionRing` inheriting from `Group`**:
   - *Rejected*: In any division ring or field, $\mathbf{0}$ has no multiplicative inverse. Inheriting from `Group` breaks the fundamental invariant that division by zero is undefined.
2. **Python Operator Overloading for Abstract Fields**:
   - *Rejected*: Requiring values to override `__add__` and `__mul__` would preclude using primitive types like `int`, `float`, and `Fraction` directly as field elements. The dictionary/carrier-passing style (`field.add(a, b)`, `field.div(a, b)`) preserves zero-wrapping purity.
3. **Separate Solver Functions for Fractions (`lu_decompose_exact`)**:
   - *Rejected*: Violates the Shannon and Noether principles of polymorphic linear algebra. A single parameter `field=...` unifies all numeric representations under one tested implementation.

## Open Questions

- [ ] Should `Field` provide an optional `characteristic: int | None` attribute for distinguishing finite characteristic $p$ from characteristic 0?
- [ ] Should `Matrix` inversion automatically default to exact arithmetic when all dictionary elements are `fractions.Fraction` or `sympy.Rational`?

## Change Log

* **2026-10-25:** Initial Draft.
* **2026-10-25:** Accepted following Council review (incorporating Shannon solver performance optimizations, Golem `ZeroDivisionError`/`SingularMatrixError` contracts, Russell circular-import prevention, Noether division ring invariants, and Explorer non-associative rings).
