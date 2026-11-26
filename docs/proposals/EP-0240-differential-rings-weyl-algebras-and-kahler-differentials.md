---
title: "EP-0240: Differential Rings, Weyl Algebras, Characteristic Varieties & Kähler Differentials"
description: "Introduce skew-derivation mixins, unboxed non-commutative Weyl algebras A_n(k), left Grobner D-module reduction, holonomic characteristic varieties, and Kahler differentials."
icon: lucide/sigma
status: draft
---

# EP-0240: Differential Rings, Weyl Algebras, Characteristic Varieties & Kähler Differentials

| Field             | Value                                                                                                  |
|:------------------|:-------------------------------------------------------------------------------------------------------|
| **EP**            | 0240                                                                                                   |
| **Title**         | Differential Rings, Weyl Algebras, Characteristic Varieties & Kähler Differentials                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                            |
| **Sponsor**       | Core Maintainers                                                                                       |
| **Delegate**      | ⚖️ Noether (Quantization & Duality), ⚡ Shannon (Unboxed Carriers) & 🛡️ Golem (Exact Field Mandate)   |
| **Status**        | Draft                                                                                                  |
| **Type**          | Standards Track                                                                                        |
| **Created**       | 2026-11-15                                                                                             |
| **Updated**       | 2026-11-26                                                                                             |
| **Replaces**      | —                                                                                                      |
| **Superseded-By** | —                                                                                                      |

---

## Abstract

This proposal establishes the non-commutative differential and geometric operator foundation for AlgebraX (`algebrax.differential`), generalizing `HasDerivation[V]` (`EP-0220`) to general skew derivations and introducing:

1. **Atomic Mixins (`src/algebrax/algebra/_mixins.py`)**: `HasSkewDerivation[R]`, `HasIntegrate[V]`, `LawLeibniz`, and `LawRotaBaxter`, composing cleanly with `EP-0005` without diamond inheritance.
2. **Differential Polynomial Rings & Hamiltonian Duality (`DifferentialPolynomialRing`, `CanonicalPoissonAlgebra`, `legendre_transform`)**: Exact jet-polynomial variational calculus ($\frac{\delta}{\delta u} \circ D \equiv 0$), concrete canonical phase-space Poisson brackets (`EP-0204`/`EP-0220`), Hamiltonian derivations $X_H = \{\cdot, H\}$, conserved integrals $\{I, H\} = 0$, and regular quadratic Legendre transforms $\mathcal{L}(q, \dot{q}) \leftrightarrow H(q, p)$.
3. **Non-Commutative Weyl Algebras $A_n(k)$ (`WeylAlgebra[V]`)**: Exact partial differential operator algebras $k\langle x_1, \dots, x_n, \partial_1, \dots, \partial_n \rangle / \langle [\partial_i, x_j] - \delta_{ij} \rangle$ stored over unboxed `dict[tuple[Monomial, Monomial], V]` carriers, with left $D$-module action on `MultivariatePolynomialAlgebra` and an Ehrenfest principal-symbol correspondence bridge to `CanonicalPoissonAlgebra` (`EP-0204`).
4. **Left Weyl Gröbner Reduction & Characteristic Varieties (`WeylLeftIdeal`, `characteristic_variety`)**: Non-commutative left reduction under admissible term orderings (Bernstein $(1,1)$ weight), mapping principal symbols $\operatorname{gr}(I)$ to Phase 9 [`AffineVariety`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) objects to certify holonomicity ($\dim \operatorname{Char}(I) = n$) and holonomic rank.
5. **Kähler Differentials $\Omega^1_{k[V]/k}$ (`KahlerDifferentialModule`)**: Universal coordinate-free exterior derivatives $d: k[V] \to \Omega^1_{k[V]/k}$ on affine coordinate rings, bridging Phase 4 DEC (`EP-0160`) and Phase 9 Jacobian tangent loci (`EP-0221`).

---

## Motivation

Through Phases 1–10, AlgebraX provides commutative polynomial ideals (`EP-0220`), affine varieties (`EP-0221`), symplectic Poisson brackets (`EP-0204`), and discrete exterior calculus (`EP-0160`). Missing is **algebraic differential calculus**:

1. **Exact Operator Algebra Beyond Floating-Point Differences**: Finite-difference approximations accumulate truncation and IEEE-754 rounding drift and cannot certify operator identities like $(\partial_x + 2x)(\partial_x - 2x) = \partial_x^2 - 4x^2 - 2$.
2. **Quantization of Phase 9 Commutative Geometry**: Passing from commutative phase space $k[x, p]$ to canonical commutation $[\partial_i, x_j] = \delta_{ij}$ turns differential equations into left ideals in $A_n(k)$ whose characteristic varieties $\operatorname{Char}(I)$ reuse `AffineVariety` directly.
3. **Intrinsic Geometry on Singular/Smooth Coordinate Rings**: `HasTangentLocus` in `EP-0221` computes Jacobian matrices in coordinates; Kähler differentials $\Omega^1_{k[V]/k}$ dualize that Jacobian into the universal derivation module of the variety.

---

## Rationale

Validated in [**EXP-0011**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md) (Experiments 1, 5, and 7) and aligned with the Grand Council and **Phase 8.5 (`EP-0250`–`EP-0254`)**:

- **⚖️ Emmy Noether (Quantization & Ideal–Variety Continuity)**:
  Weyl algebras quantize the canonical Poisson bracket of `EP-0204`/`EP-0220`, while principal symbols reverse quantization by projecting left $D$-module ideals $I \subseteq A_n(k)$ back onto commutative `AffineVariety` characteristic loci $\operatorname{Char}(I) \subset k^{2n}$. Exact `Fraction` coefficients align with `EP-0251`'s widened `typing.N`.
- **⚡ Claude Shannon (Unboxed Carriers, $O(\log m)$ Scaling & Shared Exact Linear Algebra)**:
  Operators remain sparse `dict[tuple[Monomial, Monomial], V]` mappings reusing `Monomial = tuple[int, ...]` with zero AST wrapper classes. Combinatorial Leibniz coefficients $\binom{\beta}{\kappa}\binom{u}{\kappa}\kappa!$ MUST be embedded into the base `Field[V]` in $O(\log m)$ operations via `field.nsum(field.one, mult)` rather than linear $O(m)$ addition loops (avoiding $10!$-iteration stalls on order-10 derivatives). Regular Hessian inversion in `legendre_transform` and exact linear solves in `WeylLeftIdeal` / `AlgebraicDeRhamComplex` reuse Phase 8.5 [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s consolidated `matrix.sparse_rref` / `solve(..., field=...)` / `rank` / `nullspace` kernels instead of duplicating elimination loops.
- **🛡️ The Golem (Exact Field Mandate, Admissible Termination & Hygiene)**:
  Because $[\partial_i, x_i] = 1$ cancellation residuals of $10^{-16}$ fabricate unit ideals $\langle 1 \rangle$, `WeylLeftIdeal` MUST reject IEEE-754 floating-point fields (`float`, `complex`) at construction and enforce strictly well-founded admissible monomial orderings (e.g., Bernstein $(1,1)$ weight) to guarantee left-reduction termination. All new modules in `src/algebrax/differential/` obey `EP-0254` hygiene (public-only cross-package imports, zero `EP-XXXX` citations in `src/`).
- **🧩 Bertrand Russell (Clean Protocol Separation & Law Witnesses)**:
  Following `EP-0005` and Phase 8.5 [`EP-0250`](EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md), `WeylAlgebra[V]` implements associative `Ring[WeylPoly[V]]` and `Algebra[V, WeylPoly[V]]` **without** inheriting `CommRing` or `LawCommutative`. `HasSkewDerivation[R]`, `LawLeibniz`, and `LawRotaBaxter` follow flat Layer-1 composition with `Literal[True]` law-witness properties.
- **🔬 Karl Popper (Non-Vacuous Verification Oracles)**:
  All differential verification routines follow Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts (`_materialize_samples`, `NaN != NaN` equality guard).
- **💡 Richard Feynman (The Freshman Test)**:
  *"Instead of taking numerical limits $\Delta x \to 0$, you keep $x$ and $\partial_x$ as algebraic letters that obey one rule: $\partial_x x = x\partial_x + 1$. Every derivative rule, differential operator product, and tangent form computation reduces to sorting letters alphabetically with that single swap."*

---

## Specification

### 1. Atomic Differential Mixins (`src/algebrax/algebra/_mixins.py`)

```python
from typing import Literal, Protocol, TypeVar, runtime_checkable

V = TypeVar("V")
R = TypeVar("R")


@runtime_checkable
class HasSkewDerivation(Protocol[R]):
    r"""Twisted (sigma-)derivation $\delta: R \to R$ with endomorphism $\sigma: R \to R$.

    Satisfies the skew Leibniz identity $\delta(ab) = \sigma(a)\delta(b) + \delta(a)b$.
    Ordinary derivations correspond to $\sigma = \mathrm{id}_R$.
    """

    def sigma(self, a: R) -> R: ...

    def delta(self, a: R) -> R: ...


@runtime_checkable
class HasIntegrate(Protocol[V]):
    r"""Formal exact antidifferentiation $\int: V \to V$ dual to `HasDerivation`."""

    def integrate(self, a: V, var_index: int = 0) -> V: ...


@runtime_checkable
class LawLeibniz(Protocol):
    """Axiom marker asserting that `diff` / `delta` satisfies the (skew) Leibniz product rule."""

    @property
    def is_leibniz(self) -> Literal[True]: ...


@runtime_checkable
class LawRotaBaxter(Protocol[V]):
    r"""Axiom marker asserting Rota–Baxter identity $R(a)R(b) = R(R(a)b + aR(b) + \lambda ab)$."""

    @property
    def rota_baxter_weight(self) -> V: ...
```

### 2. Differential Polynomial Rings & Euler–Lagrange Variational Complex (`src/algebrax/differential/ring.py`)

```python
JetMonomial = tuple[int, ...]  # Canonical trailing-zero-trimmed exponents (e_0, ..., e_r) for prod (u^{(j)})^{e_j}


class DifferentialPolynomialRing(Ring[dict[JetMonomial, V]], LawLeibniz, Generic[V]):
    r"""Differential polynomial ring $k\{u\} = k[u, u', u'', \dots]$ over an exact field $k$.

    Carrier:
        `dict[tuple[int, ...], V]` mapping jet-variable exponent tuples to exact field scalars.
    """

    def __init__(self, field: Field[V]) -> None: ...

    def var(self, order: int = 0) -> dict[JetMonomial, V]:
        """Return jet indeterminate u^{(order)}."""
        ...

    def partial_jet(self, expr: dict[JetMonomial, V], order: int) -> dict[JetMonomial, V]:
        """Formal partial derivative d/d(u^{(order)})."""
        ...

    def total_diff(self, expr: dict[JetMonomial, V]) -> dict[JetMonomial, V]:
        r"""Total differential derivation $D = \sum_{j \ge 0} u^{(j+1)} \frac{\partial}{\partial u^{(j)}}$."""
        ...

    def euler_lagrange(self, lagrangian: dict[JetMonomial, V]) -> dict[JetMonomial, V]:
        r"""Variational Euler–Lagrange derivative $\frac{\delta \mathcal{L}}{\delta u} = \sum_{k \ge 0} (-D)^k \frac{\partial \mathcal{L}}{\partial u^{(k)}}$."""
        ...


class CanonicalPoissonAlgebra(Generic[V]):
    r"""Concrete canonical phase-space Poisson algebra $k[q_1,\dots,q_m, p_1,\dots,p_m]$ (`EP-0204` / `EP-0220`).

    Realizes `PoissonAlgebra[V, SparseMPoly[V]]` with symplectic bracket
    $\{f, g\} = \sum_{i=1}^m (\partial_{q_i} f \, \partial_{p_i} g - \partial_{p_i} f \, \partial_{q_i} g)$.
    """

    def __init__(self, field: Field[V], n_dof: int) -> None: ...

    def hamiltonian_derivation(self, hamiltonian: SparseMPoly[V]) -> Callable[[SparseMPoly[V]], SparseMPoly[V]]:
        r"""Return Hamiltonian vector field $X_H(f) = \{f, H\}$ satisfying `HasDerivation` and Lie homomorphism $[X_F, X_G] = -X_{\{F, G\}}$."""
        ...

    def is_first_integral(self, invariant: SparseMPoly[V], hamiltonian: SparseMPoly[V]) -> bool:
        """Certify exact conservation law {invariant, hamiltonian} == 0."""
        ...


def legendre_transform(
    alg: CanonicalPoissonAlgebra[V],
    lagrangian_or_hamiltonian: SparseMPoly[V],
    *,
    forward: bool = True,
) -> SparseMPoly[V]:
    r"""Exact algebraic Legendre transform $\mathcal{L}(q, \dot{q}) \leftrightarrow H(q, p) = \sum_i p_i \dot{q}_i - \mathcal{L}$ for regular quadratic velocity/momentum Hessians $M \in \mathrm{GL}_m(k)$.

    Raises `ValueError` when $\det M = 0$ (singular/constrained systems deferred under the Dennis Point).
    """
    ...
```

### 3. Unboxed Weyl Algebra $A_n(k)$ (`src/algebrax/differential/weyl.py`)

```python
from __future__ import annotations

from typing import Generic, Literal, TypeVar

from algebrax.algebra import (
    Algebra,
    Field,
    LawAssociative,
    Monomial,
    MultivariatePolynomialAlgebra,
    SparseMPoly,
)

V = TypeVar("V")
WeylMonomial = tuple[Monomial, Monomial]  # (x_exponents, d_exponents)
WeylPoly = dict[WeylMonomial, V]
WeylOrder = Literal["bernstein", "order_lex", "elim_d"]


class WeylAlgebra(Algebra[V, WeylPoly[V]], LawAssociative, Generic[V]):
    r"""Normal-ordered Weyl Algebra $A_n(k) = k\langle x_1,\dots,x_n, \partial_1,\dots,\partial_n\rangle / \langle [\partial_i, x_j] - \delta_{ij} \rangle$.

    Carrier:
        `dict[tuple[Monomial, Monomial], V]` mapping $(x^\alpha, \partial^\beta) \mapsto c_{\alpha,\beta} \in k$.
    """

    def __init__(
        self,
        field: Field[V],
        n_vars: int,
        order: WeylOrder = "bernstein",
    ) -> None: ...

    def x(self, i: int) -> WeylPoly[V]:
        """Return coordinate multiplication generator x_i."""
        ...

    def d(self, i: int) -> WeylPoly[V]:
        """Return partial differential generator d_i."""
        ...

    def mul(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        r"""Normal-ordered Leibniz Weyl product using $O(\log m)$ `field.nsum` scalar embedding."""
        ...

    def commutator(self, p: WeylPoly[V], q: WeylPoly[V]) -> WeylPoly[V]:
        """Return [p, q] = p*q - q*p."""
        ...

    def apply_to_poly(self, op: WeylPoly[V], f: SparseMPoly[V]) -> SparseMPoly[V]:
        """Left D-module action L(f) on commutative polynomial f in k[x_1, ..., x_n]."""
        ...

    def principal_symbol(self, op: WeylPoly[V]) -> dict[WeylMonomial, V]:
        """Extract leading order-filtration symbol terms in k[x_1,...,x_n, xi_1,...,xi_n]."""
        ...
```

### 4. Weyl Left Ideals, Characteristic Varieties & Kähler Differentials (`src/algebrax/differential/dmodule.py`)

```python
class WeylLeftIdeal(Generic[V]):
    """Left ideal I subseteq A_n(k) backed by a non-commutative left Grobner basis over an exact Field."""

    def __init__(
        self,
        weyl: WeylAlgebra[V],
        generators: Sequence[WeylPoly[V]],
        max_steps: int = 10_000,
    ) -> None:
        # Reject IEEE-754 float/complex fields; run non-commutative left Buchberger S-pair completion.
        ...

    def reduce(self, op: WeylPoly[V]) -> WeylPoly[V]:
        """Normal-form left reduction rem(op, G) modulo the left Grobner basis."""
        ...

    def contains(self, op: WeylPoly[V]) -> bool:
        """Return True iff op belongs to the left ideal (reduce(op) == zero)."""
        ...

    def characteristic_variety(self) -> "AffineVariety[V]":
        r"""Compute $\operatorname{Char}(I) = V(\operatorname{gr}(I)) \subset k^{2n}$ via principal symbols."""
        ...

    def is_holonomic(self) -> bool:
        """Return True iff dim(Char(I)) == n_vars (Bernstein inequality equality)."""
        ...


class AlgebraicDeRhamComplex(Generic[V]):
    r"""Full graded exterior algebra & Kahler-de Rham complex $\Omega^\bullet_{k[V]/k} = k[V] \otimes_k \bigwedge^\bullet(dx_1, \dots, dx_n)$.

    Carrier:
        `dict[tuple[Monomial, Blade], V]` where `Blade = tuple[int, ...]` is a strictly increasing Grassmann blade
        (reusing `CliffordAlgebra` blade sorting over exact `Field[V]`), modulo $\langle I, dI \rangle$ when `ideal` is supplied.
    """

    def __init__(self, ring: MultivariatePolynomialAlgebra[V], ideal: "GroebnerIdeal[V] | None" = None) -> None: ...

    def wedge(self, alpha: dict[tuple[Monomial, Blade], V], beta: dict[tuple[Monomial, Blade], V]) -> dict[tuple[Monomial, Blade], V]:
        r"""Graded-commutative wedge product $\alpha \wedge \beta = (-1)^{pq} \beta \wedge \alpha$."""
        ...

    def exterior_derivative(self, alpha: dict[tuple[Monomial, Blade], V]) -> dict[tuple[Monomial, Blade], V]:
        r"""Graded exterior derivative $d_k: \Omega^k \to \Omega^{k+1}$ satisfying $d^2 \equiv 0$ and graded Leibniz."""
        ...

    def interior_product(self, vec_field: Sequence[SparseMPoly[V]], alpha: dict[tuple[Monomial, Blade], V]) -> dict[tuple[Monomial, Blade], V]:
        r"""Interior contraction $\iota_X: \Omega^k \to \Omega^{k-1}$ obeying $\iota_X^2 \equiv 0$."""
        ...

    def lie_derivative(self, vec_field: Sequence[SparseMPoly[V]], alpha: dict[tuple[Monomial, Blade], V]) -> dict[tuple[Monomial, Blade], V]:
        r"""Cartan's magic formula $\mathcal{L}_X = d \circ \iota_X + \iota_X \circ d$."""
        ...

    def poincare_homotopy(self, alpha: dict[tuple[Monomial, Blade], V]) -> dict[tuple[Monomial, Blade], V]:
        r"""Exact algebraic Poincare chain homotopy $h_k: \Omega^k \to \Omega^{k-1}$ ($dh + hd = \mathrm{id}$ for $\operatorname{char}(k)=0$)."""
        ...


class KahlerDifferentialModule(AlgebraicDeRhamComplex[V], Generic[V]):
    r"""Backward-compatible 1-form facade over $\Omega^1_{k[V]/k} = \bigoplus_i k[V]\,dx_i / \langle df \mid f \in I \rangle$."""

    def exterior_diff(self, f: SparseMPoly[V]) -> tuple[SparseMPoly[V], ...]:
        """Compute df = (df/dx_1, ..., df/dx_n) reduced modulo the coordinate ideal I."""
        ...

    def contract(self, one_form: Sequence[SparseMPoly[V]], derivation: Sequence[SparseMPoly[V]]) -> SparseMPoly[V]:
        """Evaluate canonical pairing <omega, X> reduced in the coordinate ring k[V]."""
        ...
```

### 5. Verification Oracles (`src/algebrax/verification/_differential.py`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_weyl_algebra_laws(weyl, ops, poly_f)`:
  1. Verifies CCR axioms $[\partial_i, x_j] == \delta_{ij} \mathbf{1}$, $[x_i, x_j] == 0$, $[\partial_i, \partial_j] == 0$.
  2. Verifies non-commutative associativity $(L_1 L_2) L_3 == L_1 (L_2 L_3)$ and $D$-module homomorphism $(L_1 L_2)(f) == L_1(L_2(f))$.
  3. Verifies multi-generator left Weyl Gröbner S-polynomial reduction ($\overline{S_L(g_i, g_j)}^G == 0$) and Bernstein inequality $\dim \operatorname{Char}(I) \ge n$ on holonomic test ideals.
  4. Verifies Kähler contraction $\langle df, X \rangle \equiv 0 \pmod{I}$ for tangent derivations $X \in \operatorname{Der}_k(k[V], k[V])$, de Rham nilpotency $d^2 \equiv 0$, graded Leibniz $d(\alpha \wedge \beta) == d\alpha \wedge \beta + (-1)^p\alpha \wedge d\beta$, Poincaré homotopy $dh + hd == \mathrm{id}$, and symplectic Cartan–Liouville ($\iota_{X_H}\omega == dH$, $\mathcal{L}_{X_H}\omega == 0$).
- `verify_variational_and_rota_baxter_laws(diff_ring, sample_jets, rb_op, weight)`:
  1. Verifies exact Null-Lagrangian cochain complex $\frac{\delta}{\delta u}(D(F)) \equiv 0$ identically in $k\{u\}$.
  2. Verifies Rota–Baxter law $R(a)R(b) == R(R(a)b + aR(b) + \lambda ab)$ for $\lambda = 0$ (integration by parts) and $\lambda = \pm 1$ (summation by parts).
- `verify_hamiltonian_and_ehrenfest_laws(poisson_alg, weyl_alg, lagrangian, ops)`:
  1. Verifies Poisson laws, Hamiltonian Lie homomorphism $[X_F, X_G] == -X_{\{F, G\}}$, and conservation $\{I, H\} == 0$.
  2. Verifies algebraic Legendre involution $\mathcal{L} \leftrightarrow H$ for regular quadratic Hessians (and `ValueError` rejection when $\det M == 0$) plus Euler–Lagrange vs. Hamilton equivalence.
  3. Verifies Weyl–Poisson Ehrenfest principal-symbol correspondence $\sigma_{\text{top}}([\widehat{A}, \widehat{B}]) == -\{\sigma_{\text{top}}(\widehat{A}), \sigma_{\text{top}}(\widehat{B})\}_{q, p}$.

---

## Backwards Compatibility

100% additive and backwards compatible. Existing `HasDerivation[V]` in `algebra._mixins` and `MultivariatePolynomialAlgebra` (`EP-0220`) remain untouched; `algebrax.differential` cleanly separates symbolic/algebraic derivations from `algebrax.analysis` discrete spectral Laplacians.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add `docs/guide/differential/weyl_and_dmodules.md` explaining $[\partial, x] = 1$, normal ordering, left Gröbner elimination, the Euler–Lagrange variational complex, Hamiltonian/Legendre duality, and the graded de Rham / Kähler exterior derivative ($d^2 = 0$, Poincaré potential recovery, Cartan–Liouville).
- **Recipe**: Add `recipes/quantum_harmonic_weyl_and_kahler.py` demonstrating quantum oscillator ladder operators in $A_n(\mathbb{Q})$, 2D Gaussian holonomicity, null-Lagrangian exactness, Legendre $\leftrightarrow$ Ehrenfest correspondence, Cartan's $\iota_{X_H}\omega = dH$, and constructive vector-potential recovery $B = d(h(B))$.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py) (Experiments 1, 5, 7, 9, 10, and 11).

---

## Rejected Ideas

1. **Inheriting `CommRing` or `LawCommutative` on `WeylAlgebra`**:
   - *Rejected*: Violates Russell's axiom consistency because $[\partial_i, x_i] = 1 \ne 0$.
2. **Supporting `float`/`complex` in `WeylLeftIdeal` Gröbner Completion**:
   - *Rejected*: Rounding residuals of $10^{-16}$ from Leibniz commutators produce false unit ideals $\langle 1 \rangle$.
3. **Unnormal-ordered Word/AST Representation for $x, \partial$**:
   - *Rejected*: Storing unreduced words `("d", "x", "d")` forces repeated commutation rewrites on every equality check; canonical normal ordering $\sum c_{\alpha,\beta} x^\alpha \partial^\beta$ guarantees unique sparse dictionary keys (`EP-0004`).

---

## Open Questions

- [ ] Whether to support $q$-Weyl algebras ($[\partial_i, x_j]_q = \delta_{ij}$) via a mode parameter on `WeylAlgebra` or delegate $q$-commutation exclusively to `OreAlgebra` (`EP-0241`).

---

## Change Log

* **2026-11-15:**
  * Initial Draft authored for Phase 11 from `EXP-0011`.
  * Added `LawRotaBaxter` mixin and `DifferentialPolynomialRing` ($k\{u\}$ total derivative & Euler–Lagrange variational complex) validated in `EXP-0011` Experiment 9.
  * Added `CanonicalPoissonAlgebra`, `legendre_transform`, and Weyl–Poisson Ehrenfest verification validated in `EXP-0011` Experiment 10.
  * Expanded Kähler differentials into graded `AlgebraicDeRhamComplex` ($d_k$, $\wedge$, $\iota_X$, $\mathcal{L}_X$, Poincaré homotopy $h_k$) validated in `EXP-0011` Experiment 11.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0250`–`EP-0254`): added `is_leibniz: Literal[True]` witness on `LawLeibniz`, replaced private `algebra._*` imports with public `algebrax.algebra`, documented `EP-0251` exact linear-algebra kernel reuse, updated verification path to `src/algebrax/verification/_differential.py`, and noted `EP-0253`/`EP-0254` contracts.
