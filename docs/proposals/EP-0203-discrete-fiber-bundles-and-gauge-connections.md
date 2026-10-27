---
title: "EP-0203: Discrete Fiber Bundles, Gauge Connections & Parallel Transport"
description: "Formalize discrete vector bundles, principal G-bundles, gauge connections, holonomy, and connection Laplacians on cell complexes, bridging Lie groups, cellular sheaves, and discrete exterior calculus."
icon: lucide/cable
status: draft
---

# EP-0203: Discrete Fiber Bundles, Gauge Connections & Parallel Transport

| Field        | Value                                                              |
|:-------------|:-------------------------------------------------------------------|
| **EP**       | 0203                                                               |
| **Title**    | Discrete Fiber Bundles, Gauge Connections & Parallel Transport     |
| **Author**   | Eran Rivlis <eran@rivlis.info>, Antigravity                        |
| **Sponsor**  | Core Maintainers                                                   |
| **Delegate** | ⚖️ Noether (Gauge Invariants & Curvature) & ⚡ Shannon (Sparse Block Mechanics) |
| **Status**   | Draft                                                              |
| **Type**     | Standards Track                                                    |
| **Created**  | 2026-10-27                                                         |
| **Updated**  | 2026-10-27                                                         |
| **Replaces** | —                                                                  |
| **Superseded-By** | —                                                             |

---

## Abstract

This proposal introduces **Discrete Fiber Bundles, Gauge Connections, and Connection Laplacians** into AlgebraX, establishing the mathematical bridge connecting Lie groups (`algebrax.lie`), cellular sheaves (`algebrax.sheaf`), and Discrete Exterior Calculus (`algebrax.dec`). Specifically, EP-0203 formalizes:
1. **Discrete Vector and Principal $G$-Bundles**: Bundles over regular cell complexes $K$ assigning fibers (vector spaces $\mathbb{R}^d$ or Lie groups $G$) to vertices and connection elements $\rho(u, v) \in G \subseteq \mathrm{GL}(d)$ to 1-cells.
2. **Parallel Transport & Holonomy**: Exact composition along 1-chains $\gamma$, and Wilson loop / discrete curvature evaluation around 2-faces ($\operatorname{Hol}(f) = \prod_{e \in \partial f} \rho(e)$).
3. **The Connection Laplacian ($L_\nabla$)**: High-performance sparse block operator $L_\nabla = D \otimes \mathbf{I}_d - \mathbf{A}_\rho$, enabling angular synchronization, robotics pose-graph optimization, and cryo-EM orientation estimation.
4. **Bundle-Valued DEC Forms**: Extension of DEC differential forms to $\Omega^k(K; E)$ with covariant exterior derivative $d_\nabla$ satisfying $d_\nabla^2 = F$ (the discrete curvature 2-form), recovering twisted de Rham cohomology when $F = \mathbf{0}$.
5. **Axiomatic Gauge Verification**: Executable property tests in `algebrax.verification`: gauge covariance ($A'_{uv} = g_u A_{uv} g_v^{-1}$), discrete Bianchi identity ($d_\nabla F = \mathbf{0}$), and flat-bundle holonomy triviality ($\operatorname{Hol}(f) = \mathbf{I}$).

All connection matrices, bundle-valued forms, and Laplacians strictly preserve AlgebraX's unboxed sparse dictionary representation (`dict[tuple[...], dict[tuple[...], float]]`), ensuring zero heap boxing overhead.

---

## Motivation

AlgebraX contains three powerful but historically disconnected components:
- **`algebrax.dec` ([EP-0160](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md))**: Scalar differential forms $\Omega^k(K; \mathbb{R})$, exterior derivative $d$, and Hodge Laplacian $\Delta$.
- **`algebrax.lie` ([EP-0163](EP-0163-lie-algebras-and-bch-dynamics.md))**: Continuous matrix Lie groups and algebras ($\mathfrak{so}(3)$, $\mathfrak{se}(3)$, $\mathfrak{sl}(2)$).
- **`algebrax.sheaf` ([EP-0202](EP-0202-functorial-sheaves-and-categorical-dec.md))**: Cellular sheaves with general stalk assignments and linear restriction maps.

In modern applied geometry, computer vision, robotics, and mathematical physics, these domains converge in the language of **Fiber Bundles and Gauge Theory**:
1. **Cellular Sheaves vs. Vector Bundles**: In applied algebraic topology (Justin Curry 2014, Robert Ghrist 2014), a cellular sheaf where all stalks have identical dimension $d$ and all restriction maps are **orthogonal isomorphisms** is precisely a **flat discrete orthogonal vector bundle** (a *local system*). General cellular sheaves allow rank-collapsing maps; fiber bundles enforce strict gauge symmetries across fibers.
2. **Angular & Pose Synchronization**: In cryo-EM molecule reconstruction (Amit Singer 2011), robotics graph-SLAM, and Structure from Motion (SfM), sensors measure noisy relative transformations $\rho_{uv} \in SO(3)$ or $SE(3)$ along edges. Reconstructing the global coordinate frames is formulated as spectral relaxation of the **Connection Laplacian** $L_\nabla$.
3. **Discrete Gauge Theory & Physics**: In lattice Yang-Mills theory and modern discrete differential geometry (Keenan Crane 2013, Mathieu Desbrun 2005), gauge fields are 1-forms taking values in a Lie algebra, parallel transport integrates these fields along edges, and the curvature 2-form $F = d A + \frac{1}{2}[A, A]$ represents the field strength (electromagnetism, gravity).

Without discrete fiber bundles, users must manually hand-roll block matrices to compute parallel transport, solve synchronization problems, or analyze vector-valued differential forms.

---

## Rationale & Council Alignment

- **⚖️ Noether (Gauge Symmetries, Conserved Currents & Curvature)**:
  Gauge invariance is the ultimate expression of Noether's symmetry principles: physical and geometric observables must remain invariant under local gauge transformations $g_u \in G$. Curvature $F$ and Chern classes measure topological obstructions to global triviality.
- **⚡ Shannon (Zero Bloat & Unboxed Block Sparsity)**:
  Rejects heavy object-oriented abstractions such as `class FiberBundle` or `class LocalChart`. A discrete connection is stored simply as a sparse block dictionary mapping edge keys to $(d \times d)$ orthogonal transformation matrices. Parallel transport is sparse matrix multiplication.
- **🔬 Popper (Falsifiability & Geometric Invariants)**:
  Establishes strict numerical invariants:
  1. **Connection Inversion**: $\rho(v, u) = \rho(u, v)^{-1} = \rho(u, v)^T$ for orthogonal groups.
  2. **Discrete Bianchi Identity**: $d_\nabla F = \mathbf{0}$.
  3. **Gauge Covariance**: $L_{\nabla'} = \mathbf{G} L_\nabla \mathbf{G}^T$ under vertex gauge transformations.
- **🧩 Russell (Taxonomy & Deductive Order)**:
  Clarifies the categorical hierarchy:
  $$\text{Scalar DEC} \subset \text{Discrete Vector Bundles (Isomorphic Stalks)} \subset \text{Cellular Sheaves (General Stalks)}$$
- **💡 Feynman (Freshman Test & Intuitive Demystification)**:
  Demystifies fiber bundles: *"Imagine each vertex on a mesh has its own coordinate frame. When you walk from vertex A to vertex B, the edge tells you how to rotate your compass. If you walk around a triangle and your compass doesn't point the same way you started, that angle difference is the curvature of the space."*

---

## Specification

### 1. The Discrete Connection Protocol (`src/algebrax/topology/bundle.py`)

A discrete connection assigns parallel transport maps in group $G \subseteq \mathrm{GL}(d)$ to oriented 1-cells (edges):

```python
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable
from collections.abc import Iterable, Sequence

G = TypeVar("G")
SparseBlockMatrix = dict[Any, dict[Any, dict[int, dict[int, float]]]]


@runtime_checkable
class DiscreteConnection(Protocol[G]):
    r"""A discrete connection (gauge field) on a 1-skeleton $K_1$.

    Assigns to each oriented edge $(u, v)$ a transport operator $\rho(u, v) \in G$
    satisfying $\rho(v, u) = \rho(u, v)^{-1}$.
    """

    @property
    def fiber_dim(self) -> int:
        """Dimension d of the fiber vector space R^d."""
        ...

    def transport(self, u: Any, v: Any) -> dict[int, dict[int, float]]:
        r"""Parallel transport matrix $\rho(u, v) : F_u \to F_v$."""
        ...

    def transport_path(self, path: Sequence[Any]) -> dict[int, dict[int, float]]:
        r"""Compute parallel transport along a path $(v_0, v_1, \dots, v_k)$:
        $$\rho(\gamma) = \rho(v_{k-1}, v_k) \cdots \rho(v_0, v_1)$$
        """
        ...
```

### 2. Concrete Orthogonal Connection (`src/algebrax/topology/bundle.py`)

```python
from algebrax.linalg.sparse import dot, transpose
from algebrax.structures.semiring import RealRing


class DiscreteOrthogonalConnection:
    r"""Discrete vector bundle connection with structure group $O(d)$ or $SO(d)$.

    Enforces exact orthogonality: $\rho(u, v)^{-1} = \rho(u, v)^T = \rho(v, u)$.
    """

    def __init__(self, fiber_dim: int) -> None:
        self.fiber_dim = fiber_dim
        self._edges: dict[tuple[Any, Any], dict[int, dict[int, float]]] = {}
        self._ring = RealRing()

    def set_transport(self, u: Any, v: Any, matrix: dict[int, dict[int, float]]) -> None:
        """Set parallel transport rho(u, v) and automatically bind rho(v, u) = rho(u, v)^T."""
        self._edges[(u, v)] = matrix
        self._edges[(v, u)] = transpose(matrix)

    def transport(self, u: Any, v: Any) -> dict[int, dict[int, float]]:
        if (u, v) not in self._edges:
            raise KeyError(f"No connection defined on edge ({u}, {v})")
        return self._edges[(u, v)]

    def transport_path(self, path: Sequence[Any]) -> dict[int, dict[int, float]]:
        if len(path) < 2:
            # Identity d x d
            return {i: {i: 1.0} for i in range(self.fiber_dim)}

        result = self.transport(path[0], path[1])
        for i in range(1, len(path) - 1):
            next_step = self.transport(path[i], path[i + 1])
            result = dot(next_step, result, self._ring)
        return result
```

### 3. Discrete Curvature & Holonomy (`src/algebrax/topology/curvature.py`)

For any oriented 2-cell (triangle or polygon) $f = (v_0, v_1, \dots, v_{k-1})$, the **holonomy** is the Wilson loop around the boundary:

$$\operatorname{Hol}(f) = \rho(v_{k-1}, v_0) \cdots \rho(v_1, v_2) \cdot \rho(v_0, v_1)$$

```python
def compute_face_holonomy(
    connection: DiscreteConnection,
    face_boundary_vertices: Sequence[Any],
) -> dict[int, dict[int, float]]:
    r"""Compute the holonomy (Wilson loop) around a closed 2-face boundary."""
    cycle = list(face_boundary_vertices) + [face_boundary_vertices[0]]
    return connection.transport_path(cycle)


def is_flat_bundle(
    connection: DiscreteConnection,
    faces: Iterable[Sequence[Any]],
    tol: float = 1e-9,
) -> bool:
    r"""Test if the discrete bundle is flat (zero curvature on all faces: $\operatorname{Hol}(f) = \mathbf{I}$)."""
    dim = connection.fiber_dim
    for f in faces:
        hol = compute_face_holonomy(connection, f)
        for i in range(dim):
            for j in range(dim):
                expected = 1.0 if i == j else 0.0
                actual = hol.get(i, {}).get(j, 0.0)
                if abs(actual - expected) > tol:
                    return False
    return True
```

### 4. The Connection Laplacian ($L_\nabla$) (`src/algebrax/topology/connection_laplacian.py`)

The **Connection Laplacian** acts on vertex fiber fields $x \in \bigoplus_{v \in V} F_v$:
$$(L_\nabla x)(u) = \sum_{v \sim u} (x(u) - \rho(v, u) x(v))$$

In block matrix form:
$$L_\nabla = D \otimes \mathbf{I}_d - \mathbf{A}_\rho$$
where $\mathbf{A}_\rho(u, v) = \rho(v, u)$ is the connection-weighted block adjacency matrix.

```python
def build_connection_laplacian(
    connection: DiscreteConnection,
    adjacency: dict[Any, set[Any]],
) -> dict[tuple[Any, int], dict[tuple[Any, int], float]]:
    r"""Construct the sparse block Connection Laplacian $L_\nabla = D \otimes \mathbf{I}_d - \mathbf{A}_\rho$."""
    d = connection.fiber_dim
    laplacian: dict[tuple[Any, int], dict[tuple[Any, int], float]] = {}

    for u, neighbors in adjacency.items():
        degree = float(len(neighbors))
        # Diagonal block: degree * I_d
        for i in range(d):
            key_u = (u, i)
            laplacian.setdefault(key_u, {})[key_u] = degree

        # Off-diagonal blocks: -rho(v, u)
        for v in neighbors:
            rho_vu = connection.transport(v, u)
            for i, row in rho_vu.items():
                key_u = (u, i)
                for j, val in row.items():
                    key_v = (v, j)
                    laplacian.setdefault(key_u, {})[key_v] = (
                        laplacian.get(key_u, {}).get(key_v, 0.0) - val
                    )

    return laplacian
```

### 5. Bundle-Valued DEC & Covariant Exterior Derivative (`src/algebrax/dec/bundle_forms.py`)

Bundle-valued differential forms $\Omega^k(K; E)$ assign vectors in $\mathbb{R}^d$ to $k$-cells:
- **0-forms**: Vertex fields $x(v) \in \mathbb{R}^d$.
- **1-forms**: Edge fields $\omega(u, v) \in \mathbb{R}^d$ with $\omega(v, u) = -\rho(u, v) \omega(u, v)$.
- **Covariant Exterior Derivative**:
  $$(d_\nabla x)(u, v) = \rho(u, v) x(u) - x(v)$$
- **Curvature Invariant**:
  $$(d_\nabla^2 x)(f) = (\operatorname{Hol}(f) - \mathbf{I}) x(v_0)$$
  When the bundle is flat ($\operatorname{Hol}(f) = \mathbf{I}$), $d_\nabla^2 = \mathbf{0}$, producing **twisted de Rham cohomology**.

### 6. Executable Verification Suite (`src/algebrax/verification/bundle.py`)

```python
def verify_connection_inversion(connection: DiscreteConnection, edges: list[tuple[Any, Any]]) -> None:
    """Verify that transport(v, u) == transport(u, v)^-1."""
    ring = RealRing()
    d = connection.fiber_dim
    for u, v in edges:
        t_uv = connection.transport(u, v)
        t_vu = connection.transport(v, u)
        prod = dot(t_vu, t_uv, ring)
        for i in range(d):
            for j in range(d):
                expected = 1.0 if i == j else 0.0
                assert abs(prod.get(i, {}).get(j, 0.0) - expected) < 1e-12


def verify_gauge_covariance(
    connection: DiscreteConnection,
    adjacency: dict[Any, set[Any]],
    gauge_transform: dict[Any, dict[int, dict[int, float]]],
) -> None:
    r"""Verify that under local gauge transformation g_u, L_nabla transforms covariantly:
    $$L_{\nabla'} = \mathbf{G} L_\nabla \mathbf{G}^T$$
    """
    ...
```

---

## Backwards Compatibility

1. **Zero Impact on Existing DEC or Sheaf Modules**:
   `algebrax.dec` continues to compute standard scalar differential forms. `DiscreteConnection` is purely additive.
2. **Specialization of Cellular Sheaf**:
   A `DiscreteOrthogonalConnection` can be converted into a `FunctorialSheaf` ([EP-0202](EP-0202-functorial-sheaves-and-categorical-dec.md)) automatically via `connection.to_sheaf()`, maintaining full structural interoperability.

---

## How to Teach This / Documentation Plan

1. **Applied Guide (`docs/guides/discrete-fiber-bundles.md`)**:
   - Tutorial on angular synchronization: recovering 2D camera orientations from noisy pairwise angular differences $SO(2)$.
   - Tutorial on discrete curvature: calculating holonomy on curved triangular meshes (sphere vs. torus).
2. **Cross-Disciplinary Recipe (`recipes/angular_synchronization.py`)**:
   - Solve a synthetic cryo-EM / robotics pose-graph synchronization problem using the Connection Laplacian and sparse eigenvectors.

---

## Reference Implementation

A reference prototype of `DiscreteOrthogonalConnection`, `compute_face_holonomy`, and `build_connection_laplacian` was evaluated in Council exploration `references/explorations/EXP-0005-categorical-foundations-and-enriched-mechanics/README.md`.

---

## Rejected Ideas

1. **Continuous Manifold Charts & Atlases**:
   *Rejected*: Violates Shannon efficiency and AlgebraX scope. Continuous differential geometry with chart transitions belongs in symbolic CAS or formal proof engines.
2. **Heap-Boxed `Fiber` Class per Node**:
   *Rejected*: Wrapping every fiber vector in a class instance creates prohibitive garbage collection pressure. Vertices index flat tuple coordinates in sparse matrices `(node_id, fiber_coord)`.

---

## Open Questions

1. **Non-Compact Lie Groups**:
   Should we support non-compact structure groups like $SE(3)$ (rotations + translations)?
   *Recommendation*: Yes, represented as affine block matrices $\begin{pmatrix} R & t \\ 0 & 1 \end{pmatrix}$, widely used in robotics pose-graph SLAM.

---

## Change Log

- **2026-10-27**: Initial draft authored following Council consensus on EXP-0005 and fiber bundle architecture.
