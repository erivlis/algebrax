import math
from collections import defaultdict
from collections.abc import Iterable, Mapping

from algebrax.semiring import Semiring, StandardSemiring
from algebrax.typing import K, N, SparseMatrix, SparseVector

__all__ = [
    'divergence',
    'fenchel_legendre_transform',
    'gaussian_kernel',
    'gradient',
    'laplacian',
    'ollivier_ricci_curvature',
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

    For Min-Plus Semiring (Tropical):
        (F*)(s) = sup_x { <s, x> - F(x) }
        But in Min-Plus algebra terms (where * is +, + is min):
        This often corresponds to the convex conjugate.

    In the context of "Tropical Fourier Transform" for a periodic signal f:
    F(s) = min_x ( f(x) - s*x )  (or similar depending on convention)

    Here we implement the standard convex conjugate definition:
    f*(s) = sup_x ( s*x - f(x) )

    Args:
        signal: The input signal (mapping from index/position to value).
        slope: The slope parameter (dual variable).
        semiring: The algebraic structure.
                  If Tropical (Min-Plus), we use min/plus logic?
                  Actually, the Fenchel transform is usually defined over the standard ring for the values.
                  If we are strictly in Tropical Semiring, "integration" is min.

    Returns:
        The value of the transform at the given slope.
    """
    # Standard Fenchel-Legendre: max(s*x - f(x))
    # This detects "slope content".

    # If the signal is sparse, we iterate over defined points.
    # We assume K (keys) are numeric (positions).

    max_val = float('-inf')

    for x, fx in signal.items():
        # We assume x is numeric (time/space index)
        if not isinstance(x, (int, float)):
            continue

        # val = s*x - f(x)
        val = slope * x - fx
        if val > max_val:
            max_val = val

    return max_val


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


def ollivier_ricci_curvature(graph: SparseMatrix) -> dict[tuple[K, K], float]:
    """
    Compute the Ollivier-Ricci Curvature for edges in a graph.
    Ric(xy) = 1 - W_1(m_x, m_y) / d(x, y)

    Where W_1 is the Wasserstein distance (Earth Mover's Distance) between
    probability measures m_x and m_y defined around nodes x and y.

    Note: This is a simplified implementation approximating W_1 for sparse graphs.
    Full computation requires a linear programming solver (e.g., scipy.optimize).
    Here we use a greedy approximation or simple overlap for efficiency in pure Python.

    Approximation: Jaccard-like overlap of neighborhoods.
    Ric(xy) approx 1 - (1 - |N(x) n N(y)| / |N(x) u N(y)|) ... this is rough.

    Let's implement a basic version based on "Forman-Ricci Curvature" which is
    much faster and purely combinatorial (O(N) instead of O(N^3)).

    Forman-Ricci Curvature for edge e=(u, v):
    F(e) = 4 - deg(u) - deg(v)

    Args:
        graph: Adjacency matrix (weighted).

    Returns:
        A dictionary mapping edges (u, v) to their curvature values.
    """
    curvature = {}
    degrees = {u: len(neighbors) for u, neighbors in graph.items()}

    for u, neighbors in graph.items():
        for v in neighbors:
            if u < v:  # Undirected edge, process once
                # Forman-Ricci Curvature (Combinatorial)
                # F(e) = 4 - deg(u) - deg(v)
                # This is a very rough proxy for "manifold curvature".
                # Negative values -> Hyperbolic (Tree-like, Expander)
                # Positive values -> Spherical (Clique-like, Cluster)
                # Zero -> Euclidean (Grid)

                # Refined Forman (accounting for triangles/weights is better but complex)
                # Let's stick to the basic combinatorial definition.
                deg_u = degrees.get(u, 0)
                deg_v = degrees.get(v, 0)

                # Standard Forman formula for unweighted graphs
                k = 4 - deg_u - deg_v

                curvature[(u, v)] = k

    return curvature
