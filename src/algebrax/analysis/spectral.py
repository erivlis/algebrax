r"""
Ramanujan expander graph verification, adjacency spectra, and discrete graph Hecke operators.

Algebraic Signatures:
    Ramanujan Bound:        $\max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$
    Hecke Walk Recursion:   $T_0 = I, \; T_1 = A, \; T_2 = A^2 - d I, \; T_k = A T_{k-1} - (d - 1) T_{k-2}$
"""

from __future__ import annotations

import math

from algebrax.matrix.core import add, dot, subtract
from algebrax.matrix.decompose import _symmetric_jacobi_eigh
from algebrax.typing import K, SparseMatrix


def _infer_regular_degree(adjacency: SparseMatrix[K, float], degree: int | None, tol: float = 1e-7) -> int:
    """Validate or infer the regularity degree d of an undirected graph."""
    nodes = sorted(set(adjacency.keys()) | {v for row in adjacency.values() for v in row}, key=str)
    if not nodes:
        raise ValueError('Cannot determine degree of an empty graph.')

    degs = [sum(float(w) for v, w in adjacency.get(u, {}).items() if abs(w) > tol) for u in nodes]
    if degree is None:
        d_first = round(degs[0])
        for d_u in degs:
            if abs(d_u - d_first) > tol:
                raise ValueError(f'Graph is not regular: found vertex degrees {degs}.')
        degree = int(d_first)
    else:
        for d_u in degs:
            if abs(d_u - degree) > tol:
                raise ValueError(f'Graph is not {degree}-regular: found vertex degree {d_u}.')

    if degree < 1:
        raise ValueError(f'Regularity degree must be >= 1, got {degree}.')
    return degree


def adjacency_spectrum(adjacency: SparseMatrix[K, float]) -> list[float]:
    r"""Compute the real eigenvalues $\lambda_1 \ge \lambda_2 \ge \dots \ge \lambda_n$ of a symmetric adjacency matrix.

    Args:
        adjacency: Symmetric sparse adjacency matrix $A$.

    Returns:
        List of eigenvalues sorted in descending order.
    """
    nodes = sorted(set(adjacency.keys()) | {v for row in adjacency.values() for v in row}, key=str)
    n = len(nodes)
    if n == 0:
        return []
    d_mat = [
        [0.5 * (float(adjacency.get(u, {}).get(v, 0.0)) + float(adjacency.get(v, {}).get(u, 0.0))) for v in nodes]
        for u in nodes
    ]
    raw_eigenvals, _ = _symmetric_jacobi_eigh(d_mat, max_sweeps=max(100, 15 * n * (n - 1) // 2))
    return sorted((float(val) for val in raw_eigenvals), reverse=True)


def is_ramanujan_graph(
    adjacency: SparseMatrix[K, float],
    degree: int | None = None,
    tol: float = 1e-7,
) -> tuple[bool, float, float]:
    r"""Verify whether a $d$-regular undirected graph satisfies the Alon-Boppana / Ramanujan expander bound.

    Algebraic Signature:
        $\lambda(G) = \max_{|\lambda_i| < d} |\lambda_i| \le 2\sqrt{d - 1}$

    Properties:
        - Trivial eigenvalues satisfy $|\lambda_i| = d$ ($\lambda_1 = d$ for each connected component,
          and $\lambda_n = -d$ if the graph is bipartite).
        - Every non-trivial eigenvalue $\lambda_i$ with $|\lambda_i| < d$ must lie in the Hasse-Weil
          interval $[-2\sqrt{d - 1}, 2\sqrt{d - 1}]$.

    Args:
        adjacency: Sparse symmetric adjacency matrix of a $d$-regular graph.
        degree: Optional regularity degree $d$ (inferred and validated from vertex degrees if `None`).
        tol: Numerical tolerance for eigenvalue comparison.

    Returns:
        Tuple `(is_ramanujan, max_nontrivial_eigenvalue, ramanujan_threshold)`.
    """
    d = _infer_regular_degree(adjacency, degree, tol=tol)
    threshold = 2.0 * math.sqrt(d - 1)
    spectrum = adjacency_spectrum(adjacency)

    # Filter out trivial eigenvalues |lambda| == d
    nontrivial = [abs(lam) for lam in spectrum if abs(abs(lam) - d) > 1e-5]
    max_nontrivial = max(nontrivial) if nontrivial else 0.0
    is_ram = max_nontrivial <= threshold + tol
    return is_ram, float(max_nontrivial), float(threshold)


def _scale_matrix(mat: SparseMatrix[K, float], scalar: float, tol: float = 1e-12) -> SparseMatrix[K, float]:
    """Multiply a sparse matrix by a scalar, pruning near-zero entries."""
    if abs(scalar) <= tol:
        return {}
    out: SparseMatrix[K, float] = {}
    for u, row in mat.items():
        scaled_row = {v: scalar * val for v, val in row.items() if abs(scalar * val) > tol}
        if scaled_row:
            out[u] = scaled_row
    return out


def hecke_graph_operator(
    adjacency: SparseMatrix[K, float],
    k: int,
    degree: int | None = None,
) -> SparseMatrix[K, float]:
    r"""Compute the $k$-th discrete Hecke (non-backtracking walk) operator $T_k$ on a $d$-regular graph.

    Algebraic Signature:
        $T_0 = I, \quad T_1 = A, \quad T_2 = A^2 - d I, \quad T_k = A T_{k-1} - (d - 1) T_{k-2} \;\; (k \ge 3)$

    Properties:
        - $(T_k)_{uv}$ counts the number of non-backtracking walks of length $k$ between $u$ and $v$.
        - Hecke operators commute pairwise: $T_j T_k = T_k T_j$, generating a commutative ring of
          spherical Hecke convolution operators over the $d$-regular graph.
        - Shares a common eigenbasis with $A$: an eigenvector $A v = \lambda v$ is an eigenvector of $T_k$.

    Args:
        adjacency: Sparse adjacency matrix $A$ of a $d$-regular graph.
        k: Walk length $k \ge 0$.
        degree: Optional regularity degree $d$ (inferred if `None`).

    Returns:
        Sparse matrix $T_k$ of non-backtracking walks of length $k$.
    """
    if k < 0:
        raise ValueError(f'Hecke operator index k must be >= 0, got {k}.')
    d = _infer_regular_degree(adjacency, degree)
    nodes = sorted(set(adjacency.keys()) | {v for row in adjacency.values() for v in row}, key=str)
    ident: SparseMatrix[K, float] = {u: {u: 1.0} for u in nodes}

    if k == 0:
        return ident
    if k == 1:
        return {u: dict(row) for u, row in adjacency.items() if row}

    t_prev2 = ident
    t_prev1: SparseMatrix[K, float] = {u: dict(row) for u, row in adjacency.items() if row}

    # Step m = 2: T_2 = A^2 - d * I
    a2 = dot(t_prev1, t_prev1)
    t_curr = subtract(a2, _scale_matrix(t_prev2, float(d)))
    if k == 2:
        return {u: {v: val for v, val in row.items() if abs(val) > 1e-12} for u, row in t_curr.items() if row}

    t_prev2, t_prev1 = t_prev1, t_curr
    for _ in range(3, k + 1):
        at = dot(adjacency, t_prev1)
        t_curr = add(at, _scale_matrix(t_prev2, -float(d - 1)))
        t_prev2, t_prev1 = t_prev1, t_curr

    cleaned: SparseMatrix[K, float] = {}
    for u, row in t_curr.items():
        clean_row = {v: val for v, val in row.items() if abs(val) > 1e-12}
        if clean_row:
            cleaned[u] = clean_row
    return cleaned


__all__ = [
    'adjacency_spectrum',
    'hecke_graph_operator',
    'is_ramanujan_graph',
]
