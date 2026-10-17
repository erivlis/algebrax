---
title: "EP-0161: Cellular Sheaves, Sheaf Cohomology & Network Laplacians"
description: "Generalizes scalar graph Laplacians and cochains to vector-valued Cellular Sheaves with linear restriction maps, sheaf coboundary operators, and Sheaf Laplacians for heterogeneous consensus and opinion dynamics."
icon: lucide/network
status: final
---

# EP-0161: Cellular Sheaves, Sheaf Cohomology & Network Laplacians

| Field        | Value                                                                                                                    |
|:-------------|:-------------------------------------------------------------------------------------------------------------------------|
| **EP**       | 0161                                                                                                                     |
| **Title**    | Cellular Sheaves, Sheaf Cohomology & Network Laplacians                                                                  |
| **Author**   | Eran Rivlis & Antigravity (The Explorer)                                                                                 |
| **Sponsor**  | The Council                                                                                                              |
| **Delegate** | 🧩 Bertrand Russell (Consistency), 🤝 The Steward (Harmony), ⚖️ Emmy Noether (Symmetry) & ⚡ Claude Shannon (Efficiency) |
| **Status**   | Final                                                                                                                    |
| **Type**     | Standards Track                                                                                                          |
| **Created**  | 2026-10-16                                                                                                               |
| **Updated**  | 2026-10-17                                                                                                               |
| **Replaces** | None                                                                                                                     |

---

## Abstract

This proposal introduces **Cellular Sheaves** and **Sheaf Laplacians** in `algebrax.homology` and `algebrax.analysis`,
generalizing the scalar cochain calculus of [EP-0153](EP-0153-semiring-matrix-symmetry-and-vector-primitives.md)
and [EP-0160](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md) to heterogeneous, multi-dimensional vector
stalks over networks. Specifically, this proposal introduces:

1. **`CellularSheaf`**: A coordinate-sparse representation of a cellular sheaf $\mathcal{F}$ over a graph or 1-skeleton,
   assigning vector space dimensions $d_v = \dim \mathcal{F} (v)$ to vertices, $d_e = \dim \mathcal{F} (e)$ to edges,
   and linear restriction maps $\rho_{v \trianglelefteq e}: \mathcal{F} (v) \to \mathcal{F} (e)$ along incidence
   relations.
2. **Sheaf Coboundary Operator ($\delta_{\mathcal{F}}: C^0 (G; \mathcal{F}) \to C^1 (G; \mathcal{F})$)**: Measures local
   disagreement across edge stalks:
   $$(\delta_{\mathcal{F}} x)_{e = (u, v)} = \rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u$$
3. **Sheaf Laplacian ($L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$)**: A symmetric positive
   semi-definite block-sparse operator indexed natively by product keys `(vertex, stalk_dim)` whose
   kernel $\ker L_{\mathcal{F}} = H^0 (G; \mathcal{F})$ is the space of **global sections** (globally consistent network
   states).
4. **Sheaf Diffusion, Dirichlet Disagreement Energy & Harmonic Extension**: Algorithms for multi-agent consensus under
   local coordinate transformations, polarized opinion dynamics (Hansen & Ghrist), and boundary-value harmonic
   interpolation via `cg_solve`.

---

## Motivation

Standard spectral graph theory ([EP-0152](EP-0152-spectral-graph-theory-laplacian.md)) and scalar Discrete Exterior
Calculus ([EP-0160](EP-0160-discrete-exterior-calculus-and-hodge-decomposition.md)) implicitly assume the **constant
sheaf**: every node holds a scalar in the same global coordinate system, and every edge compares connected nodes via
identity maps $f (v) - f (u)$.

In real-world distributed systems, this assumption fails:

- **Multi-Frame Sensor Networks & Robotics**: Autonomous agents measure 2D/3D positions or velocities in their own
  rotated local coordinate frames. Reaching consensus requires comparing states through orthogonal transformation
  matrices $\rho_{u \trianglelefteq e} \in SO (d)$ (connection graphs / vector bundles).
- **Heterogeneous Feature Spaces**: Node $u$ may track a 4D state vector while node $v$ tracks a 2D state vector,
  comparing only a shared 1D or 2D projection on their connecting edge stalk $\mathcal{F} (e)$.
- **Opinion Dynamics with Ideological Polarization**: In social networks, agents may hold multi-topic belief vectors and
  translate topics into public discourse differently along different relationships, naturally producing polarization,
  clustering, or persistent disagreement ($\ker L_{\mathcal{F}} = \{0\}$).

By indexing sparse matrices with product tuple keys `(cell, dim_idx)`, `algebrax`'s dictionary-of-dictionaries
architecture (`SparseMatrix[tuple[K, int], float]`) represents block-structured sheaf operators without dense matrix
padding or external array dependencies.

---

## Rationale

The design aligns with the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Consistency (Russell)

- **Strict Generalization of Graph Laplacians**: When $\dim \mathcal{F} (v) = \dim \mathcal{F} (e) = 1$
  and $\rho_{u \trianglelefteq e} = \rho_{v \trianglelefteq e} = [1.0]$ for all incidences, the Sheaf
  Laplacian $L_{\mathcal{F}}$ reduces *identically* to the combinatorial graph Laplacian $L_0 = D - A = d_0^T d_0$.
- **Product-Key Type Safety**: Using 2-tuple keys `(u, i)` for $0$-cochain coordinates ($u \in V, \, 0 \le i < d_u$) and
  `((u, v), j)` for $1$-cochain coordinates ($e = (u, v) \in E, \, 0 \le j < d_e$) preserves the `SparseVector` and
  `SparseMatrix` contracts across all existing `algebrax.matrix` primitives (`dot`, `transpose`, `mat_vec`, `inner`,
  `cg_solve`).

### 2. Symmetry (Noether)

- **Self-Adjoint Hodge Structure**: For any cellular sheaf $\mathcal{F}$ with inner-product
  stalks, $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$ is symmetric positive semi-definite, and the
  **Sheaf Dirichlet Energy** satisfies:
  $$E_{\mathcal{F}} (x) = \frac{1}{2} \langle x, L_{\mathcal{F}} x \rangle = \frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2 = \frac{1}{2} \sum_{e= (u,v) \in E} \|\rho_{v \trianglelefteq e} x_v - \rho_{u \trianglelefteq e} x_u\|_2^2 \ge 0$$
- **Global Sections as Conservation Laws**: A 0-cochain $x \in C^0 (G; \mathcal{F})$ is a global section
  ($x \in H^0 (G; \mathcal{F})$) if and only
  if $\delta_{\mathcal{F}} x = 0 \iff L_{\mathcal{F}} x = 0 \iff E_{\mathcal{F}} (x) = 0$.

### 3. Efficiency (Shannon)

- **Coordinate-Sparse Block Assembly**: Restriction maps $\rho_{v \trianglelefteq e}$ are stored as sparse dictionaries
  `dict[int, dict[int, float]]` (or dense 2D sequences automatically pruned of zeros),
  ensuring $O (\text{nnz} (\delta_{\mathcal{F}}))$ memory and time complexity.
- **Reuse of `cg_solve` and `vec_axpy`**: Harmonic extension (clamping boundary vertices $B \subset V$ and solving for
  interior vertices $U = V \setminus B$ minimizing $E_{\mathcal{F}} (x)$) reuses `cg_solve` and `vec_axpy` from
  `algebrax.matrix` with zero code duplication.

### 4. Clarity (Feynman)

- **The Freshman Test**: A cellular sheaf is a network where every node has its own "private notebook"
  ($\mathcal{F} (v)$), every edge has a "public bulletin board" ($\mathcal{F} (e)$), and restriction
  maps $\rho_{v \trianglelefteq e}$ are the rules for translating a node's private notes onto the shared bulletin board.
  Two neighbors agree on an edge when they post the exact same message on the bulletin board
  ($\rho_{u \trianglelefteq e} x_u = \rho_{v \trianglelefteq e} x_v$).

### 5. Falsifiability (Popper)

1. **Constant Sheaf Equivalence**: On any weighted or unweighted graph, constructing
   `CellularSheaf.constant(graph, stalk_dim=1)` must produce a `sheaf_laplacian` whose action matches
   `laplacian_matrix(graph)` to machine precision.
2. **Orthogonal Connection Sheaf Holonomy**: On a 3-cycle with $SO (2)$ rotation restriction maps whose loop composition
   (holonomy) is $I$, $\dim \ker L_{\mathcal{F}} = 2$ (non-trivial global sections exist); if the loop holonomy is $-I$
   (a discrete Möbius strip / frustrated cycle), $\dim \ker L_{\mathcal{F}} = 0$ and sheaf diffusion converges to zero.
3. **Harmonic Extension Optimality**: Solving `sheaf_harmonic_extension` with fixed boundary stalks $x_B$ must
   satisfy $(L_{\mathcal{F}} x)_{ (u, i)} = 0$ on all interior coordinates $u \in V \setminus B$.

---

## Specification

### 1. Carrier & Operator API in `algebrax.homology` (re-exported in `algebrax.analysis`)

```python
from collections.abc import Mapping, Sequence
from algebrax.typing import K, SparseMatrix, SparseVector

StalkCoord = tuple[K, int]
EdgeStalkCoord = tuple[tuple[K, K], int]
RestrictionMap = Mapping[int, Mapping[int, float]] | Sequence[Sequence[float]]


class CellularSheaf:
    r"""Cellular sheaf $\mathcal{F}$ over a 1-dimensional cell complex (graph) $G = (V, E)$.

    Algebraic Signature:
        $\mathcal{F} = \left(\{\mathcal{F}(v)\}_{v \in V}, \{\mathcal{F}(e)\}_{e \in E},
        \{\rho_{v \trianglelefteq e}: \mathcal{F}(v) \to \mathcal{F}(e)\}\right)$
    """

    def __init__(
        self,
        vertex_stalks: Mapping[K, int] | None = None,
        edge_stalks: Mapping[tuple[K, K], int] | None = None,
        restrictions: Mapping[tuple[K, tuple[K, K]], RestrictionMap] | None = None,
    ) -> None: ...

    def add_vertex(self, vertex: K, dim: int = 1) -> None: ...

    def add_edge(
        self,
        u: K,
        v: K,
        dim: int,
        rho_u: RestrictionMap,
        rho_v: RestrictionMap,
    ) -> None: ...

    @classmethod
    def constant(
        cls,
        graph: SparseMatrix[K, float],
        stalk_dim: int = 1,
    ) -> CellularSheaf:
        """Construct the constant sheaf (or weighted scalar sheaf) of dimension `stalk_dim` over `graph`."""

    def coboundary_matrix(self) -> SparseMatrix[EdgeStalkCoord, float]:
        r"""Assemble the sparse sheaf coboundary matrix $\delta_{\mathcal{F}}: C^0(G; \mathcal{F}) \to C^1(G; \mathcal{F})$."""

    def laplacian_matrix(self) -> SparseMatrix[StalkCoord, float]:
        r"""Assemble the symmetric positive semi-definite Sheaf Laplacian $L_{\mathcal{F}} = \delta_{\mathcal{F}}^T \delta_{\mathcal{F}}$."""

    def dirichlet_energy(self, section: SparseVector[StalkCoord, float]) -> float:
        r"""Compute total sheaf disagreement energy $\frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2$."""

    def global_sections_dimension(self, tol: float = 1e-9) -> int:
        r"""Compute $\dim H^0(G; \mathcal{F}) = \dim \ker L_{\mathcal{F}}$."""
```

### 2. Functional Operations

```python
def sheaf_laplacian(sheaf: CellularSheaf) -> SparseMatrix[StalkCoord, float]:
    """Return the sparse Sheaf Laplacian matrix $L_{\\mathcal{F}} = \\delta_{\\mathcal{F}}^T \\delta_{\\mathcal{F}}$."""


def sheaf_diffusion(
    sheaf: CellularSheaf,
    initial_state: SparseVector[StalkCoord, float],
    steps: int = 20,
    tau: float = 0.1,
) -> dict[StalkCoord, float]:
    r"""Simulate discrete-time sheaf heat diffusion $x^{(t+1)} = (I - \tau L_{\mathcal{F}}) x^{(t)}$."""


def sheaf_harmonic_extension(
    sheaf: CellularSheaf,
    boundary_values: SparseVector[StalkCoord, float],
    boundary_vertices: set[K],
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> dict[StalkCoord, float]:
    r"""Compute the harmonic 0-cochain $x \in C^0(G; \mathcal{F})$ minimizing $\frac{1}{2} \|\delta_{\mathcal{F}} x\|_2^2$ subject to $x|_B = \text{boundary\_values}$."""
```

---

## Backwards Compatibility

Purely additive. All existing `SimplicialComplex`, `SparseChainComplex`, `Cochain`, and `analysis` APIs remain
unchanged.

---

## How to Teach This / Documentation Plan

1. **User Guide**: Add a dedicated section in `docs/guide/homology/chain_complex.md` and
   `docs/guide/analysis/discrete_calculus.md` illustrating:
    - Constant sheaves vs. connection sheaves (2D local frame alignment).
    - Frustrated cycles (discrete Möbius bundle where global consensus is impossible).
    - Boundary-value harmonic interpolation across heterogeneous stalks.
2. **Recipe**: Add a multi-agent opinion dynamics / sensor calibration recipe in `docs/recipes.md`.

---

## Reference Implementation

```python
from collections.abc import Mapping, Sequence
from algebrax.matrix import cg_solve, dot, inner, mat_vec, transpose, vec_axpy, vec_clean


def _normalize_restriction(
    rho: Mapping[int, Mapping[int, float]] | Sequence[Sequence[float]],
) -> dict[int, dict[int, float]]:
    if isinstance(rho, Mapping):
        return {int(r): {int(c): float(v) for c, v in row.items() if abs(float(v)) > 1e-15} for r, row in rho.items()}
    out: dict[int, dict[int, float]] = {}
    for r, row in enumerate(rho):
        row_dict = {c: float(v) for c, v in enumerate(row) if abs(float(v)) > 1e-15}
        if row_dict:
            out[r] = row_dict
    return out
```

Looking at the coboundary assembly: for each canonical edge $e = (u, v)$ with $u < v$ and edge stalk
coordinate $j \in \{0, \dots, d_e - 1\}$:

- Row key in $\delta_{\mathcal{F}}$ is `(e, j)`.
- Column keys are `(v, i)` with value $+\rho_{v \trianglelefteq e}[j, i]$ and `(u, i)` with
  value $-\rho_{u \trianglelefteq e}[j, i]$.
- Then $L_{\mathcal{F}} = \text{dot} (\text{transpose} (\delta_{\mathcal{F}}), \delta_{\mathcal{F}})$ immediately yields
  the `(vertex, i)`-indexed sparse Sheaf Laplacian!

---

## Rejected Ideas

1. **Flattening Coordinates into Integer Global Indices (`0..N-1`)**:
    - *Considered*: Mapping each `(vertex, dim_idx)` pair to a contiguous integer `0..D-1`.
    - *Rejected*: Forces callers to maintain an external index-lookup table and loses the semantic clarity of `algebrax`
      's dictionary keys. Using tuple keys `(vertex, dim_idx)` works natively with all `algebrax.matrix` operations
      (`dot`, `transpose`, `mat_vec`, `cg_solve`).

---

## Open Questions

- [ ] Should `CellularSheaf` also support 2-simplices ($\delta_1: C^1 (K; \mathcal{F}) \to C^2 (K; \mathcal{F})$) in the
  initial release, or focus on 1-dimensional cellular network sheaves ($C^0 \to C^1$) where 95% of consensus and
  connection-Laplacian applications reside?

---

## Change Log

* **2026-10-17:** Finalized and fully implemented with `CellularSheaf`, `sheaf_laplacian`, `sheaf_diffusion`, and `sheaf_harmonic_extension` in `algebrax.homology` and `algebrax.analysis`.
* **2026-10-16:** Initial Draft authored by Eran Rivlis & Antigravity, building on `EP-0153` and `EP-0160`.
