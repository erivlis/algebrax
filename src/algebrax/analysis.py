import math
from collections import defaultdict
from collections.abc import Iterable, Mapping

from algebrax.semiring import ArcticSemiring, LogSemiring, Semiring, StandardSemiring, TropicalSemiring
from algebrax.typing import K, N, SparseMatrix, SparseVector

__all__ = [
    'divergence',
    'fenchel_legendre_transform',
    'forman_ricci_curvature',
    'gaussian_kernel',
    'gradient',
    'laplacian',
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


def fenchel_legendre_transform(
        signal: SparseVector[K, N],
        slope: N,
        semiring: Semiring[N] | None = None,
) -> N:
    """
    Compute the discrete Fenchel-Legendre transform (Slope Transform) of a signal at a specific slope.
    This is the Tropical/Idempotent analog of the Fourier Transform.

    If semiring is None (or StandardSemiring), we fall back to the standard convex conjugate:
        f*(s) = sup_x { s * x - f(x) }

    If a general semiring is provided, we compute the generalized Legendre-Fenchel transform:
        f*(s) = \\bigoplus_x { s \\otimes x \\otimes f(x)^{-1} }
    where \\bigoplus is semiring.add, \\otimes is semiring.mul, and f(x)^{-1} is the multiplicative inverse
    of f(x) under the semiring's multiplication.

    Args:
        signal: The input signal (mapping from index/position to value).
        slope: The slope parameter (dual variable).
        semiring: The algebraic structure.

    Returns:
        The value of the transform at the given slope.
    """
    if not signal:
        if semiring is not None:
            return semiring.zero
        return float('-inf')

    if semiring is None or isinstance(semiring, StandardSemiring):
        max_val = float('-inf')
        for x, fx in signal.items():
            if not isinstance(x, (int, float)):
                continue
            val = slope * x - fx
            if val > max_val:
                max_val = val
        if max_val == float('-inf'):
            return semiring.zero if semiring is not None else float('-inf')
        return max_val

    total = semiring.zero
    first = True
    for x, fx in signal.items():
        if not isinstance(x, (int, float)):
            continue

        try:
            sx = semiring.mul(slope, x)
        except Exception:
            sx = semiring.mul(slope, type(slope)(x))

        if isinstance(semiring, (TropicalSemiring, ArcticSemiring, LogSemiring)):
            # Multiplication is addition (+), so multiplicative inverse is negation (-fx).
            inv_fx = -fx
            term = semiring.mul(sx, inv_fx)
        else:
            try:
                inv_fx = 1.0 / fx if fx != 0 else float('inf')
                term = semiring.mul(sx, inv_fx)
            except Exception:
                term = sx - fx

        if first:
            total = term
            first = False
        else:
            total = semiring.add(total, term)

    return total


def _is_graph_weighted(graph: SparseMatrix) -> bool:
    for neighbors in graph.values():
        for w in neighbors.values():
            if w != 1 and math.isclose(w,1.0):
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
            if w_e == 0:
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
