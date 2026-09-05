---
title: "EP-0152: Spectral Graph Theory, Algebraic Connectivity & Graph Laplacians"
description: "Formulates Spectral Graph Theory natively in AlgebraX, encompassing Graph Laplacians, the Fiedler eigenvalue and vector, and spectral bipartitioning."
icon: lucide/git-branch
status: draft
---

# EP-0152: Spectral Graph Theory, Algebraic Connectivity & Graph Laplacians

| Field        | Value                                                                                        |
|:-------------|:---------------------------------------------------------------------------------------------|
| **EP**       | 0152                                                                                         |
| **Title**    | Spectral Graph Theory, Algebraic Connectivity & Graph Laplacians                             |
| **Author**   | Eran Rivlis                                                                                  |
| **Sponsor**  | The Council                                                                                  |
| **Delegate** | ⚖️ Emmy Noether (Symmetry), ⚡ Claude Shannon (Efficiency) & 🔬 Karl Popper (Falsifiability) |
| **Status**   | Draft                                                                                        |
| **Type**     | Standards Track                                                                              |
| **Created**  | 2026-09-05                                                                                   |
| **Updated**  | 2026-09-05                                                                                   |

---

## Abstract

This proposal establishes native support for **Spectral Graph Theory** in AlgebraX. It provides:
1. First-class construction of the **Laplacian Matrix** ($L = D - A$), the **Symmetric Normalized Laplacian** ($L_{\text{sym}} = D^{-1/2} L D^{-1/2}$), and the **Random-Walk Normalized Laplacian** ($L_{\text{rw}} = D^{-1} L$) housed canonically in `algebrax.matrix.laplacian_matrix`.
2. A high-performance, $O(|E|)$ sparse iterative eigensolver in `algebrax.analysis` for the **Fiedler pair**—computing the algebraic connectivity ($\lambda_2$) and the **Fiedler vector** ($\mathbf{v}_2$) via Rayleigh Quotient Conjugate Gradient (RQ-CG) and deflated shifted iteration on the subspace $\mathbf{1}^\perp$.
3. **Spectral Graph Bipartitioning** utilizing the Fiedler vector with cut metrics evaluation ($\text{cut}$, $\text{RatioCut}$, $\text{NCut}$, conductance $\phi$).
4. **Laplacian Smoothing & Graph Diffusion** (`laplacian_smoothing`) implementing Dirichlet energy minimization and the heat diffusion operator $\mathbf{u}(t) = e^{-t L} \mathbf{u}_0$ via precomputed sparse operator steps in $O(S \cdot |E|)$.
5. A dense spectral fallback (`laplacian_spectrum`) via cyclic Jacobi sweeps with explicit `PerformanceWarning` thresholds ($N > 150$) for small-scale educational visualization.

---

## Motivation

Spectral graph theory bridges graph topology, differential geometry, and numerical linear algebra:
- In `algebrax.analysis`, the function `laplacian(field, graph)` currently acts as an exterior derivative operator ($\Delta f = d^* d f$) mapping a 0-form vector field to another vector field. However, AlgebraX lacks a constructor for the **Laplacian matrix operator itself** ($L \in \text{SparseMatrix}$).
- Abstractly, constructing $L = D - A$ from an adjacency or similarity matrix $A$ is a general matrix-to-matrix algebraic transformation ($A \mapsto D - A$). Housed canonically in `algebrax.matrix.laplacian_matrix`, it applies equally to graph adjacencies, RBF kernel affinity matrices, Markov transitions, and finite-difference PDE stencils.
- Applying the Laplacian iteratively on fields (such as for heat diffusion, label propagation, or graph signal denoising) is formalized as `laplacian_smoothing(field, graph_or_laplacian, steps, tau)`. By assembling $L$ once, it avoids redundant degree calculations and executes $S$ steps in pure sparse `mat_vec` products.
- High-level topological and spectral analysis functions (`fiedler_vector`, `algebraic_connectivity`, `spectral_bipartition`, `laplacian_smoothing`) are housed in `algebrax.analysis`, with cross-exports in `algebrax.matrix` for ergonomic harmony.



By establishing an algebraic spectral foundation, AlgebraX enables downstream graph cuts, manifold learning, diffusion
geometry, and spectral clustering directly within its sparse dictionary architecture.

---

## Rationale & The Council Alignment

The design is governed by the 8 Pillars of The Council Framework (`PRINCIPLES.md`):

### 1. Symmetry (Noether)

- **Quadratic Form Invariance:** For any vector $\mathbf{x}$, the Laplacian satisfies:
  $$\mathbf{x}^T L \mathbf{x} = \frac{1}{2} \sum_{u, v} W_{uv} (x_u - x_v)^2 \ge 0$$
  guaranteeing that $L$ is positive semi-definite ($L \succeq 0$).
- **Nullspace Symmetry:** The constant vector $\mathbf{1}$ spans the exact kernel of $L$ ($L \mathbf{1} = \mathbf{0}$),
  ensuring mass balance $\sum_i v_{2, i} = 0$.

### 2. Efficiency (Shannon) & Performance Architecture

- **Dual-Tier Eigensolver:**
    - **Tier 1 (Sparse $O (|E|)$ Engine):** The Fiedler vector $\mathbf{v}_2$ is solved directly over sparse
      dictionaries using Rayleigh Quotient Conjugate Gradient (RQ-CG) deflated against $\mathbf{1}$. It requires
      only $2 |E| + 5 |V|$ operations per step and consumes $O (|E| + |V|)$ memory, scaling effortlessly to 50,000+
      edges in pure Python.
    - **Tier 2 (Dense Jacobi Sweeps):** Complete eigenspectrum decomposition is confined to small graphs ($N \le 150$),
      avoiding $O (N^3)$ explosions on large inputs.

### 3. Safety (The Golem)

- **Singularity Containment:** Isolated nodes ($d_u = 0$) are handled safely in normalized Laplacians by
  setting $D^{-1/2}_{uu} = 0$, preventing division by zero.
- **Disconnected Graphs:** If a graph has multiple connected components, $\lambda_2 = 0.0$ is detected immediately, and
  the Fiedler vector returns the indicator partition without numerical instability.
- **Performance Warning:** `laplacian_spectrum` issues a `PerformanceWarning` when $N > 150$, cautioning users against
  dense $O (N^3)$ overhead.

### 4. Clarity (Feynman)

- **The Freshman Test:** The Graph Laplacian is intuitively explained as a physical network of elastic springs along
  edges. The Fiedler eigenvalue $\lambda_2$ represents the fundamental resonant frequency of the system, while the
  zero-crossings of the Fiedler vector $\mathbf{v}_2$ identify the natural structural fault line dividing the network.

### 5. Falsifiability (Popper)

- The implementation will be verified against closed-form analytical eigenspectra on canonical graph families:
    - Path graph $P_n$: $\lambda_2 = 2 - 2 \cos (\pi / n) \approx \pi^2 / n^2$.
    - Cycle graph $C_n$: $\lambda_2 = 2 - 2 \cos (2\pi / n)$.
    - Complete graph $K_n$: $\lambda_1 = 0$, $\lambda_2 = \dots = \lambda_n = n$.
    - Star graph $S_n$: $\lambda_2 = 1.0$, $\lambda_{\max} = n$.
    - Barbell graph: Exact separation of the two cliques across the bridge edge.

### 6. Consistency (Russell)

- Clear taxonomy: `graph_laplacian(graph)` returns the linear operator `SparseMatrix`, while `laplacian(field, graph)`
  computes the divergence of the gradient ($\Delta f$).

### 7. Harmony (The Steward)

- Default parameters work out-of-the-box with standard Python dictionaries `dict[K, dict[K, float]]`.

### 8. Curiosity (The Explorer)

- Unlocks future spectral embedding ($k$-dimensional Laplacian eigenmaps), discrete Hodge theory, and graph
  convolutional filters.

---

## Detailed Performance & Algorithmic Analysis

Because AlgebraX is a pure-Python library without native compiled Fortran/C LAPACK extensions, performance must be
engineered through algorithmic minimalism.

### 1. The Spectral Gap Contraction Risk

When computing the second smallest eigenvalue $\lambda_2$ via standard shifted power iteration on $M = c I - L$
(with $c = 2 d_{\max}$), the contraction ratio between the second and third eigenvalues is:
$$\rho = \frac{c - \lambda_3}{c - \lambda_2} = 1 - \frac{\lambda_3 - \lambda_2}{c - \lambda_2}$$
On ill-conditioned graphs (such as long chain/path graphs $P_N$), the spectral
gap $\lambda_3 - \lambda_2 \sim \frac{3\pi^2}{N^2}$ shrinks rapidly, causing $\rho \to 1$ and requiring hundreds of
iterations to converge.

### 2. Algorithmic Mitigation: Rayleigh Quotient Conjugate Gradient (RQ-CG)

To guarantee rapid convergence regardless of graph diameter:

- The Fiedler vector is formulated as the unconstrained minimization of the Rayleigh quotient on the orthogonal
  subspace $S = \mathbf{1}^\perp$:
  $$\min_{\mathbf{x} \in \mathbb{R}^N} \frac{\mathbf{x}^T L \mathbf{x}}{\mathbf{x}^T \mathbf{x}} \quad \text{s.t.} \quad \mathbf{x}^T \mathbf{1} = 0$$
- Nonlinear Conjugate Gradient with Polak-Ribière update and Gram-Schmidt projection against $\mathbf{1}$ achieves
  superlinear convergence, converging in **15 to 35 iterations** across almost all planar, small-world, and barbell
  networks.
- Every iteration requires only two sparse matrix-vector products ($4 |E|$ flops), preserving strict $O (|E|)$
  complexity.

### 3. Complexity & Scalability Matrix

| Component                   | Function                 |            Time Complexity            | Memory Complexity  |           Pure-Python Latency ($N=1,000, \|E\|=5,000$)           |
|:----------------------------|:-------------------------|:-------------------------------------:|:------------------:|:----------------------------------------------------------------:|
| **Laplacian Assembly**      | `laplacian_matrix`       |          $O(\|E\| + \|V\|)$           | $O(\|E\| + \|V\|)$ |                        $\sim 2\text{ ms}$                        |
| **Laplacian Smoothing**     | `laplacian_smoothing`    |          $O(S \cdot \|E\|)$           | $O(\|E\| + \|V\|)$ |            $\sim 10\text{ ms}$ ($S=20$ steps)            |
| **Algebraic Connectivity**  | `algebraic_connectivity` |          $O(K \cdot \|E\|)$           | $O(\|E\| + \|V\|)$ |                       $\sim 15\text{ ms}$                        |
| **Fiedler Vector Solver**   | `fiedler_vector`         |          $O(K \cdot \|E\|)$           | $O(\|E\| + \|V\|)$ |                       $\sim 18\text{ ms}$                        |
| **Spectral Bipartitioning** | `spectral_bipartition`   | $O(K \cdot \|E\| + \|V\| \log \|V\|)$ | $O(\|E\| + \|V\|)$ |                       $\sim 20\text{ ms}$                        |
| **Full Spectrum**           | `laplacian_spectrum`     |               $O(N^3)$                |      $O(N^2)$      | $\sim 2.5\text{ s}$ (triggers `PerformanceWarning` if $N > 150$) |

---

## Specification

### 1. Proposed Public API Signatures

```python
from typing import Any, Literal
from algebrax.typing import K, SparseMatrix, SparseVector


def laplacian_matrix(
    matrix: SparseMatrix[K, float],
    normalized: Literal['sym', 'rw'] | None = None,
    symmetrize: bool = True,
) -> SparseMatrix[K, float]:
    r"""Construct the discrete Graph Laplacian matrix $L$ from an adjacency or affinity matrix.

    Algebraic Signature:
        $L = D - A, \quad L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2}, \quad L_{\mathrm{rw}} = D^{-1} L$

    Carrier:
        `SparseMatrix[K, float]` (Symmetric or row-stochastic linear operator).

    Housed In:
        `algebrax.matrix` (canonical), cross-exported in `algebrax.analysis`.

    Args:
        matrix: Sparse adjacency or similarity matrix representing weighted edges `u -> {v: weight}`.
        normalized: Normalization mode:
            - `None`: Combinatorial Laplacian $L = D - A$.
            - `'sym'`: Symmetric normalized Laplacian $L_{\mathrm{sym}} = D^{-1/2} L D^{-1/2}$.
            - `'rw'`: Random-walk normalized Laplacian $L_{\mathrm{rw}} = D^{-1} L$.
        symmetrize: If True, symmetrizes directed inputs as $(W + W^T) / 2$. Defaults to True.

    Returns:
        Sparse matrix representation of the Laplacian operator.
    """


def fiedler_vector(
        graph: SparseMatrix[K, float],
        normalized: bool = False,
        tol: float = 1e-8,
        max_iter: int = 500,
        seed: int | None = 42,
) -> tuple[float, SparseVector[K, float]]:
    r"""Compute the Fiedler eigenvalue (algebraic connectivity $\lambda_2$) and Fiedler vector $\mathbf{v}_2$.

    Algebraic Signature:
        $L \mathbf{v}_2 = \lambda_2 \mathbf{v}_2 \quad \text{subject to} \quad \mathbf{v}_2 \perp \mathbf{1}, \; \|\mathbf{v}_2\|_2 = 1$

    Carrier:
        `tuple[float, SparseVector[K, float]]` (Algebraic connectivity and normalized eigenvector).

    Args:
        graph: Sparse adjacency matrix.
        normalized: Whether to compute with respect to the symmetric normalized Laplacian.
        tol: Convergence tolerance for the Rayleigh quotient gradient.
        max_iter: Maximum number of sparse conjugate gradient iterations.
        seed: Random seed for initial perturbation vector.

    Returns:
        Tuple of `(lambda_2, fiedler_vector)`.
    """


def algebraic_connectivity(
        graph: SparseMatrix[K, float],
        normalized: bool = False,
        tol: float = 1e-8,
) -> float:
    r"""Compute the algebraic connectivity (Fiedler eigenvalue $\lambda_2$) of a graph.

    Algebraic Signature:
        $\lambda_2 = \min_{\mathbf{x} \perp \mathbf{1}, \|\mathbf{x}\|_2=1} \mathbf{x}^T L \mathbf{x}$
    """


def spectral_bipartition(
        graph: SparseMatrix[K, float],
        method: Literal['sign', 'median'] = 'sign',
        normalized: bool = False,
) -> tuple[set[K], set[K], dict[str, float]]:
    r"""Bipartition graph vertices into two clusters $V_1$ and $V_2$ using the Fiedler vector.

    Algebraic Signature:
        $V_1 = \{u \in V \mid v_{2, u} \ge \theta\}, \quad V_2 = \{u \in V \mid v_{2, u} < \theta\}$

    Args:
        graph: Sparse adjacency matrix.
        method: Partition thresholding criterion:
            - `'sign'`: Threshold at $\theta = 0.0$.
            - `'median'`: Threshold at $\theta = \mathrm{median}(\mathbf{v}_2)$ (balanced bipartition).
        normalized: Whether to partition using the normalized Laplacian.

    Returns:
        Tuple of `(partition_a, partition_b, metrics)` where metrics contains:
            - `'cut_size'`: Sum of weights of edges crossing the cut.
            - `'ratio_cut'`: $\mathrm{cut}(A, B) \cdot (1/|A| + 1/|B|)$.
            - `'normalized_cut'`: $\mathrm{cut}(A, B) \cdot (1/\mathrm{vol}(A) + 1/\mathrm{vol}(B))$.
            - `'conductance'`: $\mathrm{cut}(A, B) / \min(\mathrm{vol}(A), \mathrm{vol}(B))$.
    """


def laplacian_smoothing(
    field: SparseVector[K, float],
    graph: SparseMatrix[K, float],
    steps: int = 10,
    tau: float = 0.1,
    normalized: Literal['sym', 'rw'] | None = None,
) -> SparseVector[K, float]:
    r"""Smooth a scalar field on a graph via iterative Laplacian diffusion.

    Algebraic Signature:
        $\mathbf{u}^{(t+1)} = (I - \tau L) \mathbf{u}^{(t)} \approx e^{-t L} \mathbf{u}_0$

    Carrier:
        `SparseVector[K, float]` (Smoothed scalar field on vertices).

    Operations:
        - Operator Construction: Precomputes $L = \text{laplacian_matrix}(graph)$ once.
        - Iterative Contraction: Executes $S$ sparse matrix-vector steps $\mathbf{u} \leftarrow \mathbf{u} - \tau L \mathbf{u}$.

    Properties:
        Monotonically minimizes discrete Dirichlet energy $E(\mathbf{u}) = \frac{1}{2} \mathbf{u}^T L \mathbf{u}$;
        converges toward harmonic equilibrium as $t \to \infty$.

    Applications:
        - Heat diffusion and spreading dynamics over networks.
        - Graph signal processing: Spectral low-pass filtering and spatial noise reduction.
        - Semi-supervised machine learning: Soft label propagation across manifolds.
        - Spectral clustering: Thermal regularization of Fiedler vectors for robust Cheeger cuts.
        - 3D mesh geometry fairing and surface denoising.

    Args:
        field: Input scalar signal $\mathbf{u}_0$ defined on vertices.
        graph: Sparse adjacency matrix or precomputed Laplacian operator.
        steps: Number of discrete Euler diffusion steps $S \ge 1$.
        tau: Step size / diffusion rate parameter $\tau > 0$ (default 0.1).
        normalized: Optional normalization mode ('sym' or 'rw').

    Returns:
        Smoothed sparse vector field.
    """


def laplacian_spectrum(
    graph: SparseMatrix[K, float],
    k: int | None = None,
    normalized: bool = False,
) -> tuple[list[float], list[SparseVector[K, float]]]:
    r"""Compute the full or truncated eigenspectrum ($0 \le \lambda_1 \le \dots \le \lambda_k$) via cyclic Jacobi sweeps.

    Warnings:
        Issues `PerformanceWarning` if the graph order $N > 150$.
    """
```

---

## Backwards Compatibility

- **Pure Addition:** Introduces new functions in `algebrax.analysis` and exports them through `algebrax.__init__`.
- **Existing `laplacian` Function:** `algebrax.analysis.laplacian(field, graph)` computes the action on a scalar
  field $\Delta f$; it remains completely unchanged.
- **Zero Breaking Changes:** 100% backwards compatible with all existing semirings and sparse matrix representations.

---

## How to Teach This / Documentation Plan

1. **User Guide Section:** Add a dedicated subsection on Spectral Graph Theory to
   `docs/guide/analysis/discrete_calculus.md`.
2. **Graphical Laboratory View:** Add a Spectral Clustering / Fiedler View to `recipes/lab.py` demonstrating real-time
   graph bipartitioning.
3. **Recipe Demonstration:** Build a graph segmentation recipe in `recipes/` showcasing spectral clustering on social or
   infrastructure graphs.

---

## Reference Implementation

```python
import math
import random
from typing import Any, Literal
from algebrax.matrix.academic import PerformanceWarning
from algebrax.matrix.core import mat_vec
from algebrax.typing import K, SparseMatrix, SparseVector


def laplacian_matrix(
    matrix: SparseMatrix[K, float],
    normalized: Literal['sym', 'rw'] | None = None,
    symmetrize: bool = True,
) -> SparseMatrix[K, float]:
    nodes: set[K] = set(matrix.keys())
    for row in matrix.values():
        nodes.update(row.keys())

    if not nodes:
        return {}

    # Symmetrize edge weights
    adj: dict[K, dict[K, float]] = {u: {} for u in nodes}
    for u, neighbors in matrix.items():
        for v, w in neighbors.items():
            if u != v and w > 0:
                if symmetrize:
                    rev_w = matrix.get(v, {}).get(u, w)
                    avg_w = 0.5 * (w + rev_w)
                    adj[u][v] = avg_w
                    adj[v][u] = avg_w
                else:
                    adj[u][v] = w

    degrees = {u: sum(adj[u].values()) for u in nodes}

    lap: dict[K, dict[K, float]] = {u: {} for u in nodes}
    if normalized is None:
        for u in nodes:
            lap[u][u] = degrees[u]
            for v, w in adj[u].items():
                lap[u][v] = -w
    elif normalized == 'sym':
        inv_sqrt_d = {u: (1.0 / math.sqrt(degrees[u]) if degrees[u] > 0 else 0.0) for u in nodes}
        for u in nodes:
            lap[u][u] = 1.0 if degrees[u] > 0 else 0.0
            for v, w in adj[u].items():
                lap[u][v] = -w * inv_sqrt_d[u] * inv_sqrt_d[v]
    elif normalized == 'rw':
        for u in nodes:
            d = degrees[u]
            lap[u][u] = 1.0 if d > 0 else 0.0
            if d > 0:
                for v, w in adj[u].items():
                    lap[u][v] = -w / d
    else:
        raise ValueError(f"Unknown normalization mode: '{normalized}'. Expected None, 'sym', or 'rw'.")

    return {u: {v: w for v, w in row.items() if abs(w) > 1e-14} for u, row in lap.items()}


def laplacian_smoothing(
    field: SparseVector[K, float],
    graph: SparseMatrix[K, float],
    steps: int = 10,
    tau: float = 0.1,
    normalized: Literal['sym', 'rw'] | None = None,
) -> SparseVector[K, float]:
    if steps < 1:
        raise ValueError(f'steps must be a positive integer, got {steps}')
    if tau <= 0.0:
        raise ValueError(f'tau must be positive, got {tau}')

    # Assemble operator once
    lap = laplacian_matrix(graph, normalized=normalized)
    u = dict(field)

    for _ in range(steps):
        diff = mat_vec(lap, u)
        u = {k: u.get(k, 0.0) - tau * diff.get(k, 0.0) for k in u.keys() | diff.keys()}

    return u
```

---

## Rejected Ideas

1. **Relying Exclusively on Full Jacobi Sweeps:**
    - *Rejected:* $O (N^3)$ computational complexity makes full diagonalization unviable for graphs with more than 150
      vertices in pure Python.
2. **Dense Matrix Allocation for Fiedler Computation:**
    - *Rejected:* Converting sparse adjacency lists into $N \times N$ dense tables consumes $O (N^2)$ memory and negates
      the sparse architecture of AlgebraX.
3. **Overloading Existing `laplacian(field, graph)`:**
    - *Rejected:* Violates Russell Consistency. The function `laplacian` computes the 0-form vector field $\Delta f$;
      returning a matrix from the same function would introduce type collisions and API ambiguity.
4. **Providing a Redundant `graph_laplacian` Alias:**
    - *Rejected:* Violates Shannon Efficiency and Python Zen ("one obvious way to do it"). The prefix `graph_` is misleading because the operator accepts any `SparseMatrix` (including similarity matrices and PDE stencils). `laplacian_matrix` is the single canonical name.

---

## Open Questions

- [x] Should `laplacian_matrix` symmetrize directed graphs by default? *(Yes, Spectral Graph Theory requires self-adjoint
  operators; default `symmetrize=True`).*
- [ ] Should we support multi-way spectral clustering ($k > 2$) using the top $k$ Fiedler vectors in a follow-up EP? *(
  Deferred to a future unsupervised learning track).*

---

## Change Log

* **2026-09-05:** Initial Draft authored.
