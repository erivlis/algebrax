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

from algebrax.algebra._field import Field
from algebrax.converters import get_matrix_keys, grid_to_sparse, prune_sparse, sparse_to_grid
from algebrax.typing import K, SparseMatrix, SparseVector, V


class SingularMatrixError(ArithmeticError, ValueError):
    """Raised when a matrix is singular or has no unique inverse/decomposition."""


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
                if pivot != 0:  # NOSONAR - exact zero denominator singularity check
                    val = s / pivot
                    if abs(val) > 1e-12:
                        l_dict[i][j] = val

    return prune_sparse(l_dict)


def lu_decompose(  # noqa: C901
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-14,
) -> tuple[SparseMatrix[K, V], SparseMatrix[K, V], SparseMatrix[K, V]]:
    """Compute the LU decomposition with partial pivoting for a sparse matrix A:
        P @ A = L @ U
    Generically supports any Field (e.g. float, Fraction, ModularField/GaloisField).

    Args:
        matrix: A sparse matrix dict[i, dict[j, V]].
        field: Optional Field typeclass providing field operations. If None,
            executes optimized native floating-point operations.
        tol: Tolerance for floating-point pivot singularity check.

    Returns:
        A tuple (P, L, U) of sparse matrices satisfying P @ A == L @ U.
    """
    rows, cols = get_matrix_keys(matrix)
    n_rows = len(rows)
    n_cols = len(cols)
    if n_rows == 0 or n_cols == 0:
        return {}, {}, {}
    min_dim = min(n_rows, n_cols)

    p_perm = list(range(n_rows))

    if field is None:
        # Native float fast-path
        w_mat = sparse_to_grid(matrix, rows, cols, fill_value=0.0)

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

            pivot_val = w_mat[k][k]
            if abs(pivot_val) > tol:
                inv_pivot = 1.0 / pivot_val  # Shannon: pivot inversion hoisting
                for i in range(k + 1, n_rows):
                    aik = w_mat[i][k]
                    if aik == 0.0 or abs(aik) <= tol:  # Shannon: inner zero-skipping
                        continue
                    factor = aik * inv_pivot
                    w_mat[i][k] = factor
                    for j in range(k + 1, n_cols):
                        akj = w_mat[k][j]
                        if akj != 0.0:
                            w_mat[i][j] -= factor * akj

        p_res = {rows[i]: {rows[p_perm[i]]: 1.0} for i in range(n_rows)}
        l_grid = [[1.0 if i == j else (w_mat[i][j] if j < i else 0.0) for j in range(min_dim)] for i in range(n_rows)]
        u_grid = [[w_mat[i][j] if j >= i else 0.0 for j in range(n_cols)] for i in range(min_dim)]

        return (
            prune_sparse(p_res),
            grid_to_sparse(l_grid, rows, cols[:min_dim]),
            grid_to_sparse(u_grid, rows[:min_dim], cols),
        )

    # Polymorphic Field path
    f_zero = field.zero
    f_one = field.one
    is_zero = field.is_zero
    mul = field.mul
    sub = field.sub
    inv = field.inv

    w_mat = sparse_to_grid(matrix, rows, cols, fill_value=f_zero)

    for k in range(min_dim):
        pivot_row = k
        has_abs = True
        try:
            max_v = abs(w_mat[k][k])
        except (TypeError, ValueError):
            has_abs = False

        if has_abs:
            for i in range(k + 1, n_rows):
                try:
                    val_abs = abs(w_mat[i][k])
                    if val_abs > max_v:
                        max_v = val_abs
                        pivot_row = i
                except (TypeError, ValueError):
                    if is_zero(w_mat[pivot_row][k]) and not is_zero(w_mat[i][k]):
                        pivot_row = i
        else:
            if is_zero(w_mat[k][k]):
                for i in range(k + 1, n_rows):
                    if not is_zero(w_mat[i][k]):
                        pivot_row = i
                        break

        if pivot_row != k:
            w_mat[k], w_mat[pivot_row] = w_mat[pivot_row], w_mat[k]
            p_perm[k], p_perm[pivot_row] = p_perm[pivot_row], p_perm[k]

        pivot = w_mat[k][k]
        if not is_zero(pivot):
            inv_pivot = inv(pivot)  # Shannon: pivot inversion hoisting
            for i in range(k + 1, n_rows):
                aik = w_mat[i][k]
                if is_zero(aik):  # Shannon: inner zero-skipping
                    continue
                factor = mul(aik, inv_pivot)
                w_mat[i][k] = factor
                for j in range(k + 1, n_cols):
                    akj = w_mat[k][j]
                    if is_zero(akj):  # Shannon: inner zero-skipping
                        continue
                    w_mat[i][j] = sub(w_mat[i][j], mul(factor, akj))

    p_res = {rows[i]: {rows[p_perm[i]]: f_one} for i in range(n_rows)}

    l_sparse: dict[Any, dict[Any, Any]] = {}
    for i in range(n_rows):
        r_key = rows[i]
        r_dict: dict[Any, Any] = {}
        for j in range(min_dim):
            c_key = cols[j]
            val = f_one if i == j else (w_mat[i][j] if j < i else f_zero)
            if not is_zero(val):
                r_dict[c_key] = val
        if r_dict:
            l_sparse[r_key] = r_dict

    u_sparse: dict[Any, dict[Any, Any]] = {}
    for i in range(min_dim):
        r_key = rows[i]
        r_dict = {}
        for j in range(n_cols):
            c_key = cols[j]
            val = w_mat[i][j] if j >= i else f_zero
            if not is_zero(val):
                r_dict[c_key] = val
        if r_dict:
            u_sparse[r_key] = r_dict

    return p_res, l_sparse, u_sparse


lu = lu_decompose  # Canonical alias


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


def _symmetric_jacobi_eigh(  # NOSONAR - cyclic Jacobi orthogonal similarity sweeps
    a_mat: list[list[float]],
    max_sweeps: int = 100,
    tol: float = 1e-12,
) -> tuple[list[float], list[list[float]]]:
    r"""Compute eigenvalues and eigenvectors of a real symmetric matrix using cyclic Jacobi rotations.

    Note on the 'eigh' naming convention:
        Following standard LAPACK, NumPy, and SciPy conventions, 'eig' denotes general
        eigenvalue decomposition for arbitrary matrices, whereas 'eigh' is specifically
        reserved for Hermitian or real symmetric matrices. By the Spectral Theorem,
        real symmetric matrices are guaranteed to have strictly real eigenvalues and
        a complete orthonormal basis of eigenvectors ($A = V \Lambda V^T$).

    Args:
        a_mat: Symmetric dense matrix represented as a list of rows.
        max_sweeps: Maximum number of sweep iterations.
        tol: Convergence tolerance for off-diagonal elements.

    Returns:
        tuple (eigenvalues, v_dense) where:
          - eigenvalues: list of real eigenvalues (diagonal elements).
          - v_dense: n x n eigenvector matrix where column `i` is the `i`-th eigenvector (`v_dense[r][i]`).
    """
    n = len(a_mat)
    if n == 0:
        return [], []

    d_mat = [list(row) for row in a_mat]
    v_dense = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(max_sweeps):
        max_val = 0.0
        p, q = 0, 1
        for i in range(n):
            for j in range(i + 1, n):
                if abs(d_mat[i][j]) > max_val:
                    max_val = abs(d_mat[i][j])
                    p, q = i, j

        if max_val < tol:
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

    eigenvalues = [d_mat[i][i] for i in range(n)]
    return eigenvalues, v_dense


def svd(
    matrix: SparseMatrix,
    k: int | None = None,
) -> tuple[SparseMatrix, SparseVector[int, float], SparseMatrix]:
    """Compute Singular Value Decomposition (SVD) for a sparse matrix A:
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

    # Compute normal matrix B = A^T @ A
    b_mat = [[sum(a_mat[r][i] * a_mat[r][j] for r in range(m)) for j in range(n)] for i in range(n)]

    raw_eigenvals, v_dense = _symmetric_jacobi_eigh(b_mat)
    eigenvals = [max(0.0, ev) for ev in raw_eigenvals]
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


def recompose_lu(
    p_mat: SparseMatrix,
    l_mat: SparseMatrix,
    u_mat: SparseMatrix,
    *,
    field: Any = None,
) -> SparseMatrix:
    """Reconstruct the original sparse matrix A from its LU factorization (P, L, U):
        A = P^T @ (L @ U)

    Args:
        p_mat: Permutation sparse matrix.
        l_mat: Lower-triangular sparse matrix.
        u_mat: Upper-triangular sparse matrix.
        field: Optional Field typeclass used for matrix dot multiplication.

    Returns:
        The reconstructed sparse matrix A.
    """
    from algebrax.matrix.core import dot, transpose

    lu_product = dot(l_mat, u_mat, semiring=field)
    p_t = transpose(p_mat)
    return dot(p_t, lu_product, semiring=field)


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


def recompose_svd(u: SparseMatrix, s: SparseVector[int, float], v_t: SparseMatrix) -> SparseMatrix:
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


def solve_triangular(
    matrix: SparseMatrix[K, V],
    rhs: SparseVector[K, V],
    *,
    field: Field[V] | None = None,
    lower: bool = True,
) -> SparseVector[K, V]:
    """Solve triangular linear system L x = b or U x = b via forward/backward substitution.

    Operates natively on sparse dictionaries without dense array conversions.
    Generically supports any Field (float, Fraction, ModularField/GaloisField).

    Args:
        matrix: Triangular sparse matrix mapping.
        rhs: Right-hand side sparse vector.
        field: Optional Field typeclass. If None, uses native float arithmetic.
        lower: If True, solves lower-triangular L x = b; if False, solves upper-triangular U x = b.

    Returns:
        Solution vector x as a sparse dictionary dict[K, V].

    Raises:
        SingularMatrixError: If any diagonal element on the solve path is zero.
    """
    all_keys = sorted(set(matrix.keys()) | set(rhs.keys()) | {k for r in matrix.values() for k in r}, key=str)
    if not all_keys:
        return {}

    keys = all_keys if lower else list(reversed(all_keys))

    if field is None:
        x_float: dict[K, float] = {}
        for k in keys:
            row = matrix.get(k, {})
            diag = row.get(k, 0.0)
            if abs(diag) <= 1e-14:
                raise SingularMatrixError(f'Singular matrix: zero diagonal element at key {k!r}.')
            s = 0.0
            for col_k, val in row.items():
                if col_k != k and col_k in x_float:
                    s += val * x_float[col_k]
            bk = rhs.get(k, 0.0)
            sol_k = (bk - s) / diag
            if abs(sol_k) > 1e-14:
                x_float[k] = sol_k
        return x_float  # type: ignore[return-value]

    f_zero = field.zero
    is_zero = field.is_zero
    sub = field.sub
    add = field.add
    mul = field.mul
    div = field.div

    x_field: dict[K, V] = {}
    for k in keys:
        row = matrix.get(k, {})
        diag = row.get(k, f_zero)
        if is_zero(diag):
            raise SingularMatrixError(f'Singular matrix: zero diagonal element at key {k!r}.')
        s = f_zero
        for col_k, val in row.items():
            if col_k != k and col_k in x_field:
                s = add(s, mul(val, x_field[col_k]))
        bk = rhs.get(k, f_zero)
        sol_k = div(sub(bk, s), diag)
        if not is_zero(sol_k):
            x_field[k] = sol_k
    return x_field


def solve(
    matrix: SparseMatrix[K, V],
    rhs: SparseVector[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-14,
) -> SparseVector[K, V]:
    """Solve the linear system A x = b for a square sparse matrix A and vector b.

    Computes solution via LU factorization with partial pivoting:
        P A x = L U x = P b
        1. Forward substitution: L y = P b
        2. Backward substitution: U x = y

    Generically supports any Field (e.g. float, Fraction, ModularField/GaloisField).

    Args:
        matrix: Square sparse matrix A.
        rhs: Right-hand side sparse vector b.
        field: Optional Field typeclass providing field operations.
        tol: Tolerance for floating-point singularity detection.

    Returns:
        Exact or floating-point solution vector x.

    Raises:
        SingularMatrixError: If matrix A is singular or non-invertible.
        ValueError: If matrix A is not square.
    """
    rows, cols = get_matrix_keys(matrix)
    n = len(rows)
    if n != len(cols):
        raise ValueError(f'solve requires square matrix, got {n}x{len(cols)}.')
    if n == 0:
        return {}

    p_mat, l_mat, u_mat = lu_decompose(matrix, field=field, tol=tol)

    # Check rank/singularity on U diagonal
    if field is None:
        for i in range(n):
            if abs(u_mat.get(rows[i], {}).get(cols[i], 0.0)) <= tol:
                raise SingularMatrixError(f'Matrix is singular (zero pivot at row {rows[i]!r}).')
        return _solve_float(p_mat, l_mat, u_mat, rhs, rows, cols, n, tol)  # type: ignore[return-value]

    for i in range(n):
        if field.is_zero(u_mat.get(rows[i], {}).get(cols[i], field.zero)):
            raise SingularMatrixError(f'Matrix is singular (zero pivot at row {rows[i]!r}).')
    return _solve_field(p_mat, l_mat, u_mat, rhs, rows, cols, n, field)


def _solve_float(
    p_mat: SparseMatrix[K, float],
    l_mat: SparseMatrix[K, float],
    u_mat: SparseMatrix[K, float],
    rhs: SparseVector[K, float],
    rows: list[K],
    cols: list[K],
    n: int,
    tol: float,
) -> SparseVector[K, float]:
    p_b_list = [rhs.get(next(iter(p_mat.get(rows[i], {}).keys()), rows[i]), 0.0) for i in range(n)]

    # 1. Forward substitution: L y = P b
    y = [0.0] * n
    for i in range(n):
        s = p_b_list[i]
        l_row = l_mat.get(rows[i], {})
        for j in range(i):
            val = l_row.get(cols[j], 0.0)
            if val != 0.0:
                s -= val * y[j]
        y[i] = s

    # 2. Backward substitution: U x = y
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = y[i]
        u_row = u_mat.get(rows[i], {})
        for j in range(i + 1, n):
            val = u_row.get(cols[j], 0.0)
            if val != 0.0:
                s -= val * x[j]
        diag = u_row.get(cols[i], 0.0)
        x[i] = s / diag

    sol: dict[K, float] = {}
    for i in range(n):
        if abs(x[i]) > tol:
            sol[cols[i]] = x[i]
    return sol


def _solve_field(
    p_mat: SparseMatrix[K, V],
    l_mat: SparseMatrix[K, V],
    u_mat: SparseMatrix[K, V],
    rhs: SparseVector[K, V],
    rows: list[K],
    cols: list[K],
    n: int,
    field: Field[V],
) -> SparseVector[K, V]:
    f_zero = field.zero
    sub = field.sub
    mul = field.mul
    div = field.div
    is_zero = field.is_zero

    p_b_list = [rhs.get(next(iter(p_mat.get(rows[i], {}).keys()), rows[i]), f_zero) for i in range(n)]

    # 1. Forward substitution: L y = P b
    y = [f_zero] * n
    for i in range(n):
        s = p_b_list[i]
        l_row = l_mat.get(rows[i], {})
        for j in range(i):
            val = l_row.get(cols[j], f_zero)
            if not is_zero(val):
                s = sub(s, mul(val, y[j]))
        y[i] = s

    # 2. Backward substitution: U x = y
    x = [f_zero] * n
    for i in range(n - 1, -1, -1):
        s = y[i]
        u_row = u_mat.get(rows[i], {})
        for j in range(i + 1, n):
            val = u_row.get(cols[j], f_zero)
            if not is_zero(val):
                s = sub(s, mul(val, x[j]))
        diag = u_row.get(cols[i], f_zero)
        x[i] = div(s, diag)

    sol: dict[K, V] = {}
    for i in range(n):
        if not is_zero(x[i]):
            sol[cols[i]] = x[i]
    return sol


def det(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-14,
) -> V:
    """Compute the determinant of a square sparse matrix in O(N^3) time via LU decomposition.

    Determinant invariant:
        det(A) = sgn(P) * prod(diag(U))

    Generically supports any Field (e.g. float, Fraction, ModularField/GaloisField).

    Args:
        matrix: Square sparse matrix.
        field: Optional Field typeclass providing field operations.
        tol: Tolerance for floating-point singularity detection.

    Returns:
        The determinant value in the underlying Field.

    Raises:
        ValueError: If matrix is not square.
    """
    rows, cols = get_matrix_keys(matrix)
    if len(rows) != len(cols):
        raise ValueError(f'Determinant is only defined for square matrices, got {len(rows)}x{len(cols)}.')
    n = len(rows)
    if n == 0:
        return 1.0 if field is None else field.one  # type: ignore[return-value]

    p_mat, _, u_mat = lu_decompose(matrix, field=field, tol=tol)

    p_map = {r: next(iter(p_mat[r].keys())) for r in rows if p_mat.get(r)}
    visited = set()
    num_cycles = 0
    for r in rows:
        if r not in visited:
            num_cycles += 1
            curr = r
            while curr not in visited:
                visited.add(curr)
                curr = p_map.get(curr, curr)
    sign = 1 if (n - num_cycles) % 2 == 0 else -1

    if field is None:
        res_float = float(sign)
        for i in range(n):
            diag = u_mat.get(rows[i], {}).get(cols[i], 0.0)
            res_float *= diag
        return res_float  # type: ignore[return-value]

    res_field = field.one if sign == 1 else field.neg(field.one)
    for i in range(n):
        diag = u_mat.get(rows[i], {}).get(cols[i], field.zero)
        res_field = field.mul(res_field, diag)
    return res_field


def inv(
    matrix: SparseMatrix[K, V],
    *,
    field: Field[V] | None = None,
    tol: float = 1e-14,
) -> SparseMatrix[K, V]:
    """Compute the inverse A^-1 of a square sparse matrix in O(N^3) time.

    Solves A x_j = e_j for each standard basis vector e_j using precomputed LU decomposition.
    Generically supports any Field (e.g. float, Fraction, ModularField/GaloisField).

    Args:
        matrix: Square sparse matrix.
        field: Optional Field typeclass providing field operations.
        tol: Tolerance for floating-point singularity detection.

    Returns:
        Inverse matrix A^-1 as a SparseMatrix.

    Raises:
        SingularMatrixError: If matrix is singular or non-invertible.
        ValueError: If matrix is not square.
    """
    rows, cols = get_matrix_keys(matrix)
    if len(rows) != len(cols):
        raise ValueError(f'Matrix inverse requires square matrix, got {len(rows)}x{len(cols)}.')
    n = len(rows)
    if n == 0:
        return {}

    f_one = 1.0 if field is None else field.one

    inv_matrix: dict[K, dict[K, V]] = {c: {} for c in cols}
    for r in rows:
        e_r = {r: f_one}
        x_r = solve(matrix, e_r, field=field, tol=tol)
        for c, val in x_r.items():
            inv_matrix[c][r] = val

    return {c: row for c, row in inv_matrix.items() if row}
