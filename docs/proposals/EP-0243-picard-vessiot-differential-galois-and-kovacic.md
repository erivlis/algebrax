---
title: "EP-0243: Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization"
description: "Introduce Wronskian Abel–Liouville operators, symmetric/exterior powers Sym^k(L), order-2 Kovacic Liouvillian factorization and SL_2 obstruction certificates, and Picard–Vessiot Hopf torsors."
icon: lucide/git-branch
status: draft
---

# EP-0243: Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization

| Field             | Value                                                                                                  |
|:------------------|:-------------------------------------------------------------------------------------------------------|
| **EP**            | 0243                                                                                                   |
| **Title**         | Picard–Vessiot Differential Galois Theory, Symmetric Powers & Kovacic Factorization                    |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                            |
| **Sponsor**       | Core Maintainers                                                                                       |
| **Delegate**      | ⚖️ Noether (Picard–Vessiot Torsors), 🔬 Popper (SL₂ Obstruction Certificates) & 🛡️ Golem (Dennis Point) |
| **Status**        | Draft                                                                                                  |
| **Type**          | Standards Track                                                                                        |
| **Created**       | 2026-11-15                                                                                             |
| **Updated**       | 2026-11-26                                                                                             |
| **Replaces**      | —                                                                                                      |
| **Superseded-By** | —                                                                                                      |

---

## Abstract

This proposal introduces bounded-order **Differential Galois Theory (Picard–Vessiot theory)** in `algebrax.differential.galois`, serving as the differential-operator counterpart to classical polynomial Galois theory:

1. **Wronskian & Abel–Liouville Determinant Operators (`wronskian_operator`, `to_liouville_normal_form`)**: Converts order-$m$ differential Ore operators into $\operatorname{SL}_m$ normal form via the Abel–Liouville trace identity $W' = -\operatorname{Tr}(C_L)W$ (`EP-0241` `differential_companion_matrix` bridge).
2. **Symmetric & Exterior Powers (`symmetric_power`, `exterior_power`)**: Exact $\mathbb{Q}(x)$ construction of minimal differential operators annihilating $k$-fold symmetric and alternating products of solutions ($\operatorname{Sym}^k(L), \Lambda^k(L)$), detecting invariant subspaces of the differential Galois group.
3. **Order-2 Kovacic Liouvillian Classifier & Riccati Factorization (`kovacic_classify`, `kovacic_factorize`)**: Reuses Yun's `square_free_decomposition` (`EP-0242`) to check Kovacic admissibility (Cases 1–3), synthesize exact right-factors $L = (\partial - \omega_2)(\partial - \omega_1)$ over $k(x)$, or emit falsifiable **$\operatorname{SL}_2$ non-Liouvillian obstruction certificates** (proving no elementary/Liouvillian closed form exists, e.g., Airy's $y'' - xy = 0$).
4. **Picard–Vessiot Torsor Interface (`PicardVessiotTorsor`)**: Bridges the differential Galois group $\operatorname{Gal}_\partial(E/k(x)) \subseteq \operatorname{GL}_m(k)$ to [`CoordinateHopfAlgebra`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) and [`AffineVariety`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) (built on `HopfAlgebra` from [`EP-0206`](EP-0206-coalgebras-bialgebras-and-hopf-algebras.md)).

---

## Motivation

1. **Completing the Operator Factorization Story of `OreAlgebra` (`EP-0241`)**:
   `EP-0241` builds higher-order operators via `lclm` and `symmetric_product`, while `EP-0242` integrates rational functions and reduces hypergeometric sums via Gosper. Differential Galois Theory provides the **inverse decomposition and impossibility engine**: factoring reducible linear ODEs $L = (\partial - \omega_2)(\partial - \omega_1)$ over $k(x)$ and proving rigorously when an ODE admits *no* Liouvillian solution.
2. **Solving Apparent-Singularity Riccati ODEs Where General CAS Fall Back**:
   In `EXP-0011` Experiment 8, on $y'' - (x^2 + 3)y = 0$ (whose Riccati log-derivative $\omega_1(x) = x + \frac{1}{x}$ has an apparent pole at $x = 0$), `sympy.dsolve` fell back to an $O(x^6)$ power series and `sympy.solvers.ode.riccati.solve_riccati` returned `[]`, whereas exact Kovacic Case 1 Newton–Laurent extraction + linear solving over $\mathbb{Q}$ recovered $\omega_1 = \frac{x^2 + 1}{x}$ and verified $(\partial + \omega_1)(\partial - \omega_1) == \partial^2 - (x^2 + 3)$ identically.
3. **Cross-Continent Structural Unification**:
   Order-2 Kovacic subgroup classification ($\operatorname{Borel} \subset \operatorname{SL}_2$, $D_\infty$, finite primitive groups $A_4, S_4, A_5$, and full $\operatorname{SL}_2$) unifies [`OreAlgebra`](EP-0241-ore-skew-polynomial-algebras-dfinite-closure-and-frobenius.md), [`CoordinateHopfAlgebra`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md) (`HopfAlgebra` from [`EP-0206`](EP-0206-coalgebras-bialgebras-and-hopf-algebras.md)), [`GroupRepresentation`](EP-0210-group-representations-character-tables-schurs-lemma.md), and [`InvariantTheory`](EP-0214-invariant-theory-molien-series-casimir-polynomials.md).

---

## Rationale

Validated in [**EXP-0011**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/README.md) (Experiment 8) and aligned with the Grand Council and **Phase 8.5 (`EP-0250`–`EP-0254`)**:

- **⚖️ Emmy Noether (Picard–Vessiot Torsors & Subgroup Geometry)**:
  A Picard–Vessiot extension $E/k(x)$ is the differential analogue of a Galois splitting field; its differential automorphisms form an affine algebraic group $\operatorname{Gal}_\partial(E/k(x)) \subseteq \operatorname{GL}_m(k)$ whose fundamental matrix ring $R_{PV}$ is a torsor for `CoordinateHopfAlgebra` (`algebrax.variety`, `EP-0221`, grounded in `HopfAlgebra` from `EP-0206`). Symmetric powers $\operatorname{Sym}^k(L)$ correspond to symmetric tensor representations (`EP-0210`, flat Layer-1 `GroupRepresentation` protocol under `EP-0250`), turning invariant lines of $A_4, S_4, A_5$ (`EP-0214`) into rational/hyperexponential solutions of $\operatorname{Sym}^k(L)$ ($k \in \{2, 4, 6, 12\}$).
- **⚡ Claude Shannon (`square_free_decomposition` Reuse & Shared Exact Kernels)**:
  Kovacic pole-order classification requires only the **multiplicities** of finite poles of $r(x) = s(x)/t(x)$, which Yun's `square_free_decomposition(t)` (`EP-0242`) supplies with zero root factorization over $\overline{\mathbb{Q}}$. Meanwhile, `symmetric_power(L, k)`, `exterior_power(L, k)`, and Kovacic Case 1 linear solves reuse Phase 8.5 [`EP-0251`](EP-0251-sparse-linear-algebra-kernel-decompositions-and-hot-paths.md)'s consolidated exact `matrix.nullspace` / `solve_exact` kernels—staying 100% pure Python and AST-free with zero duplicated elimination loops. Exact `Fraction` arithmetic aligns with `EP-0252`'s widened `typing.N`.
- **🔬 Karl Popper (Falsifiable Obstruction Certificates & Non-Vacuous Oracles)**:
  Negative solvability claims are falsifiable algebraic theorems:
  - Every `KovacicCertificate` proving $\operatorname{Gal}_\partial = \operatorname{SL}_2$ records the exact Yun pole multiplicities, `val_inf`, and failed admissibility predicates for Cases 1–3.
  - Every positive factorization records explicit rational functions $(\omega_1, \omega_2)$ certified by exact operator multiplication $(\partial - \omega_2)(\partial - \omega_1) == L$ and cross-checked via `sympy.checkodesol`, adhering to Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts.
- **🛡️ The Golem (Strict Dennis-Point Boundary, Exact Field Mandate & Hygiene)**:
  General arbitrary-order ($n \ge 3$) Picard–Vessiot Galois group reconstruction (Hrushovski / van der Put–Singer algorithms) and arbitrary-degree algebraic number-field splitting towers are **explicitly deferred** under the Dennis Point. All rational-function operations strictly require exact characteristic-0 `Field`s (`StandardField(Fraction)`), rejecting IEEE-754 floating-point coefficients. Modules obey `EP-0254` hygiene (public-only cross-package imports, zero `EP-XXXX` references in `src/`).

---

## Specification

### 1. Symmetric Powers, Wronskians & Kovacic Solver (`src/algebrax/differential/galois.py`)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from algebrax.algebra import Field
from algebrax.differential.ore import OreOp, RationalFunc, UniPoly

V = TypeVar("V")
GaloisGroupKind = Literal["reducible_borel", "dihedral_D_inf", "finite_A4_S4_A5", "SL_2_non_liouvillian"]


@dataclass(frozen=True)
class KovacicCertificate(Generic[V]):
    """Proof-carrying Differential Galois classification certificate for u'' = r(x) u."""

    pole_multiplicities: tuple[tuple[int, int], ...]  # (multiplicity, degree_of_Q_m)
    val_at_infinity: int                              # deg(den) - deg(num)
    case1_admissible: bool
    case2_admissible: bool
    case3_admissible: bool
    group_kind: GaloisGroupKind
    riccati_factor: RationalFunc[V] | None = None     # Exact omega_1 in k(x) when Case 1 succeeds
    invariant_degree: int | None = None               # Minimal polynomial degree (1, 2, 4, 6, or 12)


@dataclass(frozen=True)
class PicardVessiotTorsor(Generic[V]):
    """Algebraic torsor descriptor linking an Ore operator's solution space to a CoordinateHopfAlgebra."""

    operator: OreOp[RationalFunc[V]]
    order: int
    wronskian_log_deriv: RationalFunc[V]  # -a_{m-1}(x) = -Tr(C_L)
    sl_reduced: bool                      # True iff a_{m-1} == 0 (Gal_d <= SL_m)
    galois_group_kind: str


def wronskian_operator(monic_op: OreOp[RationalFunc[V]], field: Field[V]) -> OreOp[RationalFunc[V]]:
    r"""Return order-1 differential Ore operator $\partial + a_{m-1}(x)$ annihilating the Wronskian $W$."""
    ...


def to_liouville_normal_form(
    order2_op: OreOp[RationalFunc[V]],
    field: Field[V],
) -> tuple[RationalFunc[V], RationalFunc[V]]:
    r"""Transform $y'' + a_1 y' + a_0 y = 0$ into $u'' = r(x) u$ via $y = u \exp(-\frac{1}{2}\int a_1 dx)$.

    Returns `(r(x), gauge_log_deriv)` where `gauge_log_deriv = -a_1 / 2`.
    """
    ...


def symmetric_power(
    monic_op: OreOp[RationalFunc[V]],
    k: int,
    field: Field[V],
) -> OreOp[RationalFunc[V]]:
    r"""Compute minimal-order differential Ore operator $\operatorname{Sym}^k(L)$ annihilating $k$-fold solution products."""
    ...


def exterior_power(
    monic_op: OreOp[RationalFunc[V]],
    k: int,
    field: Field[V],
) -> OreOp[RationalFunc[V]]:
    r"""Compute minimal-order differential Ore operator $\Lambda^k(L)$ annihilating $k \times k$ Wronskian minors."""
    ...


def kovacic_classify(
    r_func: RationalFunc[V],
    field: Field[V],
) -> KovacicCertificate[V]:
    r"""Evaluate Kovacic pole/infinity admissibility and classify Liouvillian solvability of $u'' = r(x) u$."""
    ...


def kovacic_factorize(
    order2_op: OreOp[RationalFunc[V]],
    field: Field[V],
) -> tuple[OreOp[RationalFunc[V]], OreOp[RationalFunc[V]], KovacicCertificate[V]] | KovacicCertificate[V]:
    r"""Attempt exact order-1 factorization $L = (\partial - \omega_2)(\partial - \omega_1)$ over $k(x)$.

    Returns `(left_factor, right_factor, cert)` on Case 1 reducibility, or `cert` on non-reducible / SL_2 cases.
    """
    ...
```

### 2. Bridges to Existing Continents
- **Companion Matrix Bridge (`EP-0241`)**: `wronskian_operator(L)` extracts $-\operatorname{Tr}(C_L)$ directly from `differential_companion_matrix(L)` (`EP-0241`), certifying when $\operatorname{Gal}_\partial(L) \subseteq \operatorname{SL}_m$.
- **Hopf & Variety Bridge (`EP-0221` / `EP-0206`)**: `PicardVessiotTorsor` exposes the defining determinant/invariant polynomial relations of the Galois torsor as generators for `CoordinateHopfAlgebra` (`algebrax.variety`, `EP-0221`, built on `HopfAlgebra` from `EP-0206`) and `AffineVariety` (`EP-0221`).
- **Representation & Invariant Bridge (`EP-0210` / `EP-0214`)**: `symmetric_power(L, k)` for $k \in \{2, 4, 6, 12\}$ supplies the differential counterpart to invariant ring degrees for $D_\infty, A_4, S_4, A_5$.

### 3. Verification Oracles (`src/algebrax/verification/_differential.py`)

Exported publicly via `algebrax.verification` (complying with Phase 8.5 [`EP-0253`](EP-0253-verification-engine-hardening-and-grounded-proofs.md) non-vacuous sample contracts):

- `verify_differential_galois_laws(order2_op, field)`:
  1. **Operator Factorization Identity**: Whenever `kovacic_factorize` returns `(L_left, L_right, cert)`, verifies `ore.mul(L_left, L_right) == monic(order2_op)` identically in $k(x)[\partial_x]$.
  2. **Symmetric Power Annihilation Law**: Verifies `symmetric_power(L, k)` reproduces exact known operators ($\operatorname{Sym}^2(\partial^2 + 1) = \partial^3 + 4\partial$, $\operatorname{Sym}^2(\partial^2 - x) = \partial^3 - 4x\partial - 2$) and matches `SymPy` differential evaluation (`0` residual).
  3. **Wronskian Abel–Liouville Identity**: Verifies $\Lambda^m(L) == \text{wronskian\_operator}(L) == \partial + a_{m-1}(x)$.
  4. **Obstruction Soundness**: Verifies Airy $y'' - xy = 0$ returns `group_kind == "SL_2_non_liouvillian"` with all three Kovacic cases `False`.

---

## Backwards Compatibility

100% additive and backwards compatible. Adds `algebrax.differential.galois` without modifying finite-field `GaloisField` (`algebrax.algebra` / `algebrax.galois`) or breaking any existing algebraic hierarchy or `EP-0240`–`EP-0242` APIs.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add `docs/guide/differential/differential_galois_and_kovacic.md` explaining the analogy *"Polynomial roots : Classical Galois :: Linear ODE solutions : Picard–Vessiot & Kovacic"* with concrete Airy ($\operatorname{SL}_2$) and Riccati apparent-singularity walkthroughs.
- **Recipe**: Add `recipes/differential_galois_kovacic.py` demonstrating $\operatorname{Sym}^k(L)$ invariant extraction, exact factorization of $y'' - (x^2 + 3)y = 0$, and certifying Airy non-Liouvillianity.

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/sources/prototype_differential_algebra.py) (Experiment 8) and captured in [`raw/prototype_benchmark_output.txt`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0011-differential-and-ore-algebras/raw/prototype_benchmark_output.txt).

---

## Rejected Ideas

1. **Full Arbitrary-Order ($n \ge 3$) Picard–Vessiot Galois Group Solver (Hrushovski / van der Put–Singer)**:
   - *Rejected*: Violates the Dennis Point. Arbitrary-order Tannakian reconstruction requires deep algebraic-number-field splitting towers and Lie-algebra ideal decomposition disproportionate to AlgebraX's pure-Python scope.
2. **Folding Kovacic Factorization into `EP-0241` (`OreAlgebra`)**:
   - *Rejected*: `EP-0241` already spans skew-polynomial unification (`differential`, `shift`, `difference`, `q_difference`), `gcrd`/`lclm`, Frobenius indicial roots, and companion matrices. Differential Galois Theory depends jointly on `EP-0241` (Ore operators), `EP-0242` (`square_free_decomposition`), `EP-0221`/`EP-0206` (`CoordinateHopfAlgebra`/`HopfAlgebra`), and `EP-0210`/`EP-0214` (finite $\operatorname{SL}_2$ subgroups), warranting a dedicated, cohesive EP.
3. **Replacing `algebrax.galois` ($\operatorname{GF}(p^m)$)**:
   - *Rejected*: `GaloisField` ($\operatorname{GF}(p^m)$, canonically in `algebrax.algebra` with domain facade `algebrax.galois`, `EP-0112`) serves AES/coding theory and finite-field varieties; keeping Differential Galois Theory cleanly inside `algebrax.differential.galois` avoids breaking backwards compatibility or overloading finite-field namespaces.

---

## Open Questions

- [ ] Whether `kovacic_factorize` Case 2 (dihedral $D_\infty$, quadratic invariant) and Case 3 (finite primitive $A_4, S_4, A_5$) should cap algebraic extension degree or expose an optional `SymPy` root-splitting hook when polynomial invariants require irrational roots over $\mathbb{Q}$.
- [ ] Whether to extend `symmetric_power` in Phase 11 beyond order 2 to general order-$m$ differential operators via `EP-0241`'s `symmetric_product` tensor recurrence.

---

## Change Log

* **2026-11-15:**
  * Initial Draft authored for Phase 11 from `EXP-0011` Experiment 8.
* **2026-11-26:**
  * Aligned with Phase 8.5 (`EP-0250`–`EP-0254`): corrected `CoordinateHopfAlgebra` attribution to `EP-0221` (`algebrax.variety`), noted canonical `GaloisField` location in `algebrax.algebra`, switched private `algebra._field` import to public `algebrax.algebra`, documented `EP-0251` exact linear-algebra kernel reuse, updated verification path to `src/algebrax/verification/_differential.py`, and noted `EP-0253`/`EP-0254` contracts.
