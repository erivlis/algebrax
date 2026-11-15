---
title: "EP-0214: Invariant Theory, Molien Series & Casimir Polynomials"
description: "Formalize classical invariant rings, the Reynolds projection operator, Molien's generating series, and polynomial Casimir invariants over sparse matrix actions."
icon: lucide/shield-check
status: draft
---

# EP-0214: Invariant Theory, Molien Series & Casimir Polynomials

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0214                                                                              |
| **Title**         | Invariant Theory, Molien Series & Casimir Polynomials                             |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | ⚖️ Noether (Invariant Rings) & ⚡ Shannon (Sparse Monomial Actions)               |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-15                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational framework for **Classical Invariant Theory** in AlgebraX, formalizing polynomial functions and algebraic tensors that remain invariant under linear group actions and Lie symmetries atop [`algebrax.group`](EP-0210-group-representations-character-tables-schurs-lemma.md), [`algebrax.rep`](EP-0210-group-representations-character-tables-schurs-lemma.md), and [`algebrax.lie`](EP-0211-lie-algebra-representations-clebsch-gordan.md). EP-0214 introduces:

1. **The Polynomial Reynolds Symmetrization Operator (`algebrax.rep.invariant`)**:
   An idempotent projection operator $\mathcal{R} : K[V] \to K[V]^G$ complementing linear operator averaging (`reynolds_average` in `algebrax.rep.group`):
   $$\mathcal{R}(f) = \frac{1}{|G|} \sum_{g \in G} f(\rho(g^{-1}) \mathbf{x}), \quad \mathcal{R}^2 = \mathcal{R}$$
2. **Molien's Generating Series (`algebrax.rep.invariant`)**:
   Exact computation of the Hilbert series of the graded invariant ring $K[V]^G = \bigoplus_{d=0}^\infty K[V]_d^G$ using Theodor Molien's 1897 determinant formula over `FiniteGroup[G]` or raw element sequences:
   $$M(t) = \sum_{d=0}^\infty \dim(K[V]_d^G) t^d = \frac{1}{|G|} \sum_{g \in G} \frac{1}{\det(\mathbf{I}_n - t \rho(g))}$$
   determining the exact number of linearly independent invariants at degree $d$ without expanding monomials.
3. **Primary & Secondary Invariants (Cohen–Macaulay Decomposition)**:
   Decomposing the invariant ring as a free module over a polynomial subring (Hochster–Eagon theorem):
   $$K[V]^G = \bigoplus_{j=1}^m \eta_j \cdot K[\theta_1, \dots, \theta_n]$$
   where $\theta_i$ are algebraically independent primary invariants, and $\eta_j$ are secondary invariants.
4. **High-Order Lie Casimir Invariants (`algebrax.rep.lie`, re-exported in `algebrax.lie`)**:
   Extending [`EP-0211`](EP-0211-lie-algebra-representations-clebsch-gordan.md) quadratic Casimirs to higher-order polynomial invariants in the symmetric algebra $S(\mathfrak{g})^\mathfrak{g} \cong \mathcal{Z}(U(\mathfrak{g}))$, such as the symmetric cubic Casimir $d_{ijk}$ for $\mathfrak{sl}_3$.
5. **Property-Based Verification (`src/algebrax/verification.py`)**:
   Automated verification of Reynolds idempotency (`verify_reynolds_idempotency`), polynomial invariance $f(\rho(g) \mathbf{x}) = f(\mathbf{x})$ (`verify_polynomial_invariance`), and Molien series power series expansion matching monomial counting (`verify_molien_expansion`), returning `dict[str, bool]`.

---

## Motivation

Invariant theory—founded by Cayley, Sylvester, Gordan, and Hilbert—is the historical birthplace of modern abstract algebra. In modern science:

1. **Feature Engineering & Machine Learning**: Symmetries in data (rotations, reflections, permutations) require invariant features. Machine learning architectures (SE(3)-equivariant networks, Graph Neural Networks) rely on polynomial invariants of groups to guarantee invariance.
2. **Physics & Conserved Quantities**: By Emmy Noether’s theorem, every continuous symmetry produces an invariant conservation law. Casimir polynomials in Lie algebras classify quantum charges, particle mass formulas, and Casimir energy.
3. **Counting Symmetries via Molien’s Formula**: Knowing *a priori* how many independent invariants exist at degree $d$ (via Molien series) prevents redundant search and verifies complete invariant generating sets.

---

## Rationale & Council Alignment

- **⚖️ Noether (Foundational Invariant Theory)**:
  Emmy Noether proved in 1915 (*Der Endlichkeitssatz der Invarianten endlicher Gruppen*) that the invariant ring of a finite group is always finitely generated by polynomials of degree at most $|G|$. This EP is dedicated directly to her mathematical legacy.
- **⚡ Shannon (Zero Bloat & Sparse Determinant Evaluation)**:
  Molien’s formula evaluates $\det(\mathbf{I} - t \rho(g))$ via characteristic polynomials, avoiding explosive $O(n^d)$ monomial generation. Consolidating polynomial Reynolds and Molien helpers into `src/algebrax/rep/invariant.py` while routing Lie Casimir tensors alongside `quadratic_casimir` in `src/algebrax/rep/lie.py` avoids fragmenting cohesive invariants across tiny modules.
- **🔬 Popper (Falsifiable Invariants)**:
  Every generated invariant $f(\mathbf{x})$ is subjected to empirical falsification: evaluating $|f(\rho(g) \mathbf{x}) - f(\mathbf{x})| < 10^{-12}$ for randomized probe vectors $\mathbf{x} \in \mathbb{R}^n$ and all $g \in G$.
- **🧩 Russell (Graded Algebra Taxonomy)**:
  Correctly models $K[V]^G$ as a graded sub-algebra of the polynomial algebra $K[x_1, \dots, x_n]$ ([`EP-0192`](EP-0192-unifying-domain-objects-with-algebraic-hierarchy.md)).
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"If you spin a square on a table, $x^2 + y^2$ doesn't change, and $x^4 + y^4$ doesn't change. Molien's series is a magic cash register that tells you exactly how many such unbreakable formulas exist at each power!"*

---

## Specification

### 1. Polynomial Reynolds Symmetrizer & Molien Series (`src/algebrax/rep/invariant.py`)

```python
"""Polynomial invariant theory: Reynolds projection operator and Molien series."""

from __future__ import annotations

from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass
from typing import TypeVar

from algebrax.group.finite import FiniteGroup
from algebrax.matrix import matvec, transpose
from algebrax.rep.group import GroupRepresentation
from algebrax.semiring import RealSemiring

G = TypeVar("G", bound=Hashable)


def reynolds_polynomial_operator(
    poly_eval: Callable[[Sequence[float]], float],
    rep: GroupRepresentation[float, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
) -> Callable[[Sequence[float]], float]:
    """Return invariant polynomial f_inv(x) = (1/|G|) sum_g f(rho(g^{-1}) x).

    Complements operator-level `reynolds_average` in `algebrax.rep.group`.
    """
    elements = list(elements_or_group.elements) if isinstance(elements_or_group, FiniteGroup) else list(elements_or_group)
    order = len(elements)
    semiring = RealSemiring()

    def invariant_poly(x: Sequence[float]) -> float:
        total = 0.0
        x_sparse = {i: val for i, val in enumerate(x) if val != 0.0}
        for g in elements:
            # Prefer exact rep(group.inv(g)) when FiniteGroup is given; fallback transpose for orthogonal reps
            inv_g = elements_or_group.inv(g) if isinstance(elements_or_group, FiniteGroup) else None
            mat = rep(inv_g) if inv_g is not None else transpose(rep(g))
            x_g_sparse = matvec(mat, x_sparse, semiring)
            x_g = [x_g_sparse.get(i, 0.0) for i in range(len(x))]
            total += poly_eval(x_g)
        return total / order

    return invariant_poly


@dataclass(frozen=True)
class MolienSeries:
    """Rational generating function M(t) = P(t) / Q(t) for invariant dimensions."""

    numerator_coeffs: Sequence[int]    # Secondary invariant degrees
    denominator_factors: Sequence[int] # Primary invariant degrees (1 - t^d)

    def coefficient(self, degree: int) -> int:
        """Extract dimension of invariants at given degree d: dim(K[V]_d^G)."""
        ...


def compute_molien_series(
    rep: GroupRepresentation[float, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
) -> MolienSeries:
    """Compute Molien series M(t) = (1/|G|) sum_{g in G} 1 / det(I - t rho(g))."""
    ...
```

### 2. High-Order Lie Casimir Invariants (`src/algebrax/rep/lie.py`, re-exported in `algebrax.lie`)

```python
"""Higher-order Casimir polynomial invariants in symmetric algebra S(g)."""

from algebrax.lie import LieAlgebra
from algebrax.rep.lie import LieRepresentation
from algebrax.typing import SparseTensor


def cubic_casimir_tensor(
    algebra: LieAlgebra,
    rep: LieRepresentation[float] | None = None,
) -> SparseTensor[int, float]:
    """Compute symmetric cubic Casimir d_{ijk} = Tr(rho(X_i) (rho(X_j) rho(X_k) + rho(X_k) rho(X_j))).

    Defaults to adjoint_representation(algebra). Non-zero for sl_n (n >= 3), vanishing for sl_2 and so_n.
    """
    ...
```

### 3. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for invariant polynomials and Molien series."""

def verify_reynolds_idempotency(
    reynolds_fn: Callable[[Callable[..., float]], Callable[..., float]],
    test_poly: Callable[[Sequence[float]], float],
    test_point: Sequence[float],
    tol: float = 1e-11,
) -> dict[str, bool]:
    """Verify R(R(f))(x) == R(f)(x)."""
    ...

def verify_polynomial_invariance(
    poly: Callable[[Sequence[float]], float],
    rep: GroupRepresentation[float, G],
    elements_or_group: FiniteGroup[G] | Sequence[G],
    dimension: int,
    num_probes: int = 50,
    seed: int = 42,
    tol: float = 1e-11,
) -> dict[str, bool]:
    """Verify poly(rho(g) x) == poly(x) for all g in G over randomized Gaussian probe vectors.

    Guards against false passes on accidental fixed points or symmetric sub-manifolds.
    """
    ...

def verify_molien_expansion(
    series: MolienSeries,
    actual_dimensions: Sequence[int],
) -> dict[str, bool]:
    """Verify series coefficients match dimensions of invariant subspaces."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Group invariant tools live in `algebrax.rep` (`src/algebrax/rep/invariant.py`), high-order Casimirs extend `algebrax.rep.lie` / `algebrax.lie`, and all verifiers reside in `src/algebrax/verification.py`, integrating seamlessly with `algebrax.group.FiniteGroup` and `algebrax.algebra` polynomial modules.

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/invariant_theory.md`:
  - Invariants of the Klein 4-group $V_4$ and cyclic group $C_4$.
  - Computing the Molien series of the icosahedral group $A_5$.
  - Deriving the cubic Casimir of $SU(3)$ color symmetry.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for Molien's determinant formula and the Reynolds operator.

---

## Reference Implementation

Implementations will reside in `src/algebrax/rep/invariant.py`, `src/algebrax/rep/lie.py` (with `algebrax.lie` re-exports), and `src/algebrax/verification.py`.

---

## Rejected Ideas

1. **Pure Monomial Gröbner Basis Engines for Dimension Counting**:
   - *Rejected*: Computing invariant Hilbert dimensions exclusively via general Gröbner bases (Buchberger’s algorithm) is doubly exponential, whereas Molien’s formula provides the dimensions in polynomial time using linear algebra determinants. (Once invariant generators $\pi_1, \dots, \pi_m$ are found, their algebraic syzygies and GIT quotient variety $V // G$ are computed via [`EP-0220`](EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md) and `syzygy_variety` in [`EP-0221`](EP-0221-affine-algebraic-varieties-and-stickelberger-solvers.md)).
2. **Dense Multidimensional Arrays for High-Order Casimirs**:
   - *Rejected*: High-order invariant tensors $d_{i_1 \dots i_k}$ have $n^k$ entries but are highly symmetric and sparse. They must be stored in `algebrax.tensor.SparseTensor`.

---

## Open Questions

- [ ] Algorithm for automated primary invariant generation via King's algorithm.
- [ ] Invariant theory for continuous compact Lie groups via Weyl integration formula.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
* **2026-11-15:**
  * Aligned specification to consolidate Reynolds polynomial invariants and Molien series into `src/algebrax/rep/invariant.py` accepting `FiniteGroup[G]`, route `cubic_casimir_tensor` into `src/algebrax/rep/lie.py` (re-exported in `algebrax.lie`), and place verifiers returning `dict[str, bool]` in `src/algebrax/verification.py`.
