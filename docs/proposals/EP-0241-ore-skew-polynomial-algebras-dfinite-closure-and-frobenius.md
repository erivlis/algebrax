---
title: "EP-0241: Unified Ore Skew-Polynomial Algebras, D-Finite Closure & Frobenius Solvers"
description: "Unify linear differential, shift, difference, and q-difference operators into a single mode-parameterized OreAlgebra R[D; sigma, delta] with gcrd, lclm, Frobenius indicial polynomials, and companion matrices."
icon: lucide/function-square
status: draft
---

# EP-0241: Unified Ore Skew-Polynomial Algebras, D-Finite Closure & Frobenius Solvers

| Field             | Value                                                                                                  |
|:------------------|:-------------------------------------------------------------------------------------------------------|
| **EP**            | 0241                                                                                                   |
| **Title**         | Unified Ore Skew-Polynomial Algebras, D-Finite Closure & Frobenius Solvers                             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                            |
| **Sponsor**       | Core Maintainers                                                                                       |
| **Delegate**      | ⚖️ Noether (Operator Unification), ⚡ Shannon (Content Normalization) & 🔬 Popper (LCLM Oracles)       |
| **Status**        | Draft                                                                                                  |
| **Type**          | Standards Track                                                                                        |
| **Created**       | 2026-11-15                                                                                             |
| **Updated**       | 2026-11-26                                                                                             |
| **Replaces**      | —                                                                                                      |
| **Superseded-By** | —                                                                                                      |

---

## Abstract

This proposal introduces [`OreAlgebra`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md) ($R[\partial; \sigma, \delta]$), a unified non-commutative skew-polynomial operator ring parameterized by an exact base ring/field $R$, an injective endomorphism $\sigma: R \to R$, and a $\sigma$-derivation $\delta: R \to R$ satisfying $\partial \cdot r = \sigma(r)\partial + \delta(r)$. Following the **Mode vs. Type** and **Factory Method for Specialization** heuristics, a single `OreAlgebra` engine with preset classmethods (`differential`, `shift`, `difference`, `q_difference`) delivers:

1. **Unified Skew Arithmetic & Right Euclidean Division (`right_divmod`, `gcrd`, `lclm`)**: Exact greatest common right divisors and least common left multiples with mandatory primitive-part content normalization to prevent rational coefficient swell.
2. **Constructive $D$-Finite Closure (`lclm`, `symmetric_product`)**: Automatic synthesis of exact linear ODEs and recurrences annihilating sums $f + g$ and products $f \cdot g$ of holonomic functions and sequences.
3. **Frobenius Regular-Singular Analysis & Companion Matrices (`to_euler_form`, `indicial_polynomial`, `differential_companion_matrix`)**: Algebraic extraction of Frobenius exponents at regular singular points and conversion of order-$m$ Ore equations into first-order matrix systems $\partial Y = C_L Y$ (`algebrax.matrix` & `EP-0163` Magnus/BCH bridge).

---

## Motivation

In computational mathematics, linear ODEs ($\partial_x$), recurrence relations ($S_n$), finite differences ($\Delta = S_n - 1$), and $q$-difference equations ($D_q$) are traditionally implemented as four separate codebases despite obeying identical Euclidean and closure theorems:

1. **Bridging Phase 10 Shift Models to Arbitrary Linear Operators**: [`EP-0231`](EP-0231-algebraic-signal-processing-ntt-and-mobius-transforms.md) models constant-coefficient finite shift filters via commutative `CommQuotientRing`s. Polynomial-coefficient recurrences (e.g., $n S_n - (n+1)$ or Fibonacci $S_n^2 - S_n - 1$) fail to commute with $n$ and require an **Ore skew-polynomial ring**.
2. **Automatic Closure of Special Functions & Sequences**: Proving identities like $\exp(x) + \cos(x)$ or synthesizing a recurrence for $a_n = F_n + n$ requires $\operatorname{lclm}(L_1, L_2)$ over non-commutative operator rings.
3. **Algebraic Singularity Extraction Before Numeric Evaluation**: Before running numeric ODE integrators or Taylor series around a singular point like Bessel's $x^2 y'' + xy' + (x^2 - \nu^2)y = 0$, the Euler operator $\theta = x\partial_x$ extracts the exact indicial roots $\rho = \pm \nu$ purely algebraically.

---

## Rationale

Validated in [**EXP-0011**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md) (Experiments 2 and 6) and aligned with the Grand Council and **Phase 8.5 (`EP-0250`–`EP-0254`)**:

- **⚖️ Emmy Noether (Operator Unification & Symplectic/Matrix Correspondence)**:
  Differential ($\sigma = \mathrm{id}, \delta = \frac{d}{dx}$), shift ($\sigma(p(n)) = p(n+1), \delta = 0$), forward-difference ($\sigma = S_n, \delta = S_n - \mathrm{id}$), and $q$-dilation ($\sigma(p(x)) = p(qx), \delta = 0$) are all instances of one algebraic law $\partial r = \sigma(r)\partial + \delta(r)$. Meanwhile, `differential_companion_matrix` mirrors Phase 9's Stickelberger companion matrix (`EP-0221`), turning scalar order-$m$ Ore operators into matrix systems. `OreAlgebra` strictly inherits non-commutative `Ring` (never `CommRing`/`LawCommutative`, consistent with `EP-0250`), and exact `Fraction` scalars align with `EP-0251`'s widened `typing.N`.
- **⚡ Claude Shannon (Primitive Content Reduction, Sparse Operators & Shared Exact Kernels)**:
  Ore operators are unboxed `dict[int, R]` mappings (operator order $\to$ coefficient in $R$). As observed during `EXP-0011` prototyping, naive pseudo-division accumulates scalar polynomial factors in `lclm` and `gcrd`; mandatory primitive-part/content GCD normalization keeps intermediate coefficients minimal. Linear system solves inside `lclm`, `symmetric_product`, and `guess_ore_operator` reuse Phase 8.5 [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s consolidated `matrix.nullspace` / `sparse_rref` kernels (zero duplicated elimination loops).
- **🔬 Karl Popper (Falsifiable Divisibility & Annihilation Laws)**:
  Prototyping in `EXP-0011` immediately caught a subtle degree-bound bug in `lclm` (`deg(u1) == deg(b) - deg(gcrd)`, not `deg(a) - deg(gcrd)`). Every Ore `lclm` and `symmetric_product` output is falsifiable via exact right-divisibility (`right_divmod(L, A)[1] == 0`) and exact series/sequence residual evaluation (`max residual == 0`), adhering to Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts.
- **🛡️ The Golem (Exact Field / Domain Mandate & Hygiene)**:
  Like `WeylLeftIdeal` (`EP-0240`), Ore Euclidean `gcrd`/`lclm` MUST reject IEEE-754 floating-point base coefficients, requiring exact fields/integral domains (`StandardField(Fraction)`, primality-validated `ModularField(p)` from `EP-0250`, or polynomial rings over exact fields). Modules obey `EP-0254` hygiene (public-only cross-package imports, zero `EP-XXXX` references in `src/`).

---

## Specification

### 1. Mode-Parameterized `OreAlgebra` (`src/algebrax/differential/ore.py`)

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Generic, Literal, TypeVar

from algebrax.algebra import HasSkewDerivation, LawAssociative, Ring

R = TypeVar("R")
OreOp = dict[int, R]  # Maps operator power D^k -> coefficient in R
OreKind = Literal["differential", "shift", "difference", "q_difference", "custom"]


class OreAlgebra(Ring[OreOp[R]], LawAssociative, Generic[R]):
    r"""Ore Skew-Polynomial Ring $R[\partial; \sigma, \delta]$ with commutation $\partial r = \sigma(r)\partial + \delta(r)$.

    Carrier:
        `dict[int, R]` (Sparse mapping from operator order $k \in \mathbb{N}_0$ to coefficient $c_k \in R$).
    """

    def __init__(
        self,
        base_ring: Ring[R],
        sigma: Callable[[R], R],
        delta: Callable[[R], R],
        kind: OreKind = "custom",
    ) -> None: ...

    @classmethod
    def differential(cls, base_ring: Ring[R], deriv: Callable[[R], R]) -> "OreAlgebra[R]":
        """Construct differential Ore algebra R[D_x; id, d/dx]."""
        ...

    @classmethod
    def shift(cls, base_ring: Ring[R], shift_fn: Callable[[R], R]) -> "OreAlgebra[R]":
        """Construct shift/recurrence Ore algebra R[S_n; p(n)->p(n+1), 0]."""
        ...

    @classmethod
    def difference(cls, base_ring: Ring[R], shift_fn: Callable[[R], R]) -> "OreAlgebra[R]":
        """Construct forward-difference Ore algebra R[Delta; S, S - id]."""
        ...

    @classmethod
    def q_difference(cls, base_ring: Ring[R], dilate_fn: Callable[[R], R]) -> "OreAlgebra[R]":
        """Construct q-difference Ore algebra R[D_q; p(x)->p(qx), 0]."""
        ...

    def right_divmod(self, a: OreOp[R], b: OreOp[R]) -> tuple[OreOp[R], OreOp[R]]:
        """Right Euclidean division a = q * b + r (with content normalization over fraction fields)."""
        ...

    def gcrd(self, a: OreOp[R], b: OreOp[R]) -> OreOp[R]:
        """Greatest Common Right Divisor of Ore operators a and b."""
        ...

    def lclm(self, a: OreOp[R], b: OreOp[R]) -> OreOp[R]:
        """Least Common Left Multiple annihilating f + g whenever a(f)=0 and b(g)=0."""
        ...

    def symmetric_product(self, a: OreOp[R], b: OreOp[R]) -> OreOp[R]:
        """Minimal-order Ore operator annihilating the product f * g whenever a(f)=0 and b(g)=0."""
        ...
```

### 2. Frobenius Indicial Polynomials, Newton Polygons, Companion Matrices & $D$-Finite Guessing (`src/algebrax/differential/frobenius.py`)

```python
def to_euler_form(diff_op: OreOp[UniPoly[V]]) -> dict[int, UniPoly[V]]:
    r"""Rewrite differential operator in Euler variable $\theta = x\partial_x$ using $x^k \partial_x^k = \prod_{j=0}^{k-1}(\theta - j)$."""
    ...


def indicial_polynomial(diff_op: OreOp[UniPoly[V]], point: V | None = None) -> UniPoly[V]:
    r"""Extract Frobenius indicial polynomial $I(\rho) \in k[\rho]$ at a regular singular point (default $x = 0$)."""
    ...


def differential_newton_polygon(
    diff_op: OreOp[UniPoly[V]],
) -> tuple[tuple[tuple[int, int], ...], tuple[V, ...]]:
    r"""Compute lower convex hull of $(k, \operatorname{val}_0(c_k) - k)$ and Katz irregularity slopes.

    All slopes $\le 0$ iff regular singular (Fuchsian); positive slopes $\lambda_i > 0$ give irregular
    exponential growth exponents $\exp(c x^{-\lambda_i})$ (bridging `EP-0222` `NewtonPolytope`).
    """
    ...


def differential_companion_matrix(
    monic_op: OreOp[RationalFunc[V]],
) -> SparseMatrix[int, RationalFunc[V]]:
    r"""Convert order-$m$ monic Ore operator $\partial^m + \sum_{k=0}^{m-1} a_k \partial^k$ into its $m \times m$ companion matrix $C_L$ ($\partial Y = C_L Y$)."""
    ...


def guess_ore_operator(
    samples: Sequence[V],
    mode: Literal["differential", "shift"],
    field: Field[V],
    max_order: int = 4,
    max_poly_deg: int = 3,
) -> OreOp[UniPoly[V]] | None:
    r"""D-finite Pade/recurrence guessing: synthesize minimal Ore annihilator from Taylor coefficients or sequence terms."""
    ...
```

### 3. Verification Oracles (`src/algebrax/verification/_differential.py`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_ore_algebra_laws(ore, op_a, op_b, sample_coeffs)`:
  1. Verifies skew commutation $\partial \cdot r == \sigma(r)\partial + \delta(r)$ and non-commutative associativity.
  2. Verifies `right_divmod` reconstruction $a == q \cdot b + r$ with $\deg(r) < \deg(b)$.
  3. Verifies `lclm(a, b)` is right-divisible by both `a` and `b` and satisfies $\deg(\operatorname{lclm}) = \deg(a) + \deg(b) - \deg(\operatorname{gcrd})$.
  4. Verifies `indicial_polynomial` roots match Euler substitution $y(x) = x^\rho$ at $x^0$ order, `differential_newton_polygon` yields slope $0$ on Fuchsian operators and Katz slope $3/2$ on Airy at $\infty$, and `guess_ore_operator` annihilates held-out series/sequence terms.

---

## Backwards Compatibility

100% additive and backwards compatible. Preserves all existing `EP-0231` shift signal models and `algebrax.matrix` / `EP-0163` solvers while exposing `differential_companion_matrix` as a clean bridge.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add `docs/guide/differential/ore_and_dfinite.md` showcasing how one `OreAlgebra` handles ODEs ($\exp x + \cos x$), recurrences ($F_n + n$), Bessel singular exponents, Newton-polygon irregularity slopes, and $D$-finite guessing.
- **Recipe**: Add `recipes/dfinite_closure_and_frobenius.py` synthesizing annihilators for special-function sums/products, guessing Catalan's recurrence/ODE, and analyzing Bessel/Airy singularities.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py) (Experiments 2, 6, and 9).

---

## Rejected Ideas

1. **Separate Class Hierarchy (`DifferentialOreAlgebra`, `ShiftOreAlgebra`, `QShiftOreAlgebra`)**:
   - *Rejected*: Violates `PRINCIPLES.md` (**Mode vs. Type** & **Factory Method for Specialization**). One `OreAlgebra` parameterized by `(sigma, delta)` with preset classmethods eliminates 4x boilerplate.
2. **Rational-Function-Only Arithmetic Without Pseudo-Division Support**:
   - *Rejected*: For polynomial bases $k[x]$ (including multi-variable rings in creative telescoping), pseudo-division with content normalization avoids constructing heavy nested rational fraction fields on every reduction step.

---

## Open Questions

- [ ] Whether to add a `ModularField(p)` + CRT multi-modular reconstruction backend inside `OreAlgebra.lclm` and `guess_ore_operator` as a first-class escape hatch for degree $> 10$ rational operators.

---

## Change Log

* **2026-11-15:**
  * Initial Draft authored for Phase 11 from `EXP-0011`.
  * Added `differential_newton_polygon` (Katz slopes) and `guess_ore_operator` ($D$-finite Padé/recurrence guessing) validated in `EXP-0011` Experiment 9.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0250`–`EP-0254`): switched private `algebra._*` imports to public `algebrax.algebra`, aligned `CommQuotientRing` and primality-validated `ModularField(p)`, documented `EP-0251` exact `matrix.nullspace`/`sparse_rref` reuse, updated verification path to `src/algebrax/verification/_differential.py`, and noted `EP-0253`/`EP-0254` contracts.
