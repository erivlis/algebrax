---
title: "EP-0222: Tropical Varieties, Newton Polytopes & Balanced Polyhedral Complexes"
description: "Formalize tropical polynomials over TropicalSemiring, tropical hypersurfaces T(f), dual Newton polytope subdivisions, and Noether zero-tension vertex balancing in algebrax.variety."
icon: lucide/compass
status: draft
---

# EP-0222: Tropical Varieties, Newton Polytopes & Balanced Polyhedral Complexes

| Field             | Value                                                                                          |
|:------------------|:-----------------------------------------------------------------------------------------------|
| **EP**            | 0222                                                                                           |
| **Title**         | Tropical Varieties, Newton Polytopes & Balanced Polyhedral Complexes                           |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                                    |
| **Sponsor**       | Core Maintainers                                                                               |
| **Delegate**      | 🧭 Explorer (Tropical Frontier), ⚖️ Noether (Zero-Tension Balancing) & ⚡ Shannon (Carrier Reuse) |
| **Status**        | Draft                                                                                          |
| **Type**          | Standards Track                                                                                |
| **Created**       | 2026-11-14                                                                                     |
| **Updated**       | 2026-11-14                                                                                     |
| **Replaces**      | —                                                                                              |
| **Superseded-By** | —                                                                                              |

---

## Abstract

This proposal extends `algebrax.variety` into **Tropical Algebraic Geometry**—the piece-wise linear "combinatorial shadow" of classical algebraic geometry over the idempotent `TropicalSemiring` $(\mathbb{R} \cup \{+\infty\}, \min, +)$. Reusing the exact same unboxed multivariate polynomial carrier `dict[tuple[int, ...], float]` from [`EP-0220`](EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md), EP-0222 introduces:

1. **Tropical Multivariate Polynomials (`TropicalPolynomialAlgebra`)**:
   Evaluates and composes multivariate tropical polynomials
   $$f_{\text{trop}}(w) = \bigoplus_{\alpha \in \mathcal{A}} c_\alpha \odot w^{\odot \alpha} = \min_{\alpha \in \mathcal{A}} \left(c_\alpha + \langle \alpha, w \rangle\right)$$
   over `TropicalSemiring` (min-plus) or `MaxPlusSemiring` (max-plus).
2. **Tropical Hypersurfaces (`TropicalHypersurface`)**:
   Computes the tropical zero locus $\mathcal{T}(f) \subseteq \mathbb{R}^n$—the set of points $w \in \mathbb{R}^n$ where the minimum in $f_{\text{trop}}(w)$ is achieved by **at least two** distinct monomials simultaneously (the non-differentiable corner locus).
3. **Newton Polytopes & Dual Regular Subdivisions (`newton_subdivision`)**:
   Constructs the lower convex hull of the lifted support $\{( \alpha, c_\alpha ) \in \mathbb{Z}^n \times \mathbb{R}\}$ and maps lower facets to tropical vertices and edges via Legendre–Fenchel / polyhedral duality.
4. **Noether Zero-Tension Balancing Verification (`verify_tropical_balancing`)**:
   Verifies the fundamental conservation law of tropical geometry: at every tropical vertex $v \in \mathcal{T}(f)$, the weighted primitive integer direction vectors $u_e \in \mathbb{Z}^n$ of all outgoing rays/edges sum identically to zero:
   $$\sum_{e \ni v} m_e \, u_e = \mathbf{0}$$

---

## Motivation

Standard computer algebra systems (such as SymPy) treat polynomials exclusively over classical rings $(+, \times)$ and have no native concept of tropical varieties. Conversely, AlgebraX was built from day one around **Semiring Polymorphism** (`TropicalSemiring`, `MaxPlusSemiring`) and **Discrete Topology** (`SimplicialComplex`, `CellularSheaf`):

1. **Unifying Classical & Tropical Geometry on One Carrier**:
   In AlgebraX, a multivariate polynomial `p: dict[tuple[int, ...], float]` does not store a ring inside the data structure. Passed to `MultivariatePolynomialAlgebra(field)` ([`EP-0220`](EP-0220-multivariate-polynomial-algebra-and-groebner-ideals.md)), it defines a classical smooth/algebraic curve; passed to `TropicalHypersurface(p)`, the *exact same dictionary* defines a piecewise-linear polyhedral skeleton!
2. **Combinatorial Root Bounds & Viro's Patchworking (Bernstein–Kushnirenko Theorem)**:
   The Newton polytope subdivision of a tropical polynomial counts intersection numbers (Bézout's theorem in the tropical plane), bounds the number of isolated roots of sparse polynomial systems, and models phylogenetic trees, auction equilibrium boundaries, and neural network ReLU decision boundaries.
3. **Bridging `algebrax.variety` with `algebrax.topology`**:
   The bounded cells of a 2D/3D tropical hypersurface form a 1D/2D cell complex (graph/polyhedral complex) whose Euler characteristic, Betti numbers ($b_0, b_1$, genus $g$), and cellular sheaf flows can be analyzed directly by `algebrax.topology`.

---

## Rationale

Validated in [**EXP-0009**](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/README.md) (Experiment 5, grounded in Richter-Gebert, Sturmfels & Theobald [RGST-2003]) and aligned with the Grand Council:

- **⚡ Claude Shannon (Zero-Copy Carrier Polymorphism)**:
  Zero new data structures are needed for tropical polynomials: `SparseMPoly[float] = dict[tuple[int, ...], float]` is shared 1-to-1 with `EP-0220`.
- **⚖️ Emmy Noether (The Zero-Tension Balancing Conservation Law)**:
  A polyhedral complex is a tropical variety if and only if it satisfies the **Balancing Condition** ($\sum m_e u_e = \mathbf{0}$) at every vertex. Physically, a tropical curve is a mechanical web of strings under integer tension $m_e$ in static equilibrium—a discrete conservation law dual to the closure of cycles in the Newton polygon subdivision.
- **🔬 Karl Popper (Falsifiable Corner-Locus & Balancing Oracles)**:
  Every extracted vertex $v \in \mathcal{T}(f)$ is empirically falsifiable on two independent axes:
  1. **Multi-Attainment**: At least $n + 1$ monomials achieve the exact minimum $f_{\text{trop}}(v)$ at $v$.
  2. **Zero-Tension Equilibrium**: The dual normal primitive vectors around $v$ sum to $\mathbf{0} \in \mathbb{Z}^n$.
- **💡 Richard Feynman (The Freshman Test)**:
  *"In tropical math, addition is `min` and multiplication is `+`, so a polynomial like $x^2 + xy + y^2$ becomes $\min(2x, x+y, 2y)$—a roof made of flat planes! Since $\min$ can never equal zero by cancelling positive and negative numbers, what replaces 'roots'? The creases where two or more roof planes collide!"*

---

## Specification

### 1. Tropical Polynomial Evaluation & Legendre Dual (`src/algebrax/variety/tropical.py`)

```python
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from algebrax.algebra._polynomial import Monomial, SparseMPoly
from algebrax.semiring.optimization import MaxPlusSemiring, TropicalSemiring


def tropical_eval(
    poly: SparseMPoly[float],
    point: Sequence[float],
    semiring: TropicalSemiring | MaxPlusSemiring | None = None,
) -> float:
    r"""Evaluate tropical polynomial $\bigoplus_{\alpha} (c_\alpha \odot w^{\odot \alpha})$ at `point`."""
    ...


def active_monomials(
    poly: SparseMPoly[float],
    point: Sequence[float],
    *,
    tol: float = 1e-9,
    semiring: TropicalSemiring | MaxPlusSemiring | None = None,
) -> set[Monomial]:
    r"""Return all monomials $\alpha$ that attain the tropical optimum at `point`."""
    ...
```

### 2. `TropicalHypersurface` & Newton Subdivision (`src/algebrax/variety/tropical.py`)

```python
@dataclass(frozen=True)
class TropicalCellComplex:
    r"""Polyhedral skeleton of a tropical hypersurface $\mathcal{T}(f) \subseteq \mathbb{R}^n$.

    Attributes:
        vertices: Coordinates of tropical vertices where >= n+1 monomials tie.
        vertex_monomials: Active monomial sets (dual Newton cells) at each vertex.
        bounded_edges: Pairs of vertex indices (u, v) with integer lattice weight m_e.
        rays: Outgoing infinite rays (vertex_idx, direction_tuple, weight).
    """

    vertices: tuple[tuple[float, ...], ...]
    vertex_monomials: tuple[frozenset[Monomial], ...]
    bounded_edges: tuple[tuple[int, int, int], ...]
    rays: tuple[tuple[int, tuple[int, ...], int], ...]


class TropicalHypersurface(GeometricVariety[float]):
    r"""The tropical hypersurface $\mathcal{T}(f) = \{w \in \mathbb{R}^n \mid \text{optimum attained } \ge 2 \text{ times}\}$.

    Implements `GeometricVariety[float]` (`HasPointLocus[float]`, `HasDimension`) from `algebrax.variety._mixins`.
    """

    def __init__(
        self,
        poly: SparseMPoly[float],
        n_vars: int = 2,
        *,
        semiring: TropicalSemiring | MaxPlusSemiring | None = None,
        tol: float = 1e-9,
    ) -> None: ...

    @property
    def ambient_dimension(self) -> int:
        """Ambient Euclidean/tropical space dimension n of R^n."""
        return self.n_vars

    def dimension(self) -> int:
        """Return polyhedral dimension of the tropical hypersurface (n - 1 if >= 2 monomials, else -1)."""
        return self.n_vars - 1 if len(self.poly) >= 2 else -1

    def contains_point(self, point: Sequence[float]) -> bool:
        """Return True iff >= 2 monomials attain the tropical optimum at `point`."""
        return len(active_monomials(self.poly, point, tol=self.tol, semiring=self.semiring)) >= 2

    def skeleton(self) -> TropicalCellComplex:
        """Compute the polyhedral cell complex (vertices, bounded edges, rays, weights)."""
        ...

    def genus(self) -> int:
        """Compute the tropical curve genus (number of interior lattice points in active subdivision)."""
        ...

    def balance_residuals(self) -> list[tuple[int, ...]]:
        r"""Compute $\sum_{e \ni v} m_e u_e \in \mathbb{Z}^n$ at every vertex (must equal $\mathbf{0}$)."""
        ...

    def to_simplicial_complex(self) -> SimplicialComplex[int]:
        r"""Convert the bounded polyhedral skeleton of $\mathcal{T}(f)$ into an `algebrax.topology.SimplicialComplex`.

        Enables direct topological invariant calculation via `betti_numbers(trop.to_simplicial_complex())`,
        where $b_1(\mathcal{T}_{\text{bounded}}(f)) == \operatorname{genus}(f)$ for smooth tropical plane curves.
        """
        ...


def tropical_plucker_relations(
    k_subspace: int = 2,
    n_ambient: int = 4,
) -> list[SparseMPoly[float]]:
    r"""Return the tropical Plücker polynomials for the Dressian / tropical Grassmannian $\operatorname{Trop}(\operatorname{Gr}(k, n))$.

    For $(k, n) = (2, 4)$, returns the 3-term tropical quadric
    $\min(p_{12} + p_{34},\; p_{13} + p_{24},\; p_{14} + p_{23})$ (the four-point tree metric condition
    in phylogenetics and crystal limit of $U_q(\mathfrak{sl}_n)$ in `EP-0215`).
    """
    ...
```

### 3. Verification Oracles (`src/algebrax/verification.py`)

- `verify_tropical_hypersurface_laws(hypersurface)`:
  1. Verifies every vertex $v$ satisfies `len(active_monomials(poly, v)) >= n_vars + 1`.
  2. Verifies the Noether zero-tension balancing condition: every tuple in `hypersurface.balance_residuals()` is identically `(0, ..., 0)`.
  3. Verifies every midpoint of a bounded edge satisfies `hypersurface.contains_point(midpoint) == True`.
  4. Verifies topological genus duality: for smooth 2D tropical curves, `betti_numbers(hypersurface.to_simplicial_complex())[1] == hypersurface.genus()`.

---

## Backwards Compatibility

Strictly additive. Resides in `src/algebrax/variety/tropical.py` and re-exports through `algebrax.variety`.

---

## How to Teach This / Documentation Plan

- **User Guide**: Add a tropical geometry section in `docs/guide/algebra/varieties_and_geometry.md` and cross-link from `docs/guide/semirings/optimization.md` showing how `TropicalSemiring` extends from shortest-path graphs to tropical algebraic curves and ReLU neural decision boundaries.
- **Recipe**: Add `recipes/tropical_algebraic_curves.py` (and synced `.ipynb`).

---

## Reference Implementation

Prototyped and verified in [`references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py`](https://github.com/erivlis/algebrax/blob/main/references/explorations/EXP-0009-algebraic-and-tropical-varieties/sources/prototype_varieties.py) (Experiment 5), extracting all 4 vertices of a tropical conic with exact `(0, 0)` balancing residuals.

---

## Rejected Ideas

1. **Requiring External Polyhedral C Libraries (`cddlib`, `polymake`, `ppl`)**:
   - *Rejected*: Violates AlgebraX's zero-heavy-dependency pure-Python mandate. For 2D and 3D tropical hypersurfaces (curves and surfaces), exact lower-hull facet enumeration over sparse support $\mathcal{A}$ runs in sub-millisecond pure Python.
2. **Separate `TropicalPolynomial` Wrapper Class**:
   - *Rejected*: Keeping `poly` as a plain `dict[tuple[int, ...], float]` preserves carrier symmetry with `MultivariatePolynomialAlgebra`.

---

## Open Questions

- [ ] Extending `.to_simplicial_complex()` with a `.to_cellular_sheaf()` constructor that attaches the integer lattice $\mathbb{Z}^n$ to edges and vertices so `algebrax.topology.sheaf` can verify the Noether balancing law as a harmonic 1-cochain $\delta^* w = 0$.

---

## Change Log

* **2026-11-14:**
  * Initial Draft authored for Phase 9 from `EXP-0009`.
