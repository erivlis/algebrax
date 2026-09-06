"""
Analyze edge curvature via discrete combinatorics. Supports weighted and unweighted
graphs, with optional augmentation based on triangle contributions.

This method abstracts curvature calculation for both weighted and unweighted
graphs. It captures the notion of Ricci curvature locally, reflecting flow
expansion/contraction by considering topological or geometrical graph features.

Args:
    graph (SparseMatrix): Representation of the graph structure where edges are
        stored using a sparse matrix format/mapping.
    weighted (bool | None): Whether to compute weighted Forman-Ricci curvature.
        Defaults to None, which determines weighting based on edge properties:
            - True: Use weights explicitly.
            - False: Assume unweighted graph (1 for all edges).
    augmented (bool): Whether to include triangle-based adjustments in the
        curvature calculation. Defaults to True. Relevant for both weighted
        and unweighted variants, boosting edges shared in small cliques.

Returns:
    dict[tuple[K, K], float]: Dictionary where keys are edge pairs (u, v) and
        values are their computed Forman-Ricci curvature values.
"""

import math
import random
import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Literal

from algebrax.matrix.academic import PerformanceWarning
from algebrax.matrix.core import laplacian_matrix, mat_vec, vec_mat
from algebrax.semiring import Semiring
from algebrax.typing import K, SparseMatrix, SparseVector

__all__ = [
    'algebraic_connectivity',
    'divergence',
    'eigen_centrality',
    'fiedler_vector',
    'forman_ricci_curvature',
    'gaussian_kernel',
    'gradient',
    'laplacian',
    'laplacian_matrix',
    'laplacian_smoothing',
    'laplacian_spectrum',
    'pagerank',
    'spectral_bipartition',
]


def divergence(flow: SparseMatrix) -> SparseVector:
    """
    Compute the discrete divergence of a 1-form (flow/edge signals).
    Maps edges (matrix) to nodes (vector).
    div(F)_i = sum_j (F_ij)

    This corresponds to the adjoint of the gradient (d*).

    Args:
        flow: A matrix representing flow between nodes.
              Positive F_ij implies flow from i to j.
              (Note: Convention varies, sometimes it's net flow *out*).

    Returns:
        A vector representing the net flow out of each node.
    """
    result = defaultdict(int)
    for u, neighbors in flow.items():
        for v, val in neighbors.items():
            # Flow u -> v counts as positive divergence for u
            result[u] += val
            # And negative divergence for v (if the matrix is not skew-symmetric stored)
            # If the matrix is fully stored (both u->v and v->u), we just sum rows.
            # If it's sparse/upper-triangular, we need to handle the other side.
            # Let's assume the matrix represents the 1-form fully or we treat it as directed.
            # Standard divergence is row_sum - col_sum?
            # If F is skew-symmetric (F_ij = -F_ji), then row_sum is sufficient.
            # If F is just weights, we usually define div at i as sum(w_ij) - sum(w_ji).
            result[v] -= val

    return dict(result)


def _is_graph_weighted(graph: SparseMatrix) -> bool:
    for neighbors in graph.values():
        for w in neighbors.values():
            if not math.isclose(w, 1.0):
                return True
    return False


def _get_common_neighbors(graph: SparseMatrix, node_a: K, node_b: K) -> set[K]:
    if node_a not in graph or node_b not in graph:
        return set()
    return set(graph[node_a].keys()) & set(graph[node_b].keys())


def _adjacent_sum(neighbors: Mapping[K, float], exclude_node: K, w_e: float, w_node: float) -> float:
    total = 0.0
    for z, w_edge in neighbors.items():
        if z != exclude_node:
            denom = math.sqrt(w_e * w_edge)
            if denom > 0:
                total += w_node / denom
    return total


def _unweighted_forman_ricci(
    graph: SparseMatrix,
    degrees: dict[K, int],
    augmented: bool,
) -> dict[tuple[K, K], float]:
    curvature = {}
    for u, neighbors in graph.items():
        for v in neighbors:
            try:
                should_process = u < v
            except TypeError:
                should_process = id(u) < id(v)

            if not should_process:
                continue

            deg_u = degrees.get(u, 0)
            deg_v = degrees.get(v, 0)
            k = 4.0 - deg_u - deg_v
            if augmented:
                k += 3.0 * len(_get_common_neighbors(graph, u, v))
            curvature[(u, v)] = float(k)
    return curvature


def _weighted_forman_ricci(
    graph: SparseMatrix,
    strengths: dict[K, float],
    augmented: bool,
) -> dict[tuple[K, K], float]:
    curvature = {}
    for u, neighbors in graph.items():
        for v, w_uv in neighbors.items():
            try:
                should_process = u < v
            except TypeError:
                should_process = id(u) < id(v)

            if not should_process:
                continue

            w_e = w_uv
            if w_e == 0:  # NOSONAR - exact zero denominator singularity check
                curvature[(u, v)] = 0.0
                continue

            w_u = strengths.get(u, 0.0)
            w_v = strengths.get(v, 0.0)

            sum_u = _adjacent_sum(graph[u], v, w_e, w_u)
            sum_v = _adjacent_sum(graph[v], u, w_e, w_v)

            k = w_e * ((w_u / w_e) + (w_v / w_e) - sum_u - sum_v)

            if augmented:
                tri_contrib = 0.0
                for w in _get_common_neighbors(graph, u, v):
                    w_vw = graph[v][w]
                    w_wu = graph[w][u]
                    w_f = (w_e * w_vw * w_wu) ** (1 / 3)
                    if w_f > 0:
                        tri_contrib += w_e / w_f
                k += 3.0 * tri_contrib

            curvature[(u, v)] = float(k)
    return curvature


def forman_ricci_curvature(
    graph: SparseMatrix,
    weighted: bool | None = None,
    augmented: bool = True,
) -> dict[tuple[K, K], float]:
    """
    Compute the Forman-Ricci Curvature for edges in a graph.

    Forman-Ricci Curvature (FRC) is a discrete combinatorial analog of the Ricci
    curvature on Riemannian manifolds. It measures the local divergence or cohesion
    of flows along edges.

    For an undirected edge e = (u, v) in an unweighted graph:
    - 1D FRC: F(e) = 4 - deg(u) - deg(v)
    - Augmented FRC (incorporating triangles): F(e) = 4 - deg(u) - deg(v) + 3 * tri(e)

    For a weighted graph (Sreejith et al. formulation):
    - F(e) = w_e * (w_u/w_e + w_v/w_e - sum_{e' ~ u} w_u/sqrt(w_e * w_e') - sum_{e' ~ v} w_v/sqrt(w_e * w_e'))
      where node weights w_u and w_v default to node strengths (weighted degree).
    - Augmented FRC: F_weighted_1D(e) + 3 * sum_{f > e} w_e / w_f
      where the weight of a triangle face f = (u, v, w) is the geometric mean of its edge weights.

    Args:
        graph: Adjacency matrix (weighted or unweighted).
        weighted: Whether to compute weighted curvature. If None, automatically detected
                  based on whether any edge weights differ from 1.
        augmented: Whether to include 2D triangle contributions (default is True).

    Returns:
        A dictionary mapping edges (u, v) (with u < v) to their curvature values.
    """
    if weighted is None:
        weighted = _is_graph_weighted(graph)

    if not weighted:
        degrees = {u: len(neighbors) for u, neighbors in graph.items()}
        return _unweighted_forman_ricci(graph, degrees, augmented)
    else:
        strengths = {u: sum(neighbors.values()) for u, neighbors in graph.items()}
        return _weighted_forman_ricci(graph, strengths, augmented)


def gaussian_kernel(distance_matrix: SparseMatrix, sigma: float = 1.0, threshold: float = 1e-6) -> SparseMatrix:
    """
    Compute the Gaussian (RBF) kernel from a distance matrix.
    K_ij = exp(-d_ij^2 / (2 * sigma^2))

    This transforms a distance metric into a similarity (adjacency) matrix,
    often used for spectral clustering or diffusion maps.

    Args:
        distance_matrix: A sparse matrix of distances between nodes.
        sigma: The bandwidth parameter (standard deviation).
        threshold: Minimum value to retain in the sparse output.

    Returns:
        A sparse similarity matrix.
    """
    result = {}
    denom = 2 * sigma * sigma

    for u, neighbors in distance_matrix.items():
        row = {}
        for v, dist in neighbors.items():
            val = math.exp(-(dist * dist) / denom)
            if val > threshold:
                row[v] = val
        if row:
            result[u] = row

    return result


def gradient(field: SparseVector, graph: Mapping[K, Iterable[K]]) -> SparseMatrix:
    """
    Compute the discrete gradient (exterior derivative d0) of a 0-form (node signals).
    Maps nodes (vector) to edges (matrix).
    grad(f)_ij = f(j) - f(i)

    Args:
        field: A vector of values at nodes.
        graph: Adjacency list defining the edges (topology).

    Returns:
        A matrix (1-form) representing the gradient along edges.
    """
    result = {}
    for u, neighbors in graph.items():
        if u not in field:
            continue

        val_u = field[u]
        row = {}
        for v in neighbors:
            if v in field:
                # d f(u, v) = f(v) - f(u)
                row[v] = field[v] - val_u

        if row:
            result[u] = row
    return result


def laplacian(field: SparseVector, graph: SparseMatrix) -> SparseVector:
    """
    Compute the combinatorial Laplacian of a scalar field.
    L = D - A (for unweighted) or L f = div(grad f).

    Delta f_i = sum_{j ~ i} w_ij * (f_i - f_j)

    Args:
        field: A vector of values at nodes.
        graph: Adjacency matrix (weighted).

    Returns:
        A vector representing the Laplacian at each node.
    """
    # L = div(grad(f))
    # But calculating grad then div is expensive (creates intermediate matrix).
    # Direct calculation:
    result = defaultdict(int)

    for u, neighbors in graph.items():
        if u not in field:
            continue

        val_u = field[u]
        # Degree (weighted)
        # For standard Laplacian, we sum w_ij * (f_u - f_v)

        local_sum = 0
        for v, weight in neighbors.items():
            if v in field:
                diff = val_u - field[v]
                local_sum += weight * diff

        if local_sum != 0:
            result[u] = local_sum

    return dict(result)


def _normalize_distribution_vector(
    vec: SparseVector[K, float] | None,
    nodes: set[K],
    name: str,
) -> dict[K, float]:
    num_nodes = len(nodes)
    if vec is None:
        return dict.fromkeys(nodes, 1.0 / num_nodes)

    for k, v in vec.items():
        if v < 0.0:
            raise ValueError(f'{name} values must be non-negative, got {v} for key {k}')

    total_mass = sum(vec.values())
    if total_mass <= 0.0:
        raise ValueError(f'{name} vector must have a positive sum')

    return {k: vec.get(k, 0.0) / total_mass for k in nodes}


def _build_transition_matrix(
    graph: SparseMatrix[K, float],
    nodes: set[K],
) -> tuple[SparseMatrix[K, float], set[K]]:
    trans_matrix: SparseMatrix[K, float] = {}
    dangling_nodes: set[K] = set()

    for u in nodes:
        row = graph.get(u, {})
        row_sum = sum(w for w in row.values() if w > 0.0)
        if row_sum > 0.0:
            trans_matrix[u] = {v: w / row_sum for v, w in row.items() if w > 0.0}
        else:
            dangling_nodes.add(u)

    return trans_matrix, dangling_nodes


def pagerank(
    graph: SparseMatrix[K, float],
    damping: float = 0.85,
    personalization: SparseVector[K, float] | None = None,
    semiring: Semiring[float] | type[Semiring[float]] | None = None,
    max_iter: int = 100,
    tol: float = 1e-6,
    dangling: SparseVector[K, float] | None = None,
) -> SparseVector[K, float]:
    r"""Compute algebraic PageRank / Random Walk with Restart over a semiring.

    Algebraic Signature:
        $\mathbf{p}^{(t+1)} = (\alpha \otimes \mathbf{p}^{(t)} \mathbf{P}) \oplus ((1 - \alpha) \otimes \mathbf{v})$

    Carrier:
        `SparseVector[K, float]` (Mapping from vertex identifier to centrality probability).

    Operations:
        - Out-Degree Normalization: Row-stochastic projection $P_{ij} = W_{ij} / \sum_k W_{ik}$.
        - Dangling Mass Redistribution: Scalar aggregation of dead-end probability mass.
        - Power Iteration Contraction: Iterative sparse vector-matrix contraction.

    Properties:
        Conserves total probability mass ($\sum_u p_u = 1.0$); geometrically convergent
        with contraction factor $\alpha$.

    Applications:
        Web page ranking, entity resolution, protein-protein interaction networks,
        personalized recommendation subgraphs, fraud detection.

    Args:
        graph: Sparse adjacency matrix representing directed weighted edges `u -> {v: weight}`.
        damping: Random walk continuation probability $\alpha \in [0, 1]$ (default 0.85).
        personalization: Teleportation restart probability vector $\mathbf{v}$ (default uniform).
        semiring: Semiring instance or class used for vector-matrix multiplication (default StandardSemiring).
        max_iter: Maximum number of power iterations (default 100).
        tol: Convergence tolerance under L1 norm (default 1e-6).
        dangling: Probability distribution for redistributing mass from sink vertices (default equals personalization).

    Returns:
        Sparse vector mapping each vertex identifier to its PageRank score.

    Raises:
        ValueError: If damping is not in [0, 1], max_iter < 1, tol < 0, or
            personalization/dangling has non-positive sum.

    Example:
        >>> g = {'a': {'b': 1.0}, 'b': {'a': 1.0}}
        >>> pr = pagerank(g)
        >>> round(pr['a'], 2), round(pr['b'], 2)
        (0.5, 0.5)
    """
    if not 0.0 <= damping <= 1.0:
        raise ValueError(f'damping must be between 0.0 and 1.0, got {damping}')
    if max_iter < 1:
        raise ValueError(f'max_iter must be a positive integer, got {max_iter}')
    if tol < 0.0:
        raise ValueError(f'tol must be non-negative, got {tol}')

    nodes: set[K] = set(graph.keys())
    for row in graph.values():
        nodes.update(row.keys())

    if personalization:
        nodes.update(personalization.keys())
    if dangling:
        nodes.update(dangling.keys())

    if not nodes:
        return {}
    if len(nodes) == 1:
        return {next(iter(nodes)): 1.0}

    p_vec = _normalize_distribution_vector(personalization, nodes, 'Personalization')
    if damping == 0.0:  # NOSONAR - exact boundary check for pure restart distribution
        return dict(p_vec)

    d_vec = p_vec if dangling is None else _normalize_distribution_vector(dangling, nodes, 'Dangling')
    trans_matrix, dangling_nodes = _build_transition_matrix(graph, nodes)
    sem = Semiring.normalize(semiring)

    rank: dict[K, float] = dict(p_vec)
    one_minus_alpha = 1.0 - damping

    for _ in range(max_iter):
        dangling_mass = sum(rank.get(u, 0.0) for u in dangling_nodes)
        next_rank = vec_mat(rank, trans_matrix, semiring=sem)

        dangling_term = damping * dangling_mass
        total_err = 0.0
        updated_rank: dict[K, float] = {}

        for u in nodes:
            walk_val = damping * next_rank.get(u, 0.0)
            restart_val = one_minus_alpha * p_vec.get(u, 0.0) + dangling_term * d_vec.get(u, 0.0)
            val = walk_val + restart_val
            updated_rank[u] = val
            total_err += abs(val - rank.get(u, 0.0))

        rank = updated_rank
        if total_err < tol:
            break

    return rank


def eigen_centrality(
    matrix: SparseMatrix[K, float],
    iterations: int = 100,
    tolerance: float = 1e-6,
) -> SparseVector[K, float]:
    r"""Compute the eigenvector centrality (principal eigenvector) using the Power Iteration method.

    Algebraic Signature:
        $\lambda_1 \mathbf{x} = \mathbf{A} \mathbf{x} \implies$
        $\mathbf{x}^{(t+1)} = \mathbf{A} \mathbf{x}^{(t)} / \|\mathbf{A} \mathbf{x}^{(t)}\|_2$

    Carrier:
        `SparseVector[K, float]` (Mapping from vertex identifier to normalized centrality score).

    Operations:
        - Power Iteration: Repeatedly applies matrix-vector product $\mathbf{x} \leftarrow \mathbf{A} \mathbf{x}$.
        - Euclidean Normalization: Enforces $\|\mathbf{x}\|_2 = 1.0$ at each step for numerical stability.
        - Convergence Check: Terminates when $\|\mathbf{x}^{(t+1)} - \mathbf{x}^{(t)}\|_1 < \text{tolerance}$.

    Properties:
        By the Perron-Frobenius theorem, for a connected graph with non-negative adjacency
        matrix $\mathbf{A}$, the principal eigenvector is unique, positive, and corresponds
        to the spectral radius $\lambda_{\max}(\mathbf{A})$.

    Applications:
        - Structural node ranking in undirected social, citation, and communication networks.
        - Financial systemic risk: Asset interconnectedness and centrality on correlation matrices.
        - Bipartite ranking: Dominant hub-and-authority scoring without restart damping.

    Args:
        matrix: Square non-negative adjacency or correlation matrix.
        iterations: Maximum number of power iteration steps (default 100).
        tolerance: L1 convergence threshold for stopping early (default 1e-6).

    Returns:
        Normalized `SparseVector[K, float]` representing the principal eigenvector centrality.
    """
    nodes = set(matrix.keys()) | {k for row in matrix.values() for k in row}
    n = len(nodes)
    if n == 0:
        return {}

    vector: SparseVector[K, float] = dict.fromkeys(nodes, 1.0 / n)

    for _ in range(iterations):
        new_vector = mat_vec(matrix, vector)

        norm = math.sqrt(sum(x * x for x in new_vector.values()))
        if norm == 0:  # NOSONAR - exact zero denominator singularity check
            return vector  # Matrix is likely zero

        new_vector = {k: v / norm for k, v in new_vector.items()}

        diff = sum(abs(new_vector.get(k, 0.0) - vector.get(k, 0.0)) for k in nodes)
        vector = new_vector
        if diff < tolerance:
            break

    return vector


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
        - Iterative Contraction: Executes $S$ sparse matrix-vector steps
          $\mathbf{u} \leftarrow \mathbf{u} - \tau L \mathbf{u}$.

    Properties:
        Monotonically minimizes discrete Dirichlet energy $E(\mathbf{u}) = \frac{1}{2} \mathbf{u}^T L \mathbf{u}$;
        converges toward harmonic equilibrium as $t \to \infty$.

    Applications:
        - Heat diffusion and spreading dynamics over physical/information networks.
        - Graph signal processing: Spectral low-pass filtering and spatial noise reduction.
        - Semi-supervised learning: Soft label propagation and belief spreading across manifolds.
        - Spectral clustering: Thermal regularization of Fiedler vectors for Cheeger cuts.
        - Computational geometry: 3D mesh surface fairing, smoothing, and denoising.

    Args:
        field: Input scalar signal $\mathbf{u}_0$ defined on vertices.
        graph: Sparse adjacency matrix or precomputed Laplacian operator.
        steps: Number of discrete Euler diffusion steps $S \ge 1$.
        tau: Step size / diffusion rate parameter $\tau > 0$ (default 0.1).
        normalized: Optional normalization mode ('sym' or 'rw').

    Returns:
        Smoothed sparse vector field.
    """
    if steps < 1:
        raise ValueError(f'steps must be a positive integer, got {steps}')
    if tau <= 0.0:
        raise ValueError(f'tau must be positive, got {tau}')

    is_already_lap = any(w < 0 for row in graph.values() for w in row.values())
    lap = graph if is_already_lap else laplacian_matrix(graph, normalized=normalized)

    u = dict(field)
    for _ in range(steps):
        diff = mat_vec(lap, u)
        all_keys = u.keys() | diff.keys()
        u = {k: u.get(k, 0.0) - tau * diff.get(k, 0.0) for k in all_keys}

    return {k: v for k, v in u.items() if abs(v) > 1e-14}


def fiedler_vector(  # NOSONAR - numerical Rayleigh quotient iteration and deflation kernel
    graph: SparseMatrix[K, float],
    normalized: bool = False,
    tol: float = 1e-8,
    max_iter: int = 500,
    seed: int | None = 42,
) -> tuple[float, SparseVector[K, float]]:
    r"""Compute the Fiedler eigenvalue (algebraic connectivity $\lambda_2$) and Fiedler vector $\mathbf{v}_2$.

    Algebraic Signature:
        $L \mathbf{v}_2 = \lambda_2 \mathbf{v}_2$ subject to
        $\mathbf{v}_2 \perp \mathbf{1}, \; \|\mathbf{v}_2\|_2 = 1$

    Carrier:
        `tuple[float, SparseVector[K, float]]` (Algebraic connectivity and normalized eigenvector).

    Operations:
        - RQ-CG Minimization: Solves
          $\min_{\mathbf{x} \perp \mathbf{1}, \|\mathbf{x}\|=1}
          \frac{\mathbf{x}^T L \mathbf{x}}{\mathbf{x}^T \mathbf{x}}$
          via Rayleigh Quotient Conjugate Gradient with closed-form 2D Givens angle optimization.

    Properties:
        $\lambda_2 > 0$ if and only if the graph is connected.
        The zero-level crossings of $\mathbf{v}_2$ approximate the optimal Cheeger conductance cut.

    Applications:
        - Spectral graph partitioning and community detection.
        - Algebraic connectivity and network robustness analysis.
        - Graph embedding and layout visualization.

    Args:
        graph: Sparse adjacency matrix.
        normalized: Whether to compute with respect to the symmetric normalized Laplacian.
        tol: Convergence tolerance for the Rayleigh quotient gradient.
        max_iter: Maximum number of sparse conjugate gradient iterations.
        seed: Random seed for initial perturbation vector.

    Returns:
        Tuple of `(lambda_2, fiedler_vector)`.
    """
    nodes = sorted(set(graph.keys()) | {v for row in graph.values() for v in row}, key=str)
    n = len(nodes)
    if n == 0:
        return 0.0, {}
    if n == 1:
        return 0.0, {nodes[0]: 0.0}

    # Detect connected components via BFS to handle disconnected graphs safely
    visited: set[K] = set()
    components: list[list[K]] = []
    for node in nodes:
        if node not in visited:
            comp: list[K] = []
            queue = [node]
            visited.add(node)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor, w in graph.get(curr, {}).items():
                    if w != 0 and neighbor in nodes and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(comp)

    if len(components) > 1:
        c1 = set(components[0])
        n1 = len(c1)
        n2 = n - n1
        val_c1 = math.sqrt(n2 / (n1 * n))
        val_c2 = -math.sqrt(n1 / (n2 * n))
        fiedler = {u: (val_c1 if u in c1 else val_c2) for u in nodes}
        return 0.0, fiedler

    lap = laplacian_matrix(graph, normalized='sym' if normalized else None)

    degrees = {u: sum(w for v, w in graph.get(u, {}).items() if u != v and w > 0) for u in nodes}
    z0 = {u: math.sqrt(max(degrees.get(u, 0.0), 1e-12)) for u in nodes} if normalized else dict.fromkeys(nodes, 1.0)

    norm_z0 = math.sqrt(sum(v * v for v in z0.values()))
    e0 = {u: z0[u] / norm_z0 for u in nodes}

    if n == 2:
        u, v = nodes
        x = {u: 1.0 / math.sqrt(2.0), v: -1.0 / math.sqrt(2.0)}
        lx = mat_vec(lap, x)
        lam2 = sum(x[k] * lx.get(k, 0.0) for k in nodes)
        return max(0.0, float(lam2)), x

    rng = random.Random(seed)
    x = {u: rng.gauss(0.0, 1.0) for u in nodes}

    # Project x perp e0 and normalize
    dot_e0 = sum(x[u] * e0[u] for u in nodes)
    x = {u: x[u] - dot_e0 * e0[u] for u in nodes}
    norm_x = math.sqrt(sum(v * v for v in x.values()))
    x = {u: x[u] / norm_x for u in nodes}

    lx = mat_vec(lap, x)
    lam = sum(x[u] * lx.get(u, 0.0) for u in nodes)

    g_prev: dict[K, float] | None = None
    p_dir: dict[K, float] | None = None

    for _ in range(max_iter):
        g = {u: lx.get(u, 0.0) - lam * x[u] for u in nodes}
        dot_g_e0 = sum(g[u] * e0[u] for u in nodes)
        g = {u: g[u] - dot_g_e0 * e0[u] for u in nodes}
        norm_g = math.sqrt(sum(v * v for v in g.values()))

        if norm_g < tol:
            break

        if g_prev is None or p_dir is None:
            p = {u: -g[u] for u in nodes}
        else:
            norm_g_prev_sq = sum(v * v for v in g_prev.values())
            if norm_g_prev_sq > 1e-18:
                beta = sum(g[u] * (g[u] - g_prev[u]) for u in nodes) / norm_g_prev_sq
                beta = max(0.0, beta)
            else:
                beta = 0.0
            p = {u: -g[u] + beta * p_dir[u] for u in nodes}

        # Project p perp e0 and perp x
        dot_p_e0 = sum(p[u] * e0[u] for u in nodes)
        p = {u: p[u] - dot_p_e0 * e0[u] for u in nodes}
        dot_p_x = sum(p[u] * x[u] for u in nodes)
        p = {u: p[u] - dot_p_x * x[u] for u in nodes}

        norm_p = math.sqrt(sum(v * v for v in p.values()))
        if norm_p < 1e-14:
            p = {u: -g[u] for u in nodes}
            dot_p_e0 = sum(p[u] * e0[u] for u in nodes)
            p = {u: p[u] - dot_p_e0 * e0[u] for u in nodes}
            dot_p_x = sum(p[u] * x[u] for u in nodes)
            p = {u: p[u] - dot_p_x * x[u] for u in nodes}
            norm_p = math.sqrt(sum(v * v for v in p.values()))
            if norm_p < 1e-14:
                break

        p = {u: p[u] / norm_p for u in nodes}
        lp = mat_vec(lap, p)

        a = lam
        b = sum(x[u] * lp.get(u, 0.0) for u in nodes)
        c = sum(p[u] * lp.get(u, 0.0) for u in nodes)

        theta = 0.5 * math.atan2(-2.0 * b, -(a - c))
        cos_t = math.cos(theta)
        sin_t = math.sin(theta)

        x_new = {u: cos_t * x[u] + sin_t * p[u] for u in nodes}
        dot_x_e0 = sum(x_new[u] * e0[u] for u in nodes)
        x_new = {u: x_new[u] - dot_x_e0 * e0[u] for u in nodes}
        norm_x_new = math.sqrt(sum(v * v for v in x_new.values()))
        x = {u: x_new[u] / norm_x_new for u in nodes}

        lx = mat_vec(lap, x)
        lam = sum(x[u] * lx.get(u, 0.0) for u in nodes)

        g_prev = g
        p_dir = p

    # Deterministic sign orientation: component with largest magnitude is positive
    max_k = max(x.keys(), key=lambda k: abs(x[k]))
    if x[max_k] < 0:
        x = {k: -v for k, v in x.items()}

    return max(0.0, float(lam)), x


def algebraic_connectivity(
    graph: SparseMatrix[K, float],
    normalized: bool = False,
    tol: float = 1e-8,
) -> float:
    r"""Compute the algebraic connectivity (Fiedler eigenvalue $\lambda_2$) of a graph.

    Algebraic Signature:
        $\lambda_2 = \min_{\mathbf{x} \perp \mathbf{1}, \|\mathbf{x}\|_2=1} \mathbf{x}^T L \mathbf{x}$

    Carrier:
        `float` (Second smallest eigenvalue of the graph Laplacian).

    Properties:
        $\lambda_2 = 0$ if and only if the graph has $\ge 2$ connected components.
        Bounds graph conductance via Cheeger's inequality: $\frac{\lambda_2}{2} \le h(G) \le \sqrt{2 \lambda_2}$.

    Applications:
        - Quantifying network synchronizability, bottleneck severity, and structural resilience.
        - Lower bounding node and edge connectivity.

    Args:
        graph: Sparse adjacency matrix.
        normalized: Whether to compute with respect to the symmetric normalized Laplacian.
        tol: Convergence tolerance for the solver.

    Returns:
        Algebraic connectivity $\lambda_2 \ge 0$.
    """
    lam2, _ = fiedler_vector(graph, normalized=normalized, tol=tol)
    return lam2


def spectral_bipartition(
    graph: SparseMatrix[K, float],
    method: Literal['sign', 'median'] = 'sign',
    normalized: bool = False,
) -> tuple[set[K], set[K], dict[str, float]]:
    r"""Bipartition graph vertices into two clusters $V_1$ and $V_2$ using the Fiedler vector.

    Algebraic Signature:
        $V_1 = \{u \in V \mid v_{2, u} \ge \theta\}, \quad V_2 = \{u \in V \mid v_{2, u} < \theta\}$

    Carrier:
        `tuple[set[K], set[K], dict[str, float]]` (Two vertex sets and cut quality metrics).

    Operations:
        - Eigensolving: Computes Fiedler vector $\mathbf{v}_2$.
        - Thresholding: Splits vertices using sign ($\theta = 0$) or median ($\theta = \mathrm{median}(\mathbf{v}_2)$).
        - Quality Assessment: Measures cut size, ratio cut, normalized cut, and conductance.

    Properties:
        Provides an approximation guarantee to the NP-hard Min-Cut / Sparsest Cut problem via Cheeger's inequality.

    Applications:
        - Unsupervised community detection and social network clustering.
        - Distributed computing domain decomposition and load balancing.
        - Image segmentation and computer vision graph cuts.

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
    if method not in ('sign', 'median'):
        raise ValueError(f"method must be 'sign' or 'median', got '{method}'")

    nodes = sorted(set(graph.keys()) | {v for row in graph.values() for v in row}, key=str)
    n = len(nodes)
    if n <= 1:
        return set(nodes), set(), {'cut_size': 0.0, 'ratio_cut': 0.0, 'normalized_cut': 0.0, 'conductance': 0.0}

    _, fiedler = fiedler_vector(graph, normalized=normalized)

    if method == 'median':
        sorted_vals = sorted(fiedler[u] for u in nodes)
        theta = sorted_vals[n // 2]
        v1 = {u for u in nodes if fiedler[u] >= theta}
        v2 = {u for u in nodes if fiedler[u] < theta}
    else:
        v1 = {u for u in nodes if fiedler[u] >= 0.0}
        v2 = {u for u in nodes if fiedler[u] < 0.0}

    # Ensure non-empty partitions if n >= 2
    if not v1 or not v2:
        sorted_nodes = sorted(nodes, key=lambda u: fiedler[u])
        mid = max(1, n // 2)
        v1 = set(sorted_nodes[:mid])
        v2 = set(sorted_nodes[mid:])

    # Compute cut metrics
    cut_size = 0.0
    for u in v1:
        for v, w in graph.get(u, {}).items():
            if v in v2:
                rev_w = graph.get(v, {}).get(u, w)
                cut_size += 0.5 * (float(w) + float(rev_w))

    degrees = {
        u: sum(0.5 * (float(w) + float(graph.get(v, {}).get(u, w))) for v, w in graph.get(u, {}).items() if u != v)
        for u in nodes
    }
    vol_1 = sum(degrees.get(u, 0.0) for u in v1)
    vol_2 = sum(degrees.get(u, 0.0) for u in v2)

    ratio_cut = cut_size * (1.0 / len(v1) + 1.0 / len(v2)) if (v1 and v2) else 0.0
    n_cut = cut_size * (1.0 / vol_1 + 1.0 / vol_2) if (vol_1 > 0 and vol_2 > 0) else 0.0
    min_vol = min(vol_1, vol_2)
    conductance = cut_size / min_vol if min_vol > 0 else 0.0

    metrics = {
        'cut_size': float(cut_size),
        'ratio_cut': float(ratio_cut),
        'normalized_cut': float(n_cut),
        'conductance': float(conductance),
    }
    return v1, v2, metrics


def laplacian_spectrum(  # NOSONAR - cyclic Jacobi orthogonal similarity sweeps for eigenspectrum
    graph: SparseMatrix[K, float],
    k: int | None = None,
    normalized: bool = False,
) -> tuple[list[float], list[SparseVector[K, float]]]:
    r"""Compute the eigenspectrum ($0 \le \lambda_1 \le \dots \le \lambda_k$) via cyclic Jacobi sweeps.

    Algebraic Signature:
        $L \mathbf{v}_i = \lambda_i \mathbf{v}_i, \quad 0 = \lambda_1 \le \lambda_2 \le \dots \le \lambda_n$

    Carrier:
        `tuple[list[float], list[SparseVector[K, float]]]` (Ascending eigenvalues and corresponding eigenvectors).

    Operations:
        - Jacobi Sweeps: Diagonalizes symmetric matrix $L$ in $O(N^3)$ via orthogonal Givens similarity transformations.

    Properties:
        All eigenvalues $\lambda_i \ge 0$ (positive semi-definite).
        Multiplicity of eigenvalue 0 equals the number of connected components.

    Applications:
        - Graph Fourier Transform (GFT) and spectral filter bank design.
        - Full spectrum analysis of small-to-medium networks ($N \le 150$).
        - Spectral embedding, heat kernel signatures, and wave equation simulation.

    Warnings:
        Issues `PerformanceWarning` if the graph order $N > 150$.

    Args:
        graph: Sparse adjacency matrix.
        k: Optional number of smallest eigenvalues/vectors to return (returns all if None).
        normalized: Whether to compute spectrum of symmetric normalized Laplacian.

    Returns:
        Tuple of `(eigenvalues, eigenvectors)` where eigenvalues are in ascending order.
    """
    nodes = sorted(set(graph.keys()) | {v for row in graph.values() for v in row}, key=str)
    n = len(nodes)
    if n > 150:
        warnings.warn(
            f'Computing full laplacian_spectrum for N={n} > 150 may be slow in pure Python.',
            PerformanceWarning,
            stacklevel=2,
        )

    if n == 0:
        return [], []

    lap = laplacian_matrix(graph, normalized='sym' if normalized else None)
    d_mat = [[lap.get(u, {}).get(v, 0.0) for v in nodes] for u in nodes]
    v_dense = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(100):
        max_val = 0.0
        p, q = 0, 1
        for i in range(n):
            for j in range(i + 1, n):
                if abs(d_mat[i][j]) > max_val:
                    max_val = abs(d_mat[i][j])
                    p, q = i, j

        if max_val < 1e-12:
            break

        diff = d_mat[q][q] - d_mat[p][p]
        if abs(d_mat[p][q]) < 1e-14:
            t = 0.0
        else:
            phi = diff / (2.0 * d_mat[p][q])
            t = (1.0 / (abs(phi) + math.sqrt(phi * phi + 1.0))) * (1.0 if phi >= 0 else -1.0)
        c = 1.0 / math.sqrt(t * t + 1.0)
        s = t * c

        d_pp = d_mat[p][p]
        d_qq = d_mat[q][q]
        d_pq = d_mat[p][q]

        d_mat[p][p] = d_pp - t * d_pq
        d_mat[q][q] = d_qq + t * d_pq
        d_mat[p][q] = 0.0
        d_mat[q][p] = 0.0

        for r in range(n):
            if r != p and r != q:
                d_r_p = d_mat[r][p]
                d_r_q = d_mat[r][q]
                d_mat[r][p] = c * d_r_p - s * d_r_q
                d_mat[p][r] = d_mat[r][p]
                d_mat[r][q] = s * d_r_p + c * d_r_q
                d_mat[q][r] = d_mat[r][q]

        for r in range(n):
            v_r_p = v_dense[r][p]
            v_r_q = v_dense[r][q]
            v_dense[r][p] = c * v_r_p - s * v_r_q
            v_dense[r][q] = s * v_r_p + c * v_r_q

    pairs: list[tuple[float, dict[K, float]]] = []
    for i in range(n):
        val = max(0.0, d_mat[i][i])
        vec = {nodes[r]: v_dense[r][i] for r in range(n)}
        max_k = max(vec.keys(), key=lambda k: abs(vec[k]))
        if vec[max_k] < 0:
            vec = {k: -v for k, v in vec.items()}
        pairs.append((val, vec))

    pairs.sort(key=lambda x: x[0])
    if k is not None:
        pairs = pairs[:k]

    return [p[0] for p in pairs], [p[1] for p in pairs]
