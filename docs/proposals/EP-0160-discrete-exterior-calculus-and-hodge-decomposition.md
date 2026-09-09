---
title: "EP-0160: Discrete Exterior Calculus & Helmholtz-Hodge Flow Decomposition"
description: "Establishes Discrete Exterior Calculus (DEC) and the Helmholtz-Hodge flow decomposition on simplicial and network complexes."
icon: lucide/triangle
status: draft
---

# EP-0160: Discrete Exterior Calculus & Helmholtz-Hodge Flow Decomposition

| Field        | Value                                                                                     |
|:-------------|:------------------------------------------------------------------------------------------|
| **EP**       | 0160                                                                                      |
| **Title**    | Discrete Exterior Calculus & Helmholtz-Hodge Flow Decomposition                           |
| **Author**   | Eran Rivlis & Antigravity (The Explorer)                                                  |
| **Sponsor**  | The Council                                                                               |
| **Delegate** | ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency) & 💡 Richard Feynman (Clarity) |
| **Status**   | Draft                                                                                     |
| **Type**     | Standards Track                                                                           |
| **Created**  | 2026-09-08                                                                                |
| **Updated**  | 2026-09-09                                                                                |
| **Replaces** | None                                                                                      |

---

## Abstract

This proposal establishes native support for **Discrete Exterior Calculus (DEC)** and the **Helmholtz–Hodge Flow
Decomposition** within AlgebraX. Extending the topological foundation of `algebrax.homology` (simplicial chains and
boundary operators $\partial_k$), this proposal introduces:

1. Discrete differential forms ($\Omega^k (K)$) as cochains over oriented $k$-simplices.
2. The discrete exterior derivative operator $d_k: \Omega^k \to \Omega^{k+1}$, defined as the adjoint (transpose) of the
   boundary operator $d_k = \partial_{k+1}^T$, naturally satisfying the exact chain property $d_{k+1} \circ d_k = 0$.
3. The discrete Hodge star operator $\star_k: \Omega^k \to \Omega^{n-k}$ and codifferential $\delta_k = d_{k-1}^*$.
4. The discrete Hodge–Laplacian $\Delta_k = d_{k-1} \delta_k + \delta_{k+1} d_k$ operating on general $k$-forms
   (generalizing 0-form graph Laplacians to edge circulation and face vorticity).
5. The **Helmholtz–Hodge Decomposition Engine** for arbitrary network flows and directed edge fields:
   $$\omega = d\alpha + \delta\beta + \gamma$$
   orthogonally decomposing any edge flow into an exact potential gradient flow ($d\alpha$), a coexact divergence-free
   circulation ($\delta\beta$), and a harmonic topological circulation
   ($\gamma \in \ker \Delta_1 \cong H_1 (K; \mathbb{R})$).

---

## Motivation

While AlgebraX possesses simplicial homology (`algebrax.homology.SimplicialComplex`) and spectral graph theory
(`algebrax.matrix.laplacian_matrix`, `algebrax.analysis.fiedler_vector`), applied vector calculus on networks remains
incomplete:

- **Missing Differential Forms**: Primal chains $C_k$ represent geometric elements (nodes, directed edges, triangular
  faces), but real-world physical and data signals (node pressures, edge fluxes, face curls) live naturally on the dual
  spaces—the **cochain groups** $C^k (K; \mathbb{R}) \cong \Omega^k (K)$.
- **Lack of Vector Field Decomposition**: In network optimization, traffic engineering, fluid flow simulation, financial
  transaction routing, and ranking systems (e.g., HodgeRank), directed edge flows are mixtures of three distinct
  physical phenomena:
    1. *Gradient / Potential Flow*: Flows driven by conservative node potentials (e.g., price differences, voltage,
       hydrostatic pressure).
    2. *Local Circulations / Curls*: Solenoidal eddy currents circulating around triangular 2-cells (e.g., arbitrage
       loops, local vortexes).
    3. *Harmonic / Global Circulations*: Non-trivial circulatory flows wrapping around topological cavities or
       non-contractible holes in the network (e.g., persistent cycles around city centers or structural bottlenecks).
- **The Graph Laplacian Limitation**: The standard graph Laplacian $L_0 = D - A = \partial_1 \partial_1^T$ is merely
  the $k=0$ special case ($\Delta_0 = \delta_1 d_0$) of the Hodge Laplacian. It cannot analyze higher-dimensional
  phenomena such as edge cross-talk or vortex conservation.

By introducing DEC and the Helmholtz–Hodge decomposition natively in `algebrax.analysis` and `algebrax.homology`,
AlgebraX provides an exact, zero-dependency, coordinate-sparse discrete differential geometry framework.

---

## Rationale & The Council Alignment

The design is governed by the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Symmetry (Noether)

- **Exterior Adjoint Symmetry**: The exterior derivative $d_k$ and the boundary operator $\partial_{k+1}$ are dual
  adjoints:
  $$\langle d\omega, \sigma \rangle = \langle \omega, \partial \sigma \rangle \implies d_k = \partial_{k+1}^T$$
- **Nilpotency Conservation**: Just as $\partial_k \circ \partial_{k+1} = 0$, the exterior derivative rigorously
  conserves nilpotency:
  $$d_{k+1} \circ d_k = (\partial_{k+1} \circ \partial_{k+2})^T = 0^T = 0$$
- **Hodge Orthogonality**: By the Discrete Hodge Decomposition Theorem, the $L^2$ inner product space of 1-forms
  decomposes into mutually orthogonal subspaces:
  $$\Omega^1 (K) = \mathrm{im} (d_0) \oplus \mathrm{im} (\delta_2) \oplus \mathcal{H}_1 (K)$$
  where $\mathcal{H}_1 (K) = \ker (d_1) \cap \ker (\delta_1) = \ker (\Delta_1) \cong H_1 (K; \mathbb{R})$.

### 2. Efficiency (Shannon)

- **Coordinate-Sparse Operators**: Boundary operators $\partial_k$ and exterior derivatives $d_k$ contain only entries
  in $\{-1, 0, 1\}$. They are encoded natively in `SparseMatrix` format.
- **Pure-Python Conjugate Gradient Solver**: Solving for potentials $\alpha$ and stream functions $\beta$ requires
  solving symmetric positive semi-definite systems:
  $$\Delta_0 \alpha = \delta_1 \omega, \quad \Delta_2 \beta = d_1 \omega$$
  Because $\Delta_0$ and $\Delta_2$ are positive semi-definite (singular with nullspaces corresponding to connected
  components $\beta_0$ and topological voids $\beta_2$), standard Cholesky decomposition fails ($s \le 0$). A
  coordinate-sparse Conjugate Gradient (CG) solver with nullspace projection (deflation onto $\mathbf{1}^\perp$)
  achieves convergence in $O (|E| \sqrt{\kappa})$ iterations without matrix inversions.
- **Unification with Existing Subsystems**: Avoid duplicating existing homological infrastructure.
  `algebrax.homology.coboundary(complex, k)` already computes $d^k = \partial_{k+1}^T$, and
  `SparseChainComplex.hodge_laplacian` computes $\Delta_k$. `algebrax.analysis` integrates these foundations into the
  discrete forms calculus and flow decomposition engine.

### 3. Safety (The Golem)

- **Orientation Canonicalization**: Simplices in AlgebraX are canonically stored as sorted tuples
  `(v_0, v_1, \dots, v_k)` with $v_0 < v_1 < \dots < v_k$. Directed edge flows supplied with reverse orientation
  `(u, v)` where $u > v$ are automatically canonicalized via sign inversion: $\omega ((u, v)) = -\omega ((v, u))$.
- **Gauge Deflation**: The constant vector $\mathbf{1}$ spans the nullspace of $\Delta_0$ for each connected component.
  To prevent drift and ill-conditioning in the iterative solver, node potentials $\alpha$ are gauge-fixed by projecting
  intermediate residuals onto $\mathbf{1}^\perp$ (mean-zero gauge: $\sum_{v \in C} \alpha_v = 0$).
- **Dimension Boundary Guards**: Boundary operators $\partial_k$ are guarded against complex dimension overshoots
  ($k < 0$ or $k > \dim (K)$), returning empty sparse matrices gracefully.

### 4. Clarity (Feynman)

- **The Freshman Test**: Discrete Exterior Calculus replaces continuous vector calculus (grad, curl, div) with simple
  incidence matrix multiplications on graphs:
    - Gradient of node potentials $\to d_0: \Omega^0 \to \Omega^1$.
    - Curl of edge flows $\to d_1: \Omega^1 \to \Omega^2$.
    - Divergence of edge flows $\to \delta_1 = d_0^T: \Omega^1 \to \Omega^0$.
    - The Helmholtz decomposition separates any network flow into "water running downhill" ($d\alpha$), "whirlpools
      inside triangles" ($\delta\beta$), and "river loops circling an island" ($\gamma$).

### 5. Falsifiability (Popper)

- The implementation will be falsified on exact analytical topologies:
    1. **Acyclic Tree**: Every edge flow is purely exact ($\delta\beta = 0$, $\gamma = 0$).
    2. **Planar Triangulated Disc**: Every boundary-free cycle decomposes into curl around faces
       ($\gamma = 0$, $H_1 = 0$).
    3. **Oriented Ring / Wheel Graph**: Unit circulation along the perimeter produces a pure harmonic field
       ($\gamma \ne 0, d\alpha = 0, \delta\beta = 0$).
    4. **Orthogonality
       Check**: $\langle d\alpha, \delta\beta \rangle = 0$, $\langle d\alpha, \gamma \rangle = 0$, $\langle \delta\beta, \gamma \rangle = 0$
       to within machine precision $\epsilon < 10^{-12}$.

---

## Specification

### 1. Data Models & Type Contracts

```python
from collections.abc import Mapping
from typing import NamedTuple, TypeAlias
from algebrax.typing import SparseMatrix, SparseVector

Simplex: TypeAlias = tuple[int, ...]
DiscreteForm: TypeAlias = SparseVector[Simplex, float]


class HodgeDecomposition(NamedTuple):
    """Result of Helmholtz-Hodge decomposition on a 1-form (edge flow)."""
    exact: DiscreteForm  # Gradient flow d(alpha) in im(d_0)
    coexact: DiscreteForm  # Solenoidal circulation delta(beta) in im(delta_2)
    harmonic: DiscreteForm  # Topological circulation gamma in ker(Delta_1)
    potential: DiscreteForm  # 0-form potential alpha such that exact = d(alpha)
    stream: DiscreteForm  # 2-form stream function beta such that coexact = delta(beta)
```

### 2. Foundational Sparse Linear Solver in `algebrax.matrix`

To support singular and semi-definite systems ($\Delta_0 \alpha = \delta_1 \omega$), `algebrax.matrix` provides:

```python
def cg_solve(
        matrix: SparseMatrix[K, float],
        rhs: SparseVector[K, float],
        tol: float = 1e-9,
        max_iter: int | None = None,
        project_nullspace: bool = False,
) -> SparseVector[K, float]:
    r"""Solve A x = b for a symmetric positive semi-definite sparse matrix A using Conjugate Gradients.
    
    If project_nullspace is True, deflates the constant nullspace component (1^T x = 0)
    at each iteration.
    """
    ...
```

### 3. Core Mathematical Operators in `algebrax.analysis`

```python
def exterior_derivative(
        complex: SimplicialComplex,
        k: int,
) -> SparseMatrix[Simplex, float]:
    r"""Construct the discrete exterior derivative operator d_k: \Omega^k -> \Omega^{k+1}.
    
    Equivalent to coboundary(complex, k) == \partial_{k+1}^T.
    """
    ...


def hodge_laplacian(
        complex: SimplicialComplex,
        k: int,
) -> SparseMatrix[Simplex, float]:
    r"""Construct the k-th Hodge Laplacian operator \Delta_k.
    
    \Delta_k = d_{k-1} \delta_k + \delta_{k+1} d_k
             = \partial_k^T \partial_k + \partial_{k+1} \partial_{k+1}^T
    """
    ...


def canonicalize_form(
        flow: Mapping[tuple[int, ...], float],
) -> dict[tuple[int, ...], float]:
    r"""Normalize simplex orientations so that keys are sorted tuples, flipping sign on parity swap."""
    ...


def helmholtz_hodge_decomposition(
        complex: SimplicialComplex,
        flow: Mapping[tuple[int, ...], float],
        tol: float = 1e-9,
        max_iter: int = 1000,
) -> HodgeDecomposition:
    r"""Decompose a 1-form (edge flow) into exact, coexact, and harmonic components.
    
    \omega = d(\alpha) + \delta(\beta) + \gamma
    where:
        \Delta_0 \alpha = \partial_1 \omega (solved via deflated CG)
        exact = \partial_1^T \alpha
        
        \Delta_2 \beta = \partial_2^T \omega (solved via CG on 2-simplices)
        coexact = \partial_2 \beta
        
        harmonic = \omega - exact - coexact
    """
    ...
```

---

## Backwards Compatibility

This proposal is purely additive:

- Existing simplicial homology APIs (`algebrax.homology.SimplicialComplex`, `boundary_matrix`, `betti_numbers`) remain
  completely untouched.
- `exterior_derivative` and `hodge_laplacian` leverage the existing `SparseMatrix` data structure and sparse operations
  in `algebrax.matrix`.
- No existing public interfaces or serialized state are modified.

---

## How to Teach This / Documentation Plan

1. **User Guide**: Add `docs/guide/analysis/discrete_exterior_calculus.md` detailing:
    - Cochains as discrete forms.
    - The boundary-exterior derivative adjunction ($\partial_k^T = d_{k-1}$).
    - Visual step-by-step diagram of Helmholtz-Hodge flow decomposition.
2. **Interactive Recipe**: Add a practical recipe in `docs/recipes.md`:
    - *Financial Arbitrage Loop Detection*: Using $\delta\beta$ to uncover triangular currency arbitrage and $\gamma$
      for structural capital drain loops.
    - *Traffic Network Bottlenecks*: Separating rush-hour commuter gradient flows from city-center topological
      circulation.

---

## Reference Implementation

```python
import math
from collections.abc import Mapping
from algebrax.matrix import dot, mat_vec, transpose, add, subtract
from algebrax.homology import SimplicialComplex, coboundary
from algebrax.typing import SparseMatrix, SparseVector


def cg_solve(
        matrix: SparseMatrix,
        rhs: SparseVector,
        tol: float = 1e-9,
        max_iter: int = 500,
        project_nullspace: bool = False,
) -> dict:
    """Coordinate-sparse Conjugate Gradient solver for positive semi-definite systems."""
    keys = list(matrix.keys())
    if not keys or not rhs:
        return {}

    def inner_prod(v1, v2):
        return sum(v1.get(k, 0.0) * v2.get(k, 0.0) for k in keys)

    def deflate(v):
        if not project_nullspace or not keys:
            return v
        mean = sum(v.get(k, 0.0) for k in keys) / len(keys)
        return {k: v.get(k, 0.0) - mean for k in keys if abs(v.get(k, 0.0) - mean) > 1e-15}

    x = {k: 0.0 for k in keys}
    b = deflate(dict(rhs)) if project_nullspace else dict(rhs)
    r = dict(b)
    p = dict(r)
    rsold = inner_prod(r, r)

    if rsold < tol * tol:
        return x

    for _ in range(max_iter):
        ap = mat_vec(matrix, p)
        if project_nullspace:
            ap = deflate(ap)
        pap = inner_prod(p, ap)
        if abs(pap) < 1e-15:
            break
        alpha = rsold / pap
        for k in keys:
            x[k] = x.get(k, 0.0) + alpha * p.get(k, 0.0)
            r[k] = r.get(k, 0.0) - alpha * ap.get(k, 0.0)
        if project_nullspace:
            r = deflate(r)
        rsnew = inner_prod(r, r)
        if math.sqrt(rsnew) < tol:
            break
        beta = rsnew / rsold
        for k in keys:
            p[k] = r.get(k, 0.0) + beta * p.get(k, 0.0)
        rsold = rsnew

    return {k: v for k, v in x.items() if abs(v) > 1e-12}


def helmholtz_hodge_decomposition(
        complex: SimplicialComplex,
        flow: Mapping[tuple[int, ...], float],
) -> HodgeDecomposition:
    # 1. Operators
    b1 = complex.boundary_matrices.get(1, {})  # \partial_1: C_1 -> C_0
    d0 = transpose(b1)  # d_0 = \partial_1^T: C^0 -> C^1
    delta0 = dot(b1, d0)  # \Delta_0 = \partial_1 \partial_1^T

    # 2. Exact component (potential flow)
    div_flow = mat_vec(b1, flow)  # \delta_1 \omega = \partial_1 \omega
    alpha = cg_solve(delta0, div_flow, project_nullspace=True)
    exact = mat_vec(d0, alpha)

    # 3. Coexact component (solenoidal circulation)
    coexact = {}
    stream = {}
    if 2 in complex.boundary_matrices:
        b2 = complex.boundary_matrices[2]  # \partial_2: C_2 -> C_1
        d1 = transpose(b2)  # d_1: C^1 -> C^2
        delta2 = dot(d1, b2)  # \partial_2^T \partial_2
        curl_flow = mat_vec(d1, flow)  # d_1 \omega = \partial_2^T \omega
        stream = cg_solve(delta2, curl_flow)
        coexact = mat_vec(b2, stream)

    # 4. Harmonic component
    # \gamma = \omega - exact - coexact
    harmonic = {}
    all_edges = set(flow.keys()) | set(exact.keys()) | set(coexact.keys())
    for e in all_edges:
        val = flow.get(e, 0.0) - exact.get(e, 0.0) - coexact.get(e, 0.0)
        if abs(val) > 1e-10:
            harmonic[e] = val

    return HodgeDecomposition(
        exact=exact,
        coexact=coexact,
        harmonic=harmonic,
        potential=alpha,
        stream=stream,
    )
```

---

## Rejected Ideas

1. **Continuous Metric Hodge Star Interpolation (Whitney Forms)**:
    - *Considered*: Implementing finite-element Whitney basis forms to compute continuous Hodge stars over geometric
      Riemannian metric tensors.
    - *Rejected*: Violates zero-dependency and minimal representation principles. Discrete cochain calculus with
      combinatorial or Voronoi dual weights provides exact topological and orthogonal properties with minimal
      computational overhead.
2. **Dense Pseudoinverse via SVD**:
    - *Considered*: Computing $\alpha = \Delta_0^+ (\partial_1 \omega)$ via dense Moore-Penrose pseudoinverse.
    - *Rejected*: Incurrs $O (N^3)$ computational cost and breaks sparse scaling. Conjugate gradients directly over
      `SparseMatrix` solves the potential equations in $O (|E|)$ iterations.

---

## Open Questions

- [ ] Should arbitrary circumcentric dual cell volume weights (geometric Hodge star) be configurable as an optional
  parameter to `hodge_star`, defaulting to standard combinatorial (identity) weights?
- [ ] Should HodgeRank (global ranking from inconsistent pairwise comparisons) be packaged as a convenience helper on
  top of `helmholtz_hodge_decomposition`?

---

## Change Log

* **2026-09-09:**
    * Council Review amendments incorporating The Dennis Point:
        - Added specification of pure-Python coordinate-sparse Conjugate Gradient (`cg_solve`) with nullspace deflation
          to resolve singular Hodge Laplacians without external dependencies.
        - Explicitly aligned `exterior_derivative` and `hodge_laplacian` with existing foundations in
          `algebrax.homology.coboundary` and `SparseChainComplex`.
        - Added orientation canonicalization rules for input forms.
        - Updated Reference Implementation with the complete gauge-fixed decomposition pipeline.
* **2026-09-08:**
    * Initial Draft authored by Eran Rivlis and Antigravity (The Explorer).
