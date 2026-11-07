"""
Tests for sparse matrix decompositions: LU, QR, SVD, Cholesky.
"""

import math

import pytest

from algebrax.matrix import dot, transpose
from algebrax.matrix.decompose import (
    SingularMatrixError,
    cholesky,
    det,
    inv,
    lu_decompose,
    qr,
    recompose_cholesky,
    recompose_lu,
    recompose_qr,
    recompose_svd,
    solve,
    solve_triangular,
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
        '0': {'0': 4.0, '1': 12.0},
        '1': {'0': 12.0, '1': 37.0},
    }
    l_mat = cholesky(a_spd)
    llt = dot(l_mat, transpose(l_mat))
    assert is_matrix_close(a_spd, llt)

    # Non-positive definite matrix should raise ValueError
    a_non_pd = {
        '0': {'0': -1.0, '1': 0.0},
        '1': {'0': 0.0, '1': 2.0},
    }
    with pytest.raises(ValueError, match='not positive-definite'):
        cholesky(a_non_pd)


def test_lu_decomposition():
    """Test LU decomposition with partial pivoting P @ A == L @ U."""
    a_mat = {
        '0': {'0': 1.0, '1': 2.0, '2': 4.0},
        '1': {'0': 3.0, '1': 8.0, '2': 14.0},
        '2': {'0': 2.0, '1': 6.0, '2': 13.0},
    }
    p_mat, l_mat, u_mat = lu_decompose(a_mat)
    pa = dot(p_mat, a_mat)
    lu_prod = dot(l_mat, u_mat)

    assert is_matrix_close(pa, lu_prod)
    # Check L has 1.0 on diagonal
    for r in l_mat:
        assert math.isclose(l_mat[r][r], 1.0)


def test_qr_decomposition():
    """Test QR decomposition A == Q @ R and Q^T @ Q == I."""
    a_mat = {
        '0': {'0': 12.0, '1': -51.0, '2': 4.0},
        '1': {'0': 6.0, '1': 167.0, '2': -68.0},
        '2': {'0': -4.0, '1': 24.0, '2': -41.0},
    }
    q_mat, r_mat = qr(a_mat)
    qr_prod = dot(q_mat, r_mat)
    qtq = dot(transpose(q_mat), q_mat)

    assert is_matrix_close(a_mat, qr_prod)
    # Check Q^T @ Q is Identity
    i_expected = {'0': {'0': 1.0}, '1': {'1': 1.0}, '2': {'2': 1.0}}
    assert is_matrix_close(qtq, i_expected)


def test_svd_decomposition():
    """Test Truncated SVD decomposition A ≈ U @ diag(S) @ V^T."""
    a_mat = {
        '0': {'0': 3.0, '1': 2.0, '2': 2.0},
        '1': {'0': 2.0, '1': 3.0, '2': 1.0},
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
    p, l_factor, u_factor = lu_decompose(a)
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


def test_solve_triangular_float_and_field():
    """Verify solve_triangular over float and ModularField, including upper/lower and singular cases."""
    from fractions import Fraction

    from algebrax.algebra import ModularField, StandardField

    # Empty
    assert solve_triangular({}, {}) == {}

    # Float lower-triangular L x = b
    l_mat = {0: {0: 2.0}, 1: {0: 4.0, 1: 3.0}}
    b_vec = {0: 6.0, 1: 18.0}
    x_low = solve_triangular(l_mat, b_vec, lower=True)
    assert x_low[0] == pytest.approx(3.0)
    assert x_low[1] == pytest.approx(2.0)

    # Float upper-triangular U x = b
    u_mat = {0: {0: 2.0, 1: 4.0}, 1: {1: 3.0}}
    b_up = {0: 14.0, 1: 6.0}
    x_up = solve_triangular(u_mat, b_up, lower=False)
    assert x_up[1] == pytest.approx(2.0)
    assert x_up[0] == pytest.approx(3.0)

    # Singular float triangular
    with pytest.raises(SingularMatrixError, match='zero diagonal'):
        solve_triangular({0: {0: 0.0}, 1: {1: 1.0}}, {0: 1.0}, lower=True)

    # Field lower-triangular over Q (Fraction)
    q_field = StandardField(Fraction)
    l_q = {0: {0: Fraction(2)}, 1: {0: Fraction(1), 1: Fraction(3)}}
    b_q = {0: Fraction(4), 1: Fraction(8)}
    x_q = solve_triangular(l_q, b_q, field=q_field, lower=True)
    assert x_q == {0: Fraction(2), 1: Fraction(2)}

    # Field upper-triangular over ModularField(7)
    gf7 = ModularField(7)
    assert gf7.p == 7
    u_gf = {0: {0: 2, 1: 3}, 1: {1: 4}}
    b_gf = {0: 5, 1: 1}  # 4 * x1 = 1 (mod 7) -> x1 = 2; 2*x0 + 3*2 = 5 -> 2*x0 = 6 -> x0 = 3
    x_gf = solve_triangular(u_gf, b_gf, field=gf7, lower=False)
    assert x_gf == {0: 3, 1: 2}

    # Singular Field triangular
    with pytest.raises(SingularMatrixError, match='zero diagonal'):
        solve_triangular({0: {0: 0}, 1: {1: 1}}, {0: 1}, field=gf7, lower=True)


def test_solve_det_inv_float_and_field_edge_cases():
    """Verify solve, det, inv, and lu_decompose across float, custom non-abs Field, and error paths."""
    from algebrax.algebra import Field, ModularField
    from algebrax.matrix.decompose import _symmetric_jacobi_eigh

    # Empty cases
    assert lu_decompose({}) == ({}, {}, {})
    assert svd({}) == ({}, {}, {})
    assert _symmetric_jacobi_eigh([]) == ([], [])
    assert solve({}, {}) == {}
    assert det({}) == 1.0
    assert inv({}) == {}

    gf5 = ModularField(5)
    assert det({}, field=gf5) == 1

    # Non-square errors
    rect = {0: {0: 1.0, 1: 2.0}}
    with pytest.raises(ValueError, match='square'):
        solve(rect, {0: 1.0})
    with pytest.raises(ValueError, match='square'):
        det(rect)
    with pytest.raises(ValueError, match='square'):
        inv(rect)

    # Float solve, det, inv with row swaps (pivoting)
    a_float = {0: {0: 0.0, 1: 2.0, 2: 1.0}, 1: {0: 1.0, 1: -2.0, 2: -3.0}, 2: {0: 3.0, 1: 1.0, 2: 2.0}}
    b_float = {0: 8.0, 1: -15.0, 2: 13.0}
    x_float = solve(a_float, b_float)
    assert x_float[0] == pytest.approx(1.0)
    assert x_float[1] == pytest.approx(2.0)
    assert x_float[2] == pytest.approx(4.0)

    d_float = det(a_float)
    assert d_float == pytest.approx(-15.0)

    a_inv = inv(a_float)
    prod = dot(a_float, a_inv)
    assert is_matrix_close(prod, {0: {0: 1.0}, 1: {1: 1.0}, 2: {2: 1.0}})

    # Singular float solve
    with pytest.raises(SingularMatrixError, match='singular'):
        solve({0: {0: 1.0, 1: 2.0}, 1: {0: 2.0, 1: 4.0}}, {0: 1.0, 1: 2.0})

    # Singular Field solve
    with pytest.raises(SingularMatrixError, match='singular'):
        solve({0: {0: 1, 1: 2}, 1: {0: 2, 1: 4}}, {0: 1, 1: 2}, field=gf5)

    # Custom Field whose elements do NOT support abs() to exercise the non-abs pivoting branch in lu_decompose
    class Box:
        def __init__(self, v: int):
            self.v = v % 5

        def __eq__(self, other: object) -> bool:
            return isinstance(other, Box) and self.v == other.v

    class BoxField(Field[Box]):
        @property
        def zero(self) -> Box:
            return Box(0)

        @property
        def one(self) -> Box:
            return Box(1)

        def is_zero(self, a: Box) -> bool:
            return a.v == 0

        def add(self, a: Box, b: Box) -> Box:
            return Box(a.v + b.v)

        def neg(self, a: Box) -> Box:
            return Box(-a.v)

        def mul(self, a: Box, b: Box) -> Box:
            return Box(a.v * b.v)

        def inv(self, a: Box) -> Box:
            if a.v == 0:
                raise ZeroDivisionError
            return Box(pow(a.v, -1, 5))

    bf = BoxField()
    mat_box = {
        0: {0: Box(0), 1: Box(2)},
        1: {0: Box(3), 1: Box(1)},
    }
    p_b, l_b, u_b = lu_decompose(mat_box, field=bf)
    recomp_b = recompose_lu(p_b, l_b, u_b, field=bf)
    assert recomp_b[0][1] == Box(2)
    assert recomp_b[1][0] == Box(3)
    assert det(mat_box, field=bf) == Box(4)  # -(2*3) = -6 = 4 (mod 5)
    inv_b = inv(mat_box, field=bf)
    assert dot(mat_box, inv_b, semiring=bf) == {0: {0: Box(1)}, 1: {1: Box(1)}}

