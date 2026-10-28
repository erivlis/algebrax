---
title: "EP-0212: Quiver Representations, Path Algebras & Gabriel's ADE Theorem"
description: "Formalize quiver representations on directed graphs, path algebras, indecomposable representations, the Tits quadratic form, and Gabriel's ADE classification theorem."
icon: lucide/git-fork
status: draft
---

# EP-0212: Quiver Representations, Path Algebras & Gabriel's ADE Theorem

| Field             | Value                                                                             |
|:------------------|:----------------------------------------------------------------------------------|
| **EP**            | 0212                                                                              |
| **Title**         | Quiver Representations, Path Algebras & Gabriel's ADE Theorem                     |
| **Author**        | Eran Rivlis <eran@rivlis.info>, Antigravity                                       |
| **Sponsor**       | Core Maintainers                                                                  |
| **Delegate**      | 🧩 Russell (Taxonomy & Sheaf Equivalence) & 🔬 Popper (Tits Form Falsifiability)  |
| **Status**        | Draft                                                                             |
| **Type**          | Standards Track                                                                   |
| **Created**       | 2026-10-28                                                                        |
| **Updated**       | 2026-10-28                                                                        |
| **Replaces**      | —                                                                                 |
| **Superseded-By** | —                                                                                 |

---

## Abstract

This proposal establishes the computational foundations of **Quiver Representations and Path Algebras** in AlgebraX, connecting graph theory, cellular sheaves, and simple Lie algebras. EP-0212 introduces:

1. **Quiver Representation Protocol (`algebrax.rep.quiver`)**:
   A quiver $Q = (V_Q, E_Q)$ is a directed multigraph. A representation $M$ assigns:
   - A vector space $V_i = K^{d_i}$ to each vertex $i \in V_Q$.
   - A sparse linear map $M_\alpha : V_{\operatorname{source}(\alpha)} \to V_{\operatorname{target}(\alpha)}$ to each directed edge $\alpha \in E_Q$.
2. **Unified Sheaf-Quiver Equivalence**:
   Formalizing the structural identity: a Quiver Representation is mathematically identical to a **Cellular Sheaf ([EP-0202](EP-0202-functorial-sheaves-and-categorical-dec.md))** on a 1-dimensional cell complex where restriction maps follow edge orientations.
3. **Path Algebra Constructor (`algebrax.algebra.path_algebra`)**:
   Associative algebra $K Q$ spanned by directed paths in $Q$, with multiplication defined by path concatenation ($p \cdot q = pq$ if $\operatorname{target}(p) = \operatorname{source}(q)$, else $0$).
4. **The Tits Quadratic Form & Gabriel's ADE Theorem**:
   Evaluating the Euler-Tits form for dimension vector $\mathbf{d} = (d_1, \dots, d_n)$:
   $$q_Q(\mathbf{d}) = \sum_{i \in V_Q} d_i^2 - \sum_{\alpha \in E_Q} d_{\operatorname{source}(\alpha)} d_{\operatorname{target}(\alpha)}$$
   Implementing Pierre Gabriel's landmark theorem (1972): a quiver has **finite representation type** if and only if its underlying undirected graph is a simply-laced Dynkin diagram ($A_n, D_n, E_6, E_7, E_8$), with indecomposables in exact 1-to-1 bijection with the positive roots $\Phi^+$ from [`EP-0164`](EP-0164-root-systems-and-chevalley-bases.md).
5. **Property-Based Verification (`algebrax.verification.quiver`)**:
   Verification of quiver morphism commutativity ($f_v \circ M_\alpha = N_\alpha \circ f_u$), direct sum decomposition, and positive definiteness of the Tits form on ADE graphs.

---

## Motivation

Quivers provide the modern categorical language for linear algebra problems involving multiple vector spaces and interrelated maps (e.g., matrix pencils, subspace arrangements, persistence modules).

1. **Unifying Graphs, Matrices, and Sheaves**: A matrix is a representation of the 2-vertex quiver $\bullet \to \bullet$. A persistence module in TDA ([`EP-0162`](EP-0162-persistent-homology-and-topological-data-analysis.md)) is a representation of the $A_n$ quiver $\bullet \to \bullet \to \cdots \to \bullet$. Cellular sheaves ([`EP-0161`](EP-0161-cellular-sheaves-and-laplacians.md), [`EP-0202`](EP-0202-functorial-sheaves-and-categorical-dec.md)) generalize quivers to higher-dimensional cell complexes.
2. **Gabriel's Theorem as a Deep Bridge**: Gabriel's theorem establishes an unexpected, breathtaking bridge between graph representations and Lie algebras: classifying indecomposable modules on directed graphs yields the exact same Dynkin classification ($A_n, D_n, E_6, E_7, E_8$) as simple Lie algebras.
3. **Automated Indecomposable Decomposition**: In data analysis and control theory, decomposing a network of linear maps into indecomposable blocks simplifies high-dimensional dynamical systems.

---

## Rationale & Council Alignment

- **🧩 Russell (Taxonomy & Sheaf-Quiver Identity)**:
  Recognizes that a quiver representation is an instance of a functor $\mathcal{F}: \mathbf{Path}(Q) \to \mathbf{Vect}_K$. Unifies quiver representations with AlgebraX's existing `CellularSheaf` engine, avoiding duplicative class hierarchies.
- **🔬 Popper (Falsifiability & Tits Form Definiteness)**:
  Gabriel's condition is strictly falsifiable: $q_Q(\mathbf{d}) > 0$ for all non-zero $\mathbf{d}$ if and only if $Q$ is ADE. If the graph contains a cycle or bad branching, $q_Q(\mathbf{d}) \le 0$ immediately detects infinite/wild representation type.
- **⚡ Shannon (Zero Bloat & Sparse Dictionary Carrier)**:
  A quiver representation is represented without wrappers:
  ```python
  QuiverRep = tuple[dict[Vertex, int], dict[Edge, SparseMatrix]]
  ```
  Path algebras represent basis elements as tuples of edges `(e1, e2, ...)`.
- **⚖️ Noether (Structural Symmetries)**:
  The isomorphism classes of indecomposables mirror the root orbits under the Weyl group.
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  *"A quiver is just an arrow diagram where each dot gets a vector space and each arrow gets a matrix. Gabriel found that only very special diagrams don't blow up into infinitely many uncontrollable matrix patterns."*

---

## Specification

### 1. Quiver & Representation Data Structures (`src/algebrax/rep/quiver.py`)

```python
"""Quiver representations and morphisms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Hashable, Sequence, TypeVar

from algebrax.matrix import SparseMatrix

V = TypeVar("V", bound=Hashable)  # Vertex type
E = TypeVar("E", bound=Hashable)  # Edge type
K = TypeVar("K")                   # Scalar field


@dataclass(frozen=True)
class Quiver(Generic[V, E]):
    """A directed multigraph quiver Q = (V, E, source, target)."""

    vertices: Sequence[V]
    edges: Sequence[E]
    source: dict[E, V]
    target: dict[E, V]


@dataclass(frozen=True)
class QuiverRepresentation(Generic[V, E, K]):
    """A representation of quiver Q over field K."""

    quiver: Quiver[V, E]
    dimensions: dict[V, int]              # dim(V_i)
    edge_maps: dict[E, SparseMatrix[K]]    # M_alpha: V_{s(alpha)} -> V_{t(alpha)}

    @property
    def dimension_vector(self) -> tuple[int, ...]:
        """Return dimension vector (d_1, ..., d_n)."""
        return tuple(self.dimensions[v] for v in self.quiver.vertices)
```

### 2. The Tits Quadratic Form & Gabriel Classifier (`src/algebrax/rep/gabriel.py`)

```python
"""Tits quadratic form and Gabriel's ADE representation type classifier."""

from algebrax.rep.quiver import Quiver


def tits_quadratic_form(quiver: Quiver[V, E], dim_vec: dict[V, int]) -> int:
    """Evaluate Euler-Tits form q_Q(d) = sum d_i^2 - sum_{(u,v)} d_u d_v."""
    vertex_sum = sum(d * d for d in dim_vec.values())
    edge_sum = sum(
        dim_vec[quiver.source[e]] * dim_vec[quiver.target[e]]
        for e in quiver.edges
    )
    return vertex_sum - edge_sum


def classify_representation_type(quiver: Quiver[V, E]) -> str:
    """Classify quiver representation type using Gabriel's criteria.
    
    Returns 'finite' (ADE), 'tame' (affine ADE), or 'wild'.
    """
    ...
```

### 3. Path Algebra Constructor (`src/algebrax/algebra/path_algebra.py`)

```python
"""Path algebras KQ of quivers."""

from typing import Tuple
from algebrax.algebra.monoid_algebra import QuotientMonoidAlgebraSemiring


def path_algebra(quiver: Quiver[V, E]) -> QuotientMonoidAlgebraSemiring:
    """Construct associative path algebra K Q where elements are linear combinations of paths."""
    ...
```

### 4. Verification Suite (`src/algebrax/verification/quiver.py`)

```python
"""Property-based verification for quiver representations and Gabriel's theorem."""

def verify_quiver_morphism_commutation(
    rep1: QuiverRepresentation[V, E, K],
    rep2: QuiverRepresentation[V, E, K],
    morphism_maps: dict[V, SparseMatrix[K]],
) -> bool:
    """Verify f_{t(e)} @ M_e == N_e @ f_{s(e)} for all edges e."""
    ...

def verify_tits_positive_definiteness(quiver: Quiver[V, E]) -> bool:
    """Verify q_Q(d) > 0 for all non-zero dimension vectors on ADE quivers."""
    ...
```

---

## Backwards Compatibility

Non-breaking and strictly additive. Quiver representations reside in `algebrax.rep.quiver` and integrate seamlessly with `CellularSheaf` in `algebrax.sheaf` ([`EP-0202`](EP-0202-functorial-sheaves-and-categorical-dec.md)).

---

## How to Teach This / Documentation Plan

- **Guide**: `guide/algebra/quivers_and_gabriel.md`:
  - Visualizing quivers and matrix assignments.
  - The Kronecker quiver $\bullet \rightrightarrows \bullet$ and matrix pencil canonical forms.
  - Verifying Gabriel's ADE theorem via root systems.
- **Docstrings**: Fully typed AMDS docstrings with KaTeX equations for the Tits form and path concatenation.

---

## Reference Implementation

Prototype implementations will reside in `src/algebrax/rep/quiver.py` and `src/algebrax/rep/gabriel.py`.

---

## Rejected Ideas

1. **Duplicating Sheaf Logic with a Separate `QuiverSheaf` Class**:
   - *Rejected*: A quiver representation on a directed graph is mathematically identical to a cellular sheaf. Duplicating coboundary operators or restriction logic violates the zero-bloat principle.
2. **Dense Adjacency Tensors for Paths**:
   - *Rejected*: Paths can have arbitrary length; using dense matrices for path multiplication causes explosive memory usage. Paths are represented as tuple sequences of edge identifiers.

---

## Open Questions

- [ ] Auslander–Reiten theory and reflection functors (Bernstein–Gelfand–Ponomarev) for explicit construction of all indecomposables from simple roots.
- [ ] Support for tame quivers with continuous 1-parameter families of representations.

---

## Change Log

* **2026-10-28:**
  * Initial Draft authored for Phase 8.
