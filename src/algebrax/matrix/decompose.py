"""
Sparse Matrix Decompositions (LU, QR, SVD, Cholesky).

This module provides sparse dictionary-based matrix factorizations completing the Noether
symmetry of matrix construction/deconstruction:
  - LU Decomposition with Partial Pivoting: P @ A = L @ U
  - QR Decomposition via Modified Gram-Schmidt: A = Q @ R
  - Singular Value Decomposition (SVD): A ≈ U @ diag(S) @ V^T
  - Cholesky Decomposition for SPD matrices: A = L @ L^T
"""

import math
from typing import Any

from algebrax.converters import get_matrix_keys, grid_to_sparse, prune_sparse, sparse_to_grid
from algebrax.typing import SparseMatrix, SparseVector


def cholesky(matrix: SparseMatrix) -> SparseMatrix:
    """
    Compute the Cholesky decomposition of a symmetric positive-definite sparse matrix A:
        A = L @ L^T
    where L is a lower-triangular sparse matrix.

    Args:
        matrix: A symmetric positive-definite sparse matrix dict[i, dict[j, float]].

    Returns:
        The lower-triangular sparse matrix L.

    Raises:
        ValueError: If matrix is not positive-definite.
    """
    keys = sorted(matrix.keys(), key=str)
    l_dict: dict[Any, dict[Any, float]] = {r: {} for r in keys}

    for i_idx, i in enumerate(keys):
        for j_idx in range(i_idx + 1):
            j = keys[j_idx]
            s = matrix.get(i, {}).get(j, 0.0) - sum(
                l_dict[i].get(keys[k], 0.0) * l_dict[j].get(keys[k], 0.0) for k in range(j_idx)
            )
            if i == j:
                if s <= 0:
                    raise ValueError('Matrix is not positive-definite for Cholesky decomposition.')
                l_dict[i][j] = math.sqrt(s)
            else:
                pivot = l_dict[j].get(j, 0.0)
                if pivot != 0:
                    val = s / pivot
                    if abs(val) > 1e-12:
                        l_dict[i][j] = val

    return prune_sparse(l_dict)


def lu(matrix: SparseMatrix) -> tuple[SparseMatrix, SparseMatrix, SparseMatrix]:
    """
    Compute the LU decomposition with partial pivoting for a sparse matrix A:
        P @ A = L @ U
    where P is a permutation matrix, L is lower-triangular with 1s on diagonal,
    and U is upper-triangular.

    Args:
        matrix: A sparse matrix dict[i, dict[j, float]].

    Returns:
        A tuple (P, L, U) of sparse matrices satisfying P @ A == L @ U.
    """
    rows, cols = get_matrix_keys(matrix)
    n_rows = len(rows)
    n_cols = len(cols)
    min_dim = min(n_rows, n_cols)

    p_perm = list(range(n_rows))
    w_mat = sparse_to_grid(matrix, rows, cols)

    for k in range(min_dim):
        pivot_row = k
        max_v = abs(w_mat[k][k])
        for i in range(k + 1, n_rows):
            if abs(w_mat[i][k]) > max_v:
                max_v = abs(w_mat[i][k])
                pivot_row = i

        if pivot_row != k:
            w_mat[k], w_mat[pivot_row] = w_mat[pivot_row], w_mat[k]
            p_perm[k], p_perm[pivot_row] = p_perm[pivot_row], p_perm[k]

        if abs(w_mat[k][k]) > 1e-14:
            for i in range(k + 1, n_rows):
                w_mat[i][k] /= w_mat[k][k]
                for j in range(k + 1, n_cols):
                    w_mat[i][j] -= w_mat[i][k] * w_mat[k][j]

    p_res = {rows[i]: {rows[p_perm[i]]: 1.0} for i in range(n_rows)}

    l_grid = [[1.0 if i == j else (w_mat[i][j] if j < i else 0.0) for j in range(min_dim)] for i in range(n_rows)]
    u_grid = [[w_mat[i][j] if j >= i else 0.0 for j in range(n_cols)] for i in range(min_dim)]

    return (
        prune_sparse(p_res),
        grid_to_sparse(l_grid, rows, cols[:min_dim]),
        grid_to_sparse(u_grid, rows[:min_dim], cols),
    )


def qr(matrix: SparseMatrix) -> tuple[SparseMatrix, SparseMatrix]:
    """
    Compute QR decomposition via Modified Gram-Schmidt for a sparse matrix A:
        A = Q @ R
    where Q has orthonormal columns (Q^T @ Q = I) and R is upper-triangular.

    Args:
        matrix: A sparse matrix dict[i, dict[j, float]].

    Returns:
        A tuple (Q, R) of sparse matrices satisfying A == Q @ R.
    """
    rows, cols = get_matrix_keys(matrix)
    n_rows = len(rows)
    n_cols = len(cols)

    a_grid = sparse_to_grid(matrix, rows, cols)
    v_cols = [[a_grid[r][c] for r in range(n_rows)] for c in range(n_cols)]
    q_cols = [[0.0] * n_rows for _ in range(n_cols)]
    r_mat = [[0.0] * n_cols for _ in range(n_cols)]

    for j in range(n_cols):
        v = list(v_cols[j])
        for i in range(j):
            rij = sum(q_cols[i][r] * v[r] for r in range(n_rows))
            r_mat[i][j] = rij
            for r in range(n_rows):
                v[r] -= rij * q_cols[i][r]

        rjj = math.sqrt(sum(x * x for x in v))
        r_mat[j][j] = rjj
        if rjj > 1e-14:
            for r in range(n_rows):
                q_cols[j][r] = v[r] / rjj

    q_grid = [[q_cols[c][r] for c in range(n_cols)] for r in range(n_rows)]

    return (
        grid_to_sparse(q_grid, rows, cols),
        grid_to_sparse(r_mat, cols, cols),
    )


def svd(
    matrix: SparseMatrix, k: int | None = None
) -> tuple[SparseMatrix, SparseVector[int, float], SparseMatrix]:
    """
    Compute Singular Value Decomposition (SVD) for a sparse matrix A:
        A ≈ U @ diag(S) @ V^T

    Args:
        matrix: A sparse matrix dict[i, dict[j, float]].
        k: Optional maximum rank / number of singular components to compute.

    Returns:
        A tuple (U, S, V_T) where:
          - U is a sparse matrix of left singular vectors
          - S is a sparse vector dict[int, float] of singular values
          - V_T is a sparse matrix of right singular vectors (V^T)
    """
    rows, cols = get_matrix_keys(matrix)
    m = len(rows)
    n = len(cols)
    if m == 0 or n == 0:
        return {}, {}, {}

    max_rank = min(m, n)
    r_k = max_rank if k is None else min(k, max_rank)

    a_mat = sparse_to_grid(matrix, rows, cols)

    # B = A^T @ A
    b_mat = [[sum(a_mat[r][i] * a_mat[r][j] for r in range(m)) for j in range(n)] for i in range(n)]

    v_dense = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    d_mat = [list(row) for row in b_mat]

    # Jacobi eigenvalue sweeps on A^T @ A
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
        if abs(d_mat[p][q]) < 1e-12:
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

    eigenvals = [max(0.0, d_mat[i][i]) for i in range(n)]
    pairs = [(math.sqrt(eigenvals[i]), [v_dense[j][i] for j in range(n)]) for i in range(n)]
    pairs.sort(key=lambda x: x[0], reverse=True)

    s_dict: dict[int, float] = {}
    u_cols: list[list[float]] = []
    v_cols: list[list[float]] = []

    for idx in range(r_k):
        sigma, v_col = pairs[idx]
        if sigma < 1e-12:
            break
        s_dict[idx] = sigma
        v_cols.append(v_col)

        u_col = [sum(a_mat[i][j] * v_col[j] for j in range(n)) / sigma for i in range(m)]
        u_cols.append(u_col)

    actual_k = len(s_dict)

    u_grid = [[u_cols[j][i] for j in range(actual_k)] for i in range(m)]
    vt_grid = [[v_cols[j][c] for c in range(n)] for j in range(actual_k)]

    return (
        grid_to_sparse(u_grid, rows, list(range(actual_k))),
        s_dict,
        grid_to_sparse(vt_grid, list(range(actual_k)), cols),
    )


def recompose_lu(p_mat: SparseMatrix, l_mat: SparseMatrix, u_mat: SparseMatrix) -> SparseMatrix:
    """
    Reconstruct the original sparse matrix A from its LU factorization (P, L, U):
        A = P^T @ (L @ U)

    Args:
        p_mat: Permutation sparse matrix.
        l_mat: Lower-triangular sparse matrix.
        u_mat: Upper-triangular sparse matrix.

    Returns:
        The reconstructed sparse matrix A.
    """
    from algebrax.matrix.core import dot, transpose

    lu_product = dot(l_mat, u_mat)
    p_t = transpose(p_mat)
    return dot(p_t, lu_product)


def recompose_qr(q_mat: SparseMatrix, r_mat: SparseMatrix) -> SparseMatrix:
    """
    Reconstruct the original sparse matrix A from its QR factorization (Q, R):
        A = Q @ R

    Args:
        q_mat: Orthonormal sparse matrix Q.
        r_mat: Upper-triangular sparse matrix R.

    Returns:
        The reconstructed sparse matrix A.
    """
    from algebrax.matrix.core import dot

    return dot(q_mat, r_mat)


def recompose_svd(
    u: SparseMatrix, s: SparseVector[int, float], v_t: SparseMatrix
) -> SparseMatrix:
    """
    Reconstruct the sparse matrix A from its SVD components (U, S, V_T):
        A ≈ U @ diag(S) @ V_T

    Args:
        u: Left singular vectors sparse matrix.
        s: Vector/dict of singular values.
        v_t: Right singular vectors transpose sparse matrix.

    Returns:
        The reconstructed/approximated sparse matrix A.
    """
    from algebrax.matrix.core import dot

    s_matrix = {k: {k: val} for k, val in s.items() if val != 0}
    sv_t = dot(s_matrix, v_t)
    return dot(u, sv_t)


def recompose_cholesky(l_mat: SparseMatrix) -> SparseMatrix:
    """
    Reconstruct the original symmetric positive-definite sparse matrix A from its Cholesky factor L:
        A = L @ L^T

    Args:
        l_mat: Lower-triangular sparse matrix factor.

    Returns:
        The reconstructed sparse matrix A.
    """
    from algebrax.matrix.core import dot, transpose

    return dot(l_mat, transpose(l_mat))


