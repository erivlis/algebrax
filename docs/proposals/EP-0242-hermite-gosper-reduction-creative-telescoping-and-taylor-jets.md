---
title: "EP-0242: Exact Symbolic Integration, Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jets"
description: "Introduce exact algebraic rational integration (Yun/Hermite/Rothstein-Trager), Gosper indefinite summation, creative telescoping, and multivariate Taylor Jet algebras unifying DualNumberAlgebra."
icon: lucide/integral
status: draft
---

# EP-0242: Exact Symbolic Integration, Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jets

| Field             | Value                                                                                                          |
|:------------------|:---------------------------------------------------------------------------------------------------------------|
| **EP**            | 0242                                                                                                           |
| **Title**         | Exact Symbolic Integration, Hermite & Gosper Reduction, Creative Telescoping & Multivariate Taylor Jets        |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                                    |
| **Sponsor**       | Core Maintainers                                                                                               |
| **Delegate**      | ⚡ Shannon (Zero-AST Speedup), 🔬 Popper (FTC & Gosper Oracles) & 🛡️ Golem (Safe Jet Factory)                  |
| **Status**        | Draft                                                                                                          |
| **Type**          | Standards Track                                                                                                |
| **Created**       | 2026-11-15                                                                                                     |
| **Updated**       | 2026-11-26                                                                                                     |
| **Replaces**      | —                                                                                                              |
| **Superseded-By** | —                                                                                                              |

---

## Abstract

This proposal completes AlgebraX’s differential and difference calculus stack (`algebrax.differential`) with four exact, AST-free algebraic algorithms:

1. **Exact Rational Integration (`square_free_decomposition`, `hermite_reduce`, `rothstein_trager_resultant`)**: Pure-Python integration over exact fields (`StandardField(Fraction)`) reducing any rational function $A(x)/D(x)$ to $P(x) + G_{\text{num}}/G_{\text{den}} + \int H(x)/S(x)\,dx$ with strictly square-free $S(x)$—avoiding complex root factorization and achieving **37.7x speedups** over `sympy.integrate` in `EXP-0011`.
2. **Discrete Hypergeometric Summation (`gosper_sum`)**: Exact Gosper dispersion resultant $R(h)$ and certificate solver $r(n)$ for indefinite hypergeometric sums, including rigorous non-summability proofs (`None`).
3. **Creative Telescoping (`creative_telescope`)**: Zeilberger/Chyzak Ore elimination synthesizing telescoping operator certificates $(L, B)$ for definite hypergeometric and holonomic integrals/sums.
4. **Univariate & Multivariate `TaylorJetAlgebra[V]`**: A safe ergonomic factory wrapping `CommQuotientRing` (`EP-0250`) over `PolynomialTruncationIdeal(order + 1, ...)` and multivariate $k[x_1, \dots, x_n]/\mathfrak{m}^{r+1}$ quotients, generalizing [`DualNumberAlgebra`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/algebra/_dual.py) ($n=1, r=1$) to arbitrary-order exact partial/Lie derivatives, Newton series reciprocals (`inv`), Lagrange reversion, and Newton–Picard nonlinear ODE solvers (`solve_ode_jet`).

---

## Motivation

1. **Calculus Without AST Bloat or Complex Factorization**:
   Expression-tree CAS engines spend substantial overhead reconstructing symbolic parse trees (`111.35 ms` in `EXP-0011` Experiment 3 vs. `2.95 ms` for pure unboxed Hermite reduction). Algebraic Hermite reduction and Gosper's algorithm run strictly via univariate `gcd`, extended Bézout inverses, and small exact linear solves.
2. **Fixing `PolynomialTruncationIdeal` Ergonomics for Jets**:
   `EXP-0011` Experiment 4 revealed that [`PolynomialTruncationIdeal`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/algebra/_ideals.py) takes `(max_degree, zero_coeff)` positionally and truncates degrees $\ge \text{max\_degree}$ (requiring `order + 1` for degree-`order` Taylor jets). A dedicated `TaylorJetAlgebra(field, order=..., n_vars=...)` factory eliminates this footgun and extends [`DualNumberAlgebra`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/algebra/_dual.py) from $(n=1, r=1)$ `float` pairs to arbitrary-order multivariate exact arithmetic.

---

## Rationale

Validated in [**EXP-0011**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md) (Experiments 3, 4, 6, and 7) and aligned with the Grand Council and **Phase 8.5 (`EP-0250`–`EP-0254`)**:

- **⚡ Claude Shannon (Sparse Polynomial Algorithms > Symbolic Trees & Shared Exact Kernels)**:
  Unboxed `dict[int, Fraction]` Yun/Hermite reduction achieved a **37.7x speedup** over `sympy.integrate` (`2.95 ms` vs. `111.35 ms`). Keeping `DualNumberAlgebra` (`tuple[float, float]`) untouched for ultra-lightweight 1st-order AD while introducing `TaylorJetAlgebra` for arbitrary order/variables preserves performance across both regimes. Linear solves in `gosper_sum` and `creative_telescope` reuse Phase 8.5 [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s exact `matrix.solve(..., field=...)` / `nullspace` kernels and widened `typing.N` (`Fraction`).
- **🔬 Karl Popper (Exact FTC, Gosper & Creative Telescoping Oracles)**:
  Prototyping in `EXP-0011` caught sign/index bugs in Yun (`z / a_i`), Hermite (`-(m-1)`), and Gosper (`c(n)` shift `-j`) immediately through derivative/shift residual checks and `SymPy` differential comparison. Both Hermite and Creative Telescoping return explicit **proof-carrying rational/operator certificates** verified directly in $O(\deg)$ arithmetic (`EP-0186` alignment) and obey Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts.
- **🛡️ The Golem (Safe Factory, Hygiene & Deliberate Deferrals)**:
  Wrapping `PolynomialTruncationIdeal(order + 1, field.zero)` inside `TaylorJetAlgebra` prevents off-by-one truncation bugs. Full transcendental Risch integration towers and Ritt–Wu nonlinear characteristic sets are deliberately deferred to `SymPy` under the Dennis Point. Modules obey `EP-0254` hygiene (public-only cross-package imports, zero `EP-XXXX` citations in `src/`).
- **🧩 Bertrand Russell (`CommQuotientRing` & `inv` vs. Kleene `star`)**:
  While `DualNumberAlgebra` exposes `star(a) = 1/(1-a)` as a `StarSemiring`, general `TaylorJetAlgebra` wraps Phase 8.5 [`EP-0250`](EP-0250-protocol-integrity-law-witnesses-and-algebraic-soundness.md)'s `CommQuotientRing` (distinguishing commutative quotients from general non-commutative `QuotientRing`) whose unit group consists of jets with invertible constant term $a_0 \ne 0$, computed via quadratic Newton reciprocal `inv(a)` ($y_{k+1} = y_k(2 - a y_k)$) rather than conflating division with Kleene star.

---

## Specification

### 1. Exact Rational Integration (`src/algebrax/differential/integrate.py`)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from algebrax.algebra import Field

V = TypeVar("V")
UniPoly = dict[int, V]


@dataclass(frozen=True)
class HermiteDecomposition(Generic[V]):
    r"""Exact Hermite integral decomposition $\int \frac{A}{D} dx = P + \frac{G_{\text{num}}}{G_{\text{den}}} + \int \frac{H}{S} dx$."""

    poly_integral: UniPoly[V]
    rational_num: UniPoly[V]
    rational_den: UniPoly[V]
    log_num: UniPoly[V]
    log_den: UniPoly[V]  # Guaranteed strictly square-free: deg(gcd(log_den, log_den')) == 0


def square_free_decomposition(poly: UniPoly[V], field: Field[V]) -> tuple[UniPoly[V], ...]:
    """Compute Yun's square-free decomposition P = prod_{k=1}^m A_k^k over characteristic-0 exact Field."""
    ...


def hermite_reduce(num: UniPoly[V], den: UniPoly[V], field: Field[V]) -> HermiteDecomposition[V]:
    """Compute exact Hermite rational-part extraction without algebraic factorization."""
    ...


def rothstein_trager_resultant(log_num: UniPoly[V], log_den: UniPoly[V], field: Field[V]) -> dict[tuple[int, int], V]:
    r"""Compute bivariate Rothstein–Trager resultant $R(t) = \operatorname{Res}_x(S(x), H(x) - t S'(x))$ characterizing logarithmic residues."""
    ...
```

### 2. Gosper Summation & Creative Telescoping (`src/algebrax/differential/summation.py`)

```python
@dataclass(frozen=True)
class TelescopingCertificate(Generic[V]):
    """Proof-carrying creative telescoping output L(n, S_n) F(n, k) = Delta_k(B(n, k, S_k) F(n, k))."""

    telescoper: dict[int, UniPoly[V]]
    certificate: dict[tuple[int, ...], V]


def gosper_sum(
    ratio_num: UniPoly[V],
    ratio_den: UniPoly[V],
    field: Field[V],
) -> tuple[UniPoly[V], UniPoly[V]] | None:
    r"""Exact Gosper indefinite hypergeometric summation for $t_{n+1}/t_n = f(n)/g(n)$.

    Returns reduced rational certificate $(R_{\text{num}}, R_{\text{den}})$ with $S(n) = r(n)t_n$,
    or `None` when proven non-summable in hypergeometric form.
    """
    ...


def creative_telescope(
    annihilator_gens: Sequence[dict[tuple[Monomial, Monomial], V]],
    field: Field[V],
    max_order: int = 6,
) -> TelescopingCertificate[V]:
    """Synthesize a creative telescoping operator pair (L, B) via Ore/Weyl elimination (`EP-0240`/`EP-0241`)."""
    ...
```

### 3. Univariate & Multivariate Taylor Jet Algebras (`src/algebrax/differential/jets.py`)

```python
class TaylorJetAlgebra(CommRing[dict[Monomial, V]], HasDerivation[dict[Monomial, V]], HasIntegrate[dict[Monomial, V]], Generic[V]):
    r"""Exact truncated Taylor Jet algebra $k[x_1, \dots, x_n] / \mathfrak{m}^{r+1}$ (total degree $\le r$).

    Generalizes `DualNumberAlgebra` (n=1, r=1) over any exact `Field[V]`.
    When $n = 1$, wraps `CommQuotientRing(PolynomialAlgebra(field), PolynomialTruncationIdeal(order + 1, field.zero))`.
    """

    def __init__(self, field: Field[V], order: int, n_vars: int = 1) -> None: ...

    def inv(self, jet: dict[Monomial, V]) -> dict[Monomial, V]:
        """Compute exact multiplicative reciprocal via quadratic Newton iteration when constant term != 0."""
        ...

    def compose(self, outer: UniPoly[V], inner: dict[Monomial, V]) -> dict[Monomial, V]:
        """Compose univariate Taylor series outer(inner) truncated modulo m^{r+1}."""
        ...

    def partial_derivative(self, jet: dict[Monomial, V], multi_index: Monomial) -> V:
        r"""Extract exact derivative $\left.\frac{\partial^{|\alpha|} f}{\partial x^\alpha}\right|_0 = \alpha!\, c_\alpha$."""
        ...


def solve_ode_jet(
    rhs_fn: Callable[[TaylorJetAlgebra[V], dict[int, V]], dict[int, V]],
    initial_value: V,
    field: Field[V],
    order: int,
) -> dict[int, V]:
    """Solve initial value problem y'(x) = F(x, y(x)), y(0) = y_0 exactly mod x^{order+1} via Picard/Newton iteration."""
    ...


def solve_hamiltonian_jet(
    poisson_alg: "CanonicalPoissonAlgebra[V]",
    hamiltonian: SparseMPoly[V],
    q0: Sequence[V],
    p0: Sequence[V],
    order: int,
) -> tuple[tuple[UniPoly[V], ...], tuple[UniPoly[V], ...]]:
    r"""Solve Hamilton's equations $\dot{q}_i = \partial_{p_i} H$, $\dot{p}_i = -\partial_{q_i} H$ exactly mod $t^{\text{order}+1}$."""
    ...
```

### 4. Verification Oracles (`src/algebrax/verification/_differential.py`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_hermite_decomposition(num, den, decomp, field)`: Verifies exact rational reconstruction $(P + G_{\text{num}}/G_{\text{den}})' + H/S \equiv A/D$ and $\deg\gcd(S, S') == 0$.
- `verify_gosper_certificate(f, g, cert, field)`: Verifies $r(n+1)\frac{f(n)}{g(n)} - r(n) \equiv 1$ in $\mathbb{Q}(n)$ (and compares with `sympy.concrete.gosper.gosper_sum` in verification tests).
- `verify_creative_telescoping(cert, operator_action)`: Verifies $(L - \Delta_k B)(F) \equiv 0$ on sample holonomic sequences/integrands (`EP-0186` certificate model).
- `verify_jet_and_rota_baxter_laws(jet_alg)`: Verifies `jet_integrate` obeys `LawRotaBaxter` with weight $\lambda = 0$ (integration by parts), pairs `TaylorJetAlgebra` expansions with `guess_ore_operator` (`EP-0241`) for closed-loop $D$-finite operator recovery, and certifies `solve_hamiltonian_jet` preserves exact energy $H(q(t), p(t)) \equiv H(q_0, p_0) \pmod{t^{r+1}}$ and symplectic variational Jacobian $D\Phi_t^T J D\Phi_t \equiv J \pmod{t^{r+1}}$.

---

## Backwards Compatibility

100% additive and backwards compatible. [`DualNumberAlgebra`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/algebra/_dual.py) and [`PolynomialTruncationIdeal`](https://github.com/erivlis/algebrax/blob/main/src/algebrax/algebra/_ideals.py) keep their existing public signatures unchanged.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add `docs/guide/differential/integration_and_jets.md` contrasting numerical quadratures/RK4 against exact Hermite reduction, Gosper certificates, and Newton–Picard Jet ODE solving.
- **Recipe**: Add `recipes/exact_calculus_hermite_gosper_jets.py` demonstrating 37x rational Hermite reduction, factorial/rational Gosper telescoping, and exact $\tan(x)$ / 2D Hessian extraction via Taylor Jets.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py) (Experiments 3, 4, 6, 7, 9, and 10).

---

## Rejected Ideas

1. **Full Transcendental Risch Integration Towers**:
   - *Rejected*: Requires recursive differential field extensions, structure-theorem case splits, and AST-heavy symbolic manipulation misaligned with Shannon's unboxed sparse carriers; SymPy remains the fallback oracle when full elementary closed forms are needed.
2. **Replacing `DualNumberAlgebra` Directly with Dictionary Carriers**:
   - *Rejected*: Breaks backwards compatibility and adds unnecessary dict-allocation overhead to fast 1st-order `tuple[float, float]` dual-number differentiation.

---

## Open Questions

- [ ] Whether `rothstein_trager_resultant` should automatically split irreducible quadratic/cubic factors over `EP-0221` companion-matrix algebraic extensions or leave the resultant unfactored by default.

---

## Change Log

* **2026-11-15:**
  * Initial Draft authored for Phase 11 from `EXP-0011`.
  * Added `LawRotaBaxter` (weight 0) and `guess_ore_operator` (`EP-0241`) integration verification notes from `EXP-0011` Experiment 9.
  * Added `solve_hamiltonian_jet` with exact truncated energy & symplectic Jacobian conservation checks from `EXP-0011` Experiment 10.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0250`–`EP-0254`): updated `TaylorJetAlgebra` to wrap `CommQuotientRing` (`EP-0250`), switched private `algebra._field` import to public `algebrax.algebra`, documented `EP-0251` exact linear-algebra kernel reuse, updated verification path to `src/algebrax/verification/_differential.py`, and noted `EP-0253`/`EP-0254` contracts.
