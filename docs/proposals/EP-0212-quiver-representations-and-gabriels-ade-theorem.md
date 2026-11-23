---
title: "EP-0212: Quiver Representations, Path Algebras & Gabriel's ADE Theorem"
description: "Formalize quiver representations on directed graphs, path algebras, indecomposable representations, the Tits quadratic form, and Gabriel's ADE classification theorem."
icon: lucide/git-fork
status: final
---

# EP-0212: Quiver Representations, Path Algebras & Gabriel's ADE Theorem

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0212                                                                              |
| **Title**         | Quiver Representations, Path Algebras & Gabriel's ADE Theorem                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | 🧩 Russell (Taxonomy & Sheaf Equivalence) & 🔬 Popper (Tits Form Falsifiability)  |
| **Status**        | Final                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-11-23                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational foundations of **Quiver Representations and Path Algebras** in AlgebraX, connecting graph theory, cellular sheaves, and simple Lie algebras. EP-0212 introduces:

1. **Quiver Representation Protocol (`algebrax.rep.quiver`)**:
   A quiver $Q = (V_Q, E_Q)$ is a directed multigraph. A representation $M$ assigns:
   - A vector space $V_i = K^{d_i}$ to each vertex $i \in V_Q$.
   - A sparse linear map $M_\alpha : V_{\operatorname{source}(\alpha)} \to V_{\operatorname{target}(\alpha)}$ to each directed edge $\alpha \in E_Q$.
2. **Unified Sheaf-Quiver Equivalence (`algebrax.topology.sheaf`)**:
   Formalizing the structural identity (`to_cellular_sheaf` / `from_cellular_sheaf`): a Quiver Representation is mathematically identical to a **Cellular Sheaf ([EP-0202](EP-0202-functorial-sheaves-and-categorical-dec.md))** on a 1-dimensional cell complex where restriction maps follow edge orientations.
3. **Path Algebra Constructor (`algebrax.algebra._path_algebra`)**:
   Associative algebra $K Q$ spanned by directed paths in $Q$, with multiplication defined by path concatenation ($p \cdot q = pq$ if $\operatorname{target}(p) = \operatorname{source}(q)$, else $0$), exported cleanly via `algebrax.algebra`.
4. **The Tits Quadratic Form & Gabriel's ADE Theorem (`algebrax.rep.quiver`)**:
   Evaluating the Euler–Tits form for dimension vector $\mathbf{d} = (d_1, \dots, d_n)$:
   $$q_Q(\mathbf{d}) = \sum_{i \in V_Q} d_i^2 - \sum_{\alpha \in E_Q} d_{\operatorname{source}(\alpha)} d_{\operatorname{target}(\alpha)}$$
   Implementing Pierre Gabriel's landmark theorem (1972): a quiver has **finite representation type** if and only if its underlying undirected graph is a simply-laced Dynkin diagram ($A_n, D_n, E_6, E_7, E_8$), with indecomposables in exact 1-to-1 bijection with the positive roots $\Phi^+$ from [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md).
5. **Property-Based Verification (`algebrax.verification`)**:
   Verification of quiver morphism commutativity ($f_v \circ M_\alpha = N_\alpha \circ f_u$), direct sum decomposition, and positive definiteness of the Tits form on ADE graphs in `src/algebrax/verification.py`.

---

## Motivation

Quivers provide the modern categorical language for linear algebra problems involving multiple vector spaces and interrelated maps (e.g., matrix pencils, subspace arrangements, persistence modules).

1. **Unifying Graphs, Matrices, and Sheaves**: A matrix is a representation of the 2-vertex quiver $\bullet \to \bullet$. A persistence module in TDA ([`EP-0162`](EP-0162-persistent-homology-and-topological-barcodes.md)) is a representation of the $A_n$ quiver $\bullet \to \bullet \to \cdots \to \bullet$. Cellular sheaves ([`EP-0161`](EP-0161-cellular-sheaves-and-network-laplacians.md), [`EP-0202`](EP-0202-functorial-sheaves-and-categorical-dec.md)) generalize quivers to higher-dimensional cell complexes.
2. **Gabriel's Theorem as a Deep Bridge**: Gabriel's theorem establishes an unexpected, breathtaking bridge between graph representations and Lie algebras: classifying indecomposable modules on directed graphs yields the exact same Dynkin classification ($A_n, D_n, E_6, E_7, E_8$) as simple Lie algebras.
3. **Automated Indecomposable Decomposition**: In data analysis and control theory, decomposing a network of linear maps into indecomposable blocks simplifies high-dimensional dynamical systems.

---

## Rationale & Council Alignment

- **🧩 Russell (Taxonomy & Sheaf-Quiver Identity)**:
  Recognizes that a quiver representation is an instance of a functor $\mathcal{F}: \mathbf{Path}(Q) \to \mathbf{Vect}_K$. Unifies quiver representations with AlgebraX's existing `CellularSheaf` engine (`algebrax.topology.sheaf`), avoiding duplicative class hierarchies.
- **🔬 Popper (Falsifiability & Tits Form Definiteness)**:
  Gabriel's condition is strictly falsifiable: $q_Q(\mathbf{d}) > 0$ for all non-zero $\mathbf{d}$ if and only if $Q$ is ADE. If the graph contains a cycle or bad branching, $q_Q(\mathbf{d}) \le 0$ immediately detects infinite/wild representation type.
- **⚡ Shannon (Zero Bloat & Sparse Dictionary Carrier)**:
  Edge maps are bare `SparseMatrix` dictionaries and path basis elements are tuples of edges `(e1, e2, ...)`.
- **⚖️ Noether (Structural Symmetries)**:
  The isomorphism classes of indecomposables mirror the root orbits under the Weyl group (`algebrax.lie.RootSystem`).
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"A quiver is just an arrow diagram where each dot gets a vector space and each arrow gets a matrix. Gabriel found that only very special diagrams don't blow up into infinitely many uncontrollable matrix patterns."*

---

## Specification

### 1. Quiver, Tits Form & Gabriel Classifier (`src/algebrax/rep/quiver.py`)

```python
"""Quiver representations, Tits quadratic form, Gabriel's ADE theorem, and CellularSheaf adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Hashable, Sequence, TypeVar

from algebrax.typing import SparseMatrix

K = TypeVar("K")                   # Scalar field
V = TypeVar("V", bound=Hashable)  # Vertex type
E = TypeVar("E", bound=Hashable)  # Edge type


@dataclass(frozen=True)
class Quiver(Generic[V, E]):
    """A directed multigraph quiver Q = (V, E, source, target)."""

    vertices: Sequence[V]
    edges: Sequence[E]
    source: dict[E, V]
    target: dict[E, V]


@dataclass(frozen=True)
class QuiverRepresentation(Generic[K, V, E]):
    """A representation of quiver Q over field K."""

    quiver: Quiver[V, E]
    dimensions: dict[V, int]                 # dim(V_i)
    edge_maps: dict[E, SparseMatrix[int, K]] # M_alpha: V_{s(alpha)} -> V_{t(alpha)}

    @property
    def dimension_vector(self) -> tuple[int, ...]:
        """Return dimension vector (d_1, ..., d_n)."""
        return tuple(self.dimensions[v] for v in self.quiver.vertices)


def tits_quadratic_form(quiver: Quiver[V, E], dim_vec: dict[V, int]) -> int:
    """Evaluate Euler-Tits form q_Q(d) = sum d_i^2 - sum_{(u,v)} d_u d_v."""
    ...


def classify_representation_type(quiver: Quiver[V, E]) -> str:
    """Classify quiver representation type using Gabriel's criteria ('finite', 'tame', or 'wild')."""
    ...
```

### 2. Path Algebra Constructor (`src/algebrax/algebra/_path_algebra.py`)

```python
"""Path algebras KQ of quivers (re-exported from algebrax.algebra)."""

from algebrax.algebra._monoid_algebra import QuotientMonoidAlgebra


def path_algebra(quiver: Quiver[V, E]) -> QuotientMonoidAlgebra[tuple[E, ...], K]:
    """Construct associative path algebra K Q where elements are linear combinations of paths."""
    ...
```

### 3. Verification Suite (`src/algebrax/verification.py`)

```python
"""Property-based verification for quiver representations and Gabriel's theorem."""

def verify_quiver_morphism_commutation(
    rep1: QuiverRepresentation[K, V, E],
    rep2: QuiverRepresentation[K, V, E],
    morphism_maps: dict[V, SparseMatrix[int, K]],
    tol: float = 1e-9,
) -> dict[str, bool]:
    """Verify f_{t(e)} @ M_e == N_e @ f_{s(e)} for all edges e."""
    ...

def verify_tits_positive_definiteness(quiver: Quiver[V, E]) -> dict[str, bool]:
    """Verify q_Q(d) > 0 for all non-zero dimension vectors on ADE quivers."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Quiver representations reside in `algebrax.rep.quiver` and integrate seamlessly with `CellularSheaf` in `algebrax.topology.sheaf` ([`EP-0202`](EP-0202-functorial-sheaves-and-categorical-dec.md)) and `RootSystem` in `algebrax.lie` ([`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md)).

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/quivers_and_gabriel.md`:
  - Visualizing quivers and matrix assignments.
  - The Kronecker quiver $\bullet \rightrightarrows \bullet$ and matrix pencil canonical forms.
  - Verifying Gabriel's ADE theorem via root systems.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for the Tits form and path concatenation.

---

## Reference Implementation

Implemented across:

- **`src/algebrax/rep/quiver.py`** (re-exported in `src/algebrax/rep/__init__.py`):
  `Quiver`, `QuiverRepresentation`, `direct_sum_quiver_rep`, `simple_representation`, `interval_representation`, `euler_form`, `tits_quadratic_form`, `bgp_reflect_dimension`, `classify_dynkin_type`, `classify_representation_type`, `gabriel_positive_roots`, `dynkin_quiver`, `kronecker_quiver`, `cycle_quiver`, `to_cellular_sheaf`, and `from_cellular_sheaf`.
- **`src/algebrax/algebra/_path_algebra.py`** (re-exported in `src/algebrax/algebra/__init__.py`):
  `PathAlgebra` (subclassing `QuotientMonoidAlgebra` with unboxed `(start_vertex, (e_1, ..., e_k))` keys, primitive orthogonal idempotents summing to $\mathbf{1}_{KQ}$, optional `max_path_length` truncation, and `evaluate_in_rep`) and `path_algebra`.
- **`src/algebrax/verification.py`**:
  `verify_quiver_morphism_commutation`, `verify_quiver_direct_sum`, and `verify_tits_positive_definiteness`.
- **Verification & Documentation**:
  `tests/algebrax/test_rep_quiver.py`, `tests/verifications/test_differential_sympy.py` (`test_differential_quiver_tits_form_and_gabriel_ade_vs_sympy`), `docs/verification.md`, and `docs/guide/algebra/quivers_and_gabriel.md`.

---

## Rejected Ideas

1. **Duplicating Sheaf Logic with a Separate `QuiverSheaf` Class**:
   - *Rejected*: A quiver representation on a directed graph is mathematically identical to a 1-dimensional cellular sheaf. Duplicating coboundary operators or restriction logic violates the zero-bloat principle.
2. **Dense Adjacency Tensors for Paths**:
   - *Rejected*: Paths can have arbitrary length; using dense matrices for path multiplication causes explosive memory usage. Paths are represented as unboxed `(start_vertex, (e_1, ..., e_k))` tuples of edge identifiers.

---

## Open Questions

- [x] Dimension-level Bernstein–Gelfand–Ponomarev (BGP) / Weyl reflection operator (`bgp_reflect_dimension`) preserving $q_Q(\mathbf{d})$. Full functorial Auslander–Reiten quiver translation ($\tau, \tau^-$) on matrix representations remains a potential future extension.
- [x] Classification and exact nullspace radical detection for all tame extended Euclidean diagrams ($\widetilde{A}_n, \widetilde{D}_n, \widetilde{E}_6, \widetilde{E}_7, \widetilde{E}_8$). Explicit Kronecker pencil canonical form (Weierstrass–Kronecker normal form) remains a potential future extension.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
* **2026-11-15:**
  * Consolidated module layout into `src/algebrax/rep/quiver.py`, `src/algebrax/algebra/_path_algebra.py`, and `src/algebrax/verification.py`; aligned cellular sheaf interoperability with `algebrax.topology.sheaf.CellularSheaf`.
* **2026-11-23:**
  * Implemented `algebrax.rep.quiver`, `algebrax.algebra.PathAlgebra` / `path_algebra`, quiver verifiers in `algebrax.verification`, SymPy differential oracle, unit/falsification tests, and user guide `docs/guide/algebra/quivers_and_gabriel.md`; transitioned status to **Final** (completing Phase 8).
