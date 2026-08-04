"""
Tests for sparse matrix decompositions: LU, QR, SVD, Cholesky.
"""

import math

import pytest

from algebrax.matrix import dot, transpose
from algebrax.matrix.decompose import (
    cholesky,
    lu,
    qr,
    recompose_cholesky,
    recompose_lu,
    recompose_qr,
    recompose_svd,
    svd,
)


def is_matrix_close(m1: dict, m2: dict, tol: float = 1e-6) -> bool:
    """Helper to check numerical equality of sparse matrices."""
    all_rows = set(m1.keys()) | set(m2.keys())
    for r in all_rows:
        row1 = m1.get(r, {})
        row2 = m2.get(r, {})
        all_cols = set(row1.keys()) | set(row2.keys())
        for c in all_cols:
            v1 = row1.get(c, 0.0)
            v2 = row2.get(c, 0.0)
            if not math.isclose(v1, v2, abs_tol=tol):
                return False
    return True


def test_cholesky_decomposition():
    """Test Cholesky decomposition L @ L^T == A for SPD matrix."""
    a_spd = {
        "0": {"0": 4.0, "1": 12.0},
        "1": {"0": 12.0, "1": 37.0},
    }
    l_mat = cholesky(a_spd)
    llt = dot(l_mat, transpose(l_mat))
    assert is_matrix_close(a_spd, llt)

    # Non-positive definite matrix should raise ValueError
    a_non_pd = {
        "0": {"0": -1.0, "1": 0.0},
        "1": {"0": 0.0, "1": 2.0},
    }
    with pytest.raises(ValueError, match="not positive-definite"):
        cholesky(a_non_pd)


def test_lu_decomposition():
    """Test LU decomposition with partial pivoting P @ A == L @ U."""
    a_mat = {
        "0": {"0": 1.0, "1": 2.0, "2": 4.0},
        "1": {"0": 3.0, "1": 8.0, "2": 14.0},
        "2": {"0": 2.0, "1": 6.0, "2": 13.0},
    }
    p_mat, l_mat, u_mat = lu(a_mat)
    pa = dot(p_mat, a_mat)
    lu_prod = dot(l_mat, u_mat)

    assert is_matrix_close(pa, lu_prod)
    # Check L has 1.0 on diagonal
    for r in l_mat:
        assert math.isclose(l_mat[r][r], 1.0)


def test_qr_decomposition():
    """Test QR decomposition A == Q @ R and Q^T @ Q == I."""
    a_mat = {
        "0": {"0": 12.0, "1": -51.0, "2": 4.0},
        "1": {"0": 6.0, "1": 167.0, "2": -68.0},
        "2": {"0": -4.0, "1": 24.0, "2": -41.0},
    }
    q_mat, r_mat = qr(a_mat)
    qr_prod = dot(q_mat, r_mat)
    qtq = dot(transpose(q_mat), q_mat)

    assert is_matrix_close(a_mat, qr_prod)
    # Check Q^T @ Q is Identity
    i_expected = {"0": {"0": 1.0}, "1": {"1": 1.0}, "2": {"2": 1.0}}
    assert is_matrix_close(qtq, i_expected)


def test_svd_decomposition():
    """Test Truncated SVD decomposition A ≈ U @ diag(S) @ V^T."""
    a_mat = {
        "0": {"0": 3.0, "1": 2.0, "2": 2.0},
        "1": {"0": 2.0, "1": 3.0, "2": 1.0},
    }
    u_mat, s_vec, vt_mat = svd(a_mat)

    # Reconstruct A = U @ S_diag @ VT
    s_mat = {i: {i: s_vec[i]} for i in s_vec}
    us = dot(u_mat, s_mat)
    usvt = dot(us, vt_mat)

    assert is_matrix_close(a_mat, usvt)
    assert len(s_vec) == 2  # min(2, 3)

    # Truncated k=1
    _, s1, _ = svd(a_mat, k=1)
    assert len(s1) == 1


def test_recompose_cholesky():
    """Verify A == recompose_cholesky(L) for SPD matrix."""
    a = {0: {0: 4.0, 1: 12.0}, 1: {0: 12.0, 1: 37.0}}
    l_factor = cholesky(a)
    recomposed = recompose_cholesky(l_factor)
    assert is_matrix_close(a, recomposed)


def test_recompose_lu():
    """Verify A == recompose_lu(P, L, U)."""
    a = {0: {0: 2.0, 1: 1.0}, 1: {0: 4.0, 1: 3.0}}
    p, l_factor, u_factor = lu(a)
    recomposed = recompose_lu(p, l_factor, u_factor)
    assert is_matrix_close(a, recomposed)


def test_recompose_qr():
    """Verify A == recompose_qr(Q, R)."""
    a = {0: {0: 1.0, 1: 2.0}, 1: {0: 3.0, 1: 4.0}}
    q, r = qr(a)
    recomposed = recompose_qr(q, r)
    assert is_matrix_close(a, recomposed)


def test_recompose_svd():
    """Verify A ≈ recompose_svd(U, S, V_T)."""
    a = {0: {0: 3.0, 1: 0.0}, 1: {0: 0.0, 1: 4.0}}
    u, s, v_t = svd(a)
    recomposed = recompose_svd(u, s, v_t)
    assert is_matrix_close(a, recomposed)

