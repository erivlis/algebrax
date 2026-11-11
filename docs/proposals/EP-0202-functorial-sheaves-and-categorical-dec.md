---
title: "EP-0202: Functorial Sheaves & Categorical DEC"
description: "Formalize Cellular Sheaves as contravariant functors from cell posets into the matrix category Mat(R), establish the coboundary operator as a natural transformation, and unify Sheaf Cohomology with Discrete Exterior Calculus."
icon: lucide/layers
status: draft
---

# EP-0202: Functorial Sheaves & Categorical DEC

| Field             | Value                                                                      |
|:------------------|:---------------------------------------------------------------------------|
| **EP**            | 0202                                                                       |
| **Title**         | Functorial Sheaves & Categorical DEC                                       |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                |
| **Sponsor**       | Core Maintainers                                                           |
| **Delegate**      | ⚖️ Noether (Topological Invariants) & 🔬 Popper (Cohomological Nilpotency) |
| **Status**        | Draft                                                                      |
| **Type**          | Standards Track                                                            |
| **Created**       | 2026-10-27                                                                 |
| **Updated**       | 2026-10-27                                                                 |
| **Replaces**      | —                                                                          |
| **Superseded-By** | —                                                                          |

---

## Abstract

This proposal elevates AlgebraX's cellular sheaf mechanics (`algebrax.sheaf`) and Discrete Exterior Calculus (`algebrax.dec`) into a unified, functorial architecture anchored by the category theory framework introduced in [EP-0200](EP-0200-categorical-abstractions-and-enriched-matrices.md). EP-0202 establishes:
1. **Cellular Sheaves as Contravariant Functors**: A cellular sheaf $\mathcal{F}$ over a cell complex $K$ is formalized as a functor $\mathcal{F}: \mathbf{Poset}(K)^{\text{op}} \to \mathbf{Mat}(\mathbb{R})$ assigning stalks $\mathcal{F}(\sigma)$ to cells and restriction matrices $\mathcal{E}_{\sigma \trianglelefteq \tau}$ to incidence relations.
2. **DEC as the Constant Sheaf**: Proves and operationalizes the identity between standard Discrete Exterior Calculus (DEC) and the constant rank-1 sheaf $\underline{\mathbb{R}}$, showing that the DEC exterior derivative $\mathbf{d}_k$ is the cellular coboundary of the trivial sheaf.
3. **Coboundary as a Natural Transformation**: Formalizes the degree-$k$ coboundary operator $\delta^k: C^k(K; \mathcal{F}) \to C^{k+1}(K; \mathcal{F})$ as a natural transformation between cochain functors, with guaranteed nilpotency $\delta^{k+1} \circ \delta^k = 0$.
4. **General Sheaf Laplacian**: Constructs the generalized Hodge-Sheaf Laplacian $L_k = \delta_k^* \delta_k + \delta_{k-1} \delta_{k-1}^*$ as a categorical matrix operator, bridging network consensus, distributed synchronization, and field theories.
5. **Executable Cohomological Invariants**: Implements `verify_sheaf_functoriality`, `verify_coboundary_nilpotency`, and `verify_sheaf_laplacian_properties` in `algebrax.verification`.

All implementations maintain raw sparse dictionary matrices (`dict[K, dict[V, S]]`) for all restriction maps, boundary matrices, and Laplacians, with zero heap-boxing overhead.

---

## Motivation

In Phase 4, AlgebraX introduced `CellularSheaf` ([EP-0161](EP-0161-cellular-sheaves-and-network-laplacians.md)) and Discrete Exterior Calculus ([EP-0160](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md)). While computationally functional, they currently exist as isolated silos:
- `CellularSheaf` uses procedural dictionary lookups for stalks and restrictions, with no link to `algebrax.category`.
- `algebrax.dec` calculates simplicial boundary operators $\partial_k$ and Hodge Laplacians $\Delta_k$ independently of sheaf structures.
- There is no formal realization that **Discrete Exterior Calculus is simply the special case of cellular sheaf theory with constant rank-1 stalks** $\mathcal{F}(\sigma) \cong \mathbb{R}$.

Foundational applied topology literature demonstrates that these subjects are one and the same:
1. **Justin Curry (2014)** (*Sheaves, Cosheaves, and Applications*, Ph.D. thesis, University of Pennsylvania) established that cellular sheaves on cell complexes are precisely diagrams indexed by the face poset category $\mathbf{Poset}(K)$, and their global sections are limits over this category.
2. **Robert Ghrist (2014)** (*Elementary Applied Topology*) demonstrated that cellular sheaves generalize scalar graph signal processing to multi-dimensional data, network consensus, and asynchronous coordination.
3. **Mathlib (Lean 4)** organizes sheaf theory via presheaves as contravariant functors `TopCatᵒᵖ ⥤ Type*` or `Cᵒᵖ ⥤ A`.

By formalizing cellular sheaves as functors into $\mathbf{Mat}(\mathbb{R})$, AlgebraX unifies DEC differential forms, sheaf cohomology, and graph neural network message passing under a single, elegant mathematical foundation.

---

## Rationale & Council Alignment

- **⚖️ Noether (Symmetries, Harmonic Invariants & Conservation)**:
  Harmonic forms and global sections ($\ker L_{\mathcal{F}} = H^0(K; \mathcal{F})$) represent conserved states across distributed topological networks. Sheaf functoriality guarantees that these conserved topological quantities are invariant under coordinate re-parameterizations.
- **🔬 Popper (Falsifiability & Cohomological Nilpotency)**:
  Cohomology is defined by the nilpotency of the coboundary operator ($\delta^2 = 0$). Popper demands executable verification ensuring $\delta^{k+1} \circ \delta^k = \mathbf{0}$ to machine precision across arbitrary simplicial and cellular complexes.
- **🧩 Russell (Taxonomy & Deductive Order)**:
  Eliminates redundant concepts. Establishes the cell complex poset category $\mathbf{Poset}(K)$, where cells are objects and face relations are morphisms, providing the exact domain category for sheaf functors.
- **⚡ Shannon (Zero Bloat & Sparse Efficiency)**:
  Sheaf restriction maps $\mathcal{E}_{v \trianglelefteq e}$ and the global coboundary $\delta$ are represented directly as sparse block matrices using AlgebraX's native `dict[tuple[...], dict[tuple[...], float]]`. No dense wrappers or dynamic graph node wrappers are created.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  Demystifies sheaves for engineers: *"A graph puts numbers on nodes and edges. A cellular sheaf puts vector spaces on nodes and edges, and gives you a translation matrix for each edge that translates node A's language into node B's language."*

---

## Specification

### 1. The Cell Poset Category (`src/algebrax/category/poset.py`)

Every regular cell complex $K$ induces a poset category $\mathbf{Poset}(K)$:
- **Objects**: Cells $\sigma \in K$ (vertices $v$, edges $e$, faces $f$).
- **Morphisms**: Inclusion relations $\sigma \trianglelefteq \tau$ indicating that $\sigma$ is a face of $\tau$.
- **Composition**: Transitivity of face relations ($\sigma \trianglelefteq \tau \trianglelefteq \rho \implies \sigma \trianglelefteq \rho$).

In accordance with [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), `CellPosetCategory` nominally subclasses `Category[Cell, FaceInclusion]`:

```python
from collections.abc import Iterable
from dataclasses import dataclass
from algebrax.category.core import Category


@dataclass(frozen=True)
class Cell:
    """A cell in a regular cell or simplicial complex."""

    dimension: int
    id: tuple[int, ...]  # e.g., (0,) for vertex 0, (0, 1) for edge (0,1)


@dataclass(frozen=True)
class FaceInclusion:
    """Morphism sigma <= tau representing face inclusion."""

    source_cell: Cell  # Face (lower dimension)
    target_cell: Cell  # Coface (higher dimension)


class CellPosetCategory(Category[Cell, FaceInclusion]):
    """Poset category Poset(K) of a regular cell complex."""

    def __init__(self, cells: Iterable[Cell], faces: Iterable[tuple[Cell, Cell]]) -> None:
        self._cells = set(cells)
        self._faces = set(faces)  # (face, coface) pairs

    def id(self, x: Cell) -> FaceInclusion:
        return FaceInclusion(x, x)

    def compose(self, f: FaceInclusion, g: FaceInclusion) -> FaceInclusion:
        if f.target_cell != g.source_cell:
            raise ValueError(f"Incompatible face composition: {f} followed by {g}")
        return FaceInclusion(f.source_cell, g.target_cell)

    def source(self, f: FaceInclusion) -> Cell:
        return f.source_cell

    def target(self, f: FaceInclusion) -> Cell:
        return f.target_cell
```

### 2. Functorial Sheaf Protocol (`src/algebrax/topology/sheaf.py`)

Following [EP-0194](EP-0194-atomic-algebraic-mixins-and-protocol-composition.md), `FunctorialSheaf` is a flat `@runtime_checkable` `Protocol` modeling a contravariant functor from $\mathbf{Poset}(K)$ to $\mathbf{Mat}(\mathbb{R})$:

```python
from typing import Any, Protocol, runtime_checkable
from algebrax.typing import SparseMatrix


@runtime_checkable
class FunctorialSheaf(Protocol):
    r"""A cellular sheaf $\mathcal{F}: \mathbf{Poset}(K)^{\text{op}} \to \mathbf{Mat}(\mathbb{R})$.

    Contravariantly maps:
    - Cell $\sigma \mapsto$ Stalk dimension $\mathbb{R}^{d_\sigma}$
    - Face inclusion $\sigma \trianglelefteq \tau \mapsto$ Restriction matrix $\mathcal{E}_{\sigma \trianglelefteq \tau} : \mathbb{R}^{d_\tau} \to \mathbb{R}^{d_\sigma}$
    """

    @property
    def poset_category(self) -> CellPosetCategory:
        """The underlying cell poset category Poset(K)."""
        ...

    def stalk_dim(self, cell: Cell) -> int:
        """Dimension of the stalk at cell sigma."""
        ...

    def restriction_map(self, face: Cell, coface: Cell) -> SparseMatrix[int, float]:
        r"""Restriction matrix $\mathcal{E}_{face \trianglelefteq coface}$."""
        ...
```

### 3. Unification of DEC and the Constant Sheaf (`src/algebrax/topology/sheaf.py`)

The standard Discrete Exterior Calculus (DEC) boundary operator $\mathbf{d}_k$ is proven to be the coboundary operator of the constant sheaf $\underline{\mathbb{R}}$. Concrete class `ConstantSheaf` nominally subclasses `FunctorialSheaf`:

```python
class ConstantSheaf(FunctorialSheaf):
    r"""The constant rank-1 sheaf $\underline{\mathbb{R}}$ over cell complex $K$.

    - Stalk at every cell is $\mathbb{R}^1$.
    - Restriction map for oriented face $\sigma \trianglelefteq \tau$ is $[+1]$ or $[-1]$
      depending on orientation compatibility.
    - Its coboundary $\delta^k$ is identically the DEC exterior derivative $\mathbf{d}_k$.
    """

    def __init__(self, complex_cells: list[Cell], orientations: dict[tuple[Cell, Cell], int]) -> None:
        self.cells = complex_cells
        self.orientations = orientations  # +1 or -1 for (face, coface)
        self._poset = CellPosetCategory(complex_cells, orientations.keys())

    @property
    def poset_category(self) -> CellPosetCategory:
        return self._poset

    def stalk_dim(self, cell: Cell) -> int:
        return 1

    def restriction_map(self, face: Cell, coface: Cell) -> SparseMatrix[int, float]:
        sign = self.orientations.get((face, coface), 1)
        return {0: {0: float(sign)}}
```

### 4. Coboundary Natural Transformation & Sheaf Laplacian (`src/algebrax/topology/sheaf.py`)

The global degree-$k$ cochain space is the direct sum of stalks:
$$C^k(K; \mathcal{F}) = \bigoplus_{\dim \sigma = k} \mathcal{F}(\sigma)$$

The coboundary operator $\delta^k: C^k(K; \mathcal{F}) \to C^{k+1}(K; \mathcal{F})$ is a block sparse matrix:
$$\delta^k(x)(\tau) = \sum_{\sigma \trianglelefteq \tau} [\sigma : \tau] \mathcal{E}_{\sigma \trianglelefteq \tau} x(\sigma)$$

```python
from algebrax.matrix import add, dot, transpose
from algebrax.semiring import StandardSemiring


def build_sheaf_coboundary_matrix(sheaf: FunctorialSheaf, k: int) -> SparseMatrix[Any, float]:
    r"""Assemble the sparse block coboundary matrix $\delta^k: C^k \to C^{k+1}$."""
    matrix: SparseMatrix[Any, float] = {}
    ...
    return matrix


def build_sheaf_laplacian(sheaf: FunctorialSheaf, k: int = 0) -> SparseMatrix[Any, float]:
    r"""Assemble the k-th Sheaf Laplacian $L_k = \delta_k^* \delta_k + \delta_{k-1} \delta_{k-1}^*$.

    For degree 0 (vertex signals), $L_0 = \delta_0^T \delta_0$.
    """
    delta_k = build_sheaf_coboundary_matrix(sheaf, k)
    delta_k_t = transpose(delta_k)
    semiring = StandardSemiring(float)

    l_up = dot(delta_k_t, delta_k, semiring=semiring)
    if k == 0:
        return l_up

    delta_prev = build_sheaf_coboundary_matrix(sheaf, k - 1)
    delta_prev_t = transpose(delta_prev)
    l_down = dot(delta_prev, delta_prev_t, semiring=semiring)

    return add(l_up, l_down, semiring=semiring)
```

### 5. Verification Invariants (`src/algebrax/verification.py`)

```python
def verify_sheaf_functoriality(sheaf: FunctorialSheaf, sample_paths: list[tuple[Cell, Cell, Cell]]) -> bool:
    r"""Verify functoriality of restriction maps:
    $$\mathcal{E}_{\sigma \trianglelefteq \rho} = \mathcal{E}_{\sigma \trianglelefteq \tau} \circ \mathcal{E}_{\tau \trianglelefteq \rho}$$
    """
    semiring = StandardSemiring(float)
    for sigma, tau, rho in sample_paths:
        r_sigma_tau = sheaf.restriction_map(sigma, tau)
        r_tau_rho = sheaf.restriction_map(tau, rho)
        r_sigma_rho = sheaf.restriction_map(sigma, rho)

        composed = dot(r_sigma_tau, r_tau_rho, semiring=semiring)
        if composed != r_sigma_rho:
            return False
    return True


def verify_coboundary_nilpotency(sheaf: FunctorialSheaf, k: int) -> bool:
    r"""Verify the fundamental cohomological invariant $\delta^{k+1} \circ \delta^k = \mathbf{0}$."""
    semiring = StandardSemiring(float)
    delta_k = build_sheaf_coboundary_matrix(sheaf, k)
    delta_k1 = build_sheaf_coboundary_matrix(sheaf, k + 1)
    delta2 = dot(delta_k1, delta_k, semiring=semiring)
    return not delta2 or all(abs(val) < 1e-12 for row in delta2.values() for val in row.values())
```

---

## Backwards Compatibility

1. **Non-Breaking Extension**:
   `CellularSheaf` in `algebrax.topology` is updated to nominally subclass `FunctorialSheaf` while retaining its existing helper methods.
2. **Interoperability with DEC**:
   Existing discrete differential form workflows in `algebrax.analysis` remain unchanged; `ConstantSheaf` provides an explicit bidirectional bridge.

---

## How to Teach This / Documentation Plan

1. **Architecture Essay**:
   Author an architectural essay linking Sheaf Theory, DEC, and Category Theory (*"From Triangles to Cohomology: The Functorial Bridge"*).
2. **Applied Guide (`docs/guides/cellular-sheaves-and-dec.md`)**:
   Showcase practical applications:
   - Opinion consensus on graphs with biased communication channels.
   - Distributed camera synchronization in robotics (SE(2) / SE(3) sheaf stalks).
   - Solving Poisson's equation on curved simplicial surfaces via DEC and constant sheaf Laplacians.

---

## Reference Implementation

A reference implementation of `CellPosetCategory`, `ConstantSheaf`, and the block Sheaf Laplacian was evaluated in Council exploration `references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Continuous Sheafification with Topological Spaces and Open Sets**:
   *Rejected*: AlgebraX operates strictly on discrete, finite computational structures. Continuous topological spaces with open covers ($X, \mathcal{U}$) belong in symbolic theorem provers, not sparse computational linear algebra frameworks.
2. **Boxing Cochains in Heavy Object Wrappers**:
   *Rejected*: Cochains $C^k(K; \mathcal{F})$ are represented as flat dictionary vectors `dict[tuple[Cell, int], float]`, ensuring direct compatibility with high-performance linear solvers (`scipy.sparse` / native sparse operations).

---

## Open Questions

1. **Cosheaves & Homology**:
   Should we formalize cellular *cosheaves* (covariant functors preserving boundary maps $\partial_k$) as a distinct protocol, or rely on linear duality ($C_k \cong C^k$)?
   *Recommendation*: Rely on linear duality via matrix transposition $\delta^* = \partial$ for discrete complexes over fields.

---

## Change Log

- **2026-10-27**: Initial draft authored following Council consensus on EXP-0005.
