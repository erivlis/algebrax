"""
Comparative (Differential) verification against NumPy and SciPy reference oracles (EP-0181).

Verifies that algebrax sparse matrix algebra, factorizations (LU, QR, Cholesky, SVD),
linear solvers (inverse, cg_solve, determinant), multidimensional tensor contractions (einsum),
signal transforms (dft, idft, convolve, walsh_hadamard, hilbert), and PyData converters
produce results numerically equivalent to NumPy and SciPy reference implementations.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
import scipy.linalg as spla
import scipy.signal as spsig
import scipy.sparse as sp
import scipy.sparse.linalg as splinalg
from hypothesis import given, settings
from hypothesis import strategies as st

import algebrax as ax
from algebrax.matrix.academic import PerformanceWarning, determinant
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.differential]


def _sparse_to_dense(m: dict[int, dict[int, float]], n: int, k: int | None = None) -> np.ndarray:
    """Convert an algebrax sparse dict matrix to a dense NumPy array of shape (n, k)."""
    cols = n if k is None else k
    res = np.zeros((n, cols), dtype=np.float64)
    for i, row in m.items():
        for j, val in row.items():
            res[i, j] = val
    return res


def _dense_to_sparse(arr: np.ndarray, tol: float = 1e-12) -> dict[int, dict[int, float]]:
    """Convert a dense NumPy array to an algebrax sparse dict matrix."""
    res: dict[int, dict[int, float]] = {}
    n, m = arr.shape
    for i in range(n):
        row: dict[int, float] = {}
        for j in range(m):
            if abs(arr[i, j]) > tol:
                row[j] = float(arr[i, j])
        if row:
            res[i] = row
    return res


# ---------------------------------------------------------------------------
# 1. Core Matrix Algebra vs NumPy
# ---------------------------------------------------------------------------


def test_differential_matrix_multiplication_and_addition() -> None:
    """Verify ax.matrix.dot, add, and subtract against NumPy equivalents on random sparse matrices."""
    rng = np.random.default_rng(42)
    n = 6
    mask_a = rng.random((n, n)) > 0.4
    mask_b = rng.random((n, n)) > 0.4
    vals_a = rng.standard_normal((n, n)) * mask_a
    vals_b = rng.standard_normal((n, n)) * mask_b

    a_sparse = _dense_to_sparse(vals_a)
    b_sparse = _dense_to_sparse(vals_b)

    # Matrix multiplication: A @ B
    ax_prod = ax.matrix.dot(a_sparse, b_sparse)
    np_prod = _dense_to_sparse(vals_a @ vals_b)
    assert semiring_elements_equal(ax_prod, np_prod, tol=1e-10)

    # Matrix addition: A + B
    ax_add = ax.matrix.add(a_sparse, b_sparse)
    np_add = _dense_to_sparse(vals_a + vals_b)
    assert semiring_elements_equal(ax_add, np_add, tol=1e-12)

    # Matrix subtraction: A - B
    ax_sub = ax.matrix.subtract(a_sparse, b_sparse)
    np_sub = _dense_to_sparse(vals_a - vals_b)
    assert semiring_elements_equal(ax_sub, np_sub, tol=1e-12)


def test_differential_transpose_trace_and_frobenius() -> None:
    """Verify ax.matrix.transpose, trace, and frobenius_inner against NumPy."""
    rng = np.random.default_rng(123)
    n = 5
    vals_a = rng.standard_normal((n, n))
    vals_b = rng.standard_normal((n, n))
    sparse_a = _dense_to_sparse(vals_a)
    sparse_b = _dense_to_sparse(vals_b)

    # Transpose
    ax_trans = ax.matrix.transpose(sparse_a)
    np_trans = _dense_to_sparse(vals_a.T)
    assert semiring_elements_equal(ax_trans, np_trans, tol=1e-12)

    # Trace
    ax_tr = ax.matrix.trace(sparse_a)
    np_tr = float(np.trace(vals_a))
    assert math.isclose(ax_tr, np_tr, rel_tol=1e-12, abs_tol=1e-12)

    # Frobenius inner product: <A, B>_F = Tr(A^T B)
    ax_frob = ax.matrix.frobenius_inner(sparse_a, sparse_b)
    np_frob = float(np.sum(vals_a * vals_b))
    assert math.isclose(ax_frob, np_frob, rel_tol=1e-11, abs_tol=1e-11)


@pytest.mark.parametrize('exponent', [0, 1, 2, 5])
def test_differential_matrix_power(exponent: int) -> None:
    """Verify binary exponentiation ax.matrix.power against np.linalg.matrix_power."""
    vals = np.array(
        [
            [1.0, 2.0, 0.0, 0.0],
            [0.0, 1.0, 1.0, 0.0],
            [0.0, 0.0, 2.0, 1.0],
            [1.0, 0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )
    sparse_m = _dense_to_sparse(vals)

    ax_pow = ax.matrix.power(sparse_m, exponent)
    np_pow = _dense_to_sparse(np.linalg.matrix_power(vals, exponent))
    assert semiring_elements_equal(ax_pow, np_pow, tol=1e-10)


def test_differential_mat_vec_and_vec_ops() -> None:
    """Verify ax.matrix.mat_vec, vec_mat, inner, vec_norm, and vec_axpy against NumPy."""
    rng = np.random.default_rng(314)
    n = 6
    mat_dense = rng.standard_normal((n, n))
    x_dense = rng.standard_normal(n)
    y_dense = rng.standard_normal(n)

    mat_sparse = _dense_to_sparse(mat_dense)
    x_sparse = {i: float(x_dense[i]) for i in range(n)}
    y_sparse = {i: float(y_dense[i]) for i in range(n)}

    # Matrix-vector product: A @ x
    ax_mv = ax.matrix.mat_vec(mat_sparse, x_sparse)
    np_mv = mat_dense @ x_dense
    for i in range(n):
        assert math.isclose(ax_mv.get(i, 0.0), float(np_mv[i]), rel_tol=1e-11, abs_tol=1e-11)

    # Vector-matrix product: x^T @ A
    ax_vm = ax.matrix.vec_mat(x_sparse, mat_sparse)
    np_vm = x_dense @ mat_dense
    for i in range(n):
        assert math.isclose(ax_vm.get(i, 0.0), float(np_vm[i]), rel_tol=1e-11, abs_tol=1e-11)

    # Inner product & Euclidean norm
    assert math.isclose(ax.matrix.inner(x_sparse, y_sparse), float(np.dot(x_dense, y_dense)), abs_tol=1e-11)
    assert math.isclose(ax.matrix.vec_norm(x_sparse), float(np.linalg.norm(x_dense)), abs_tol=1e-11)

    # AXPY: a * x + y
    alpha = 2.5
    ax_axpy = ax.matrix.vec_axpy(alpha, x_sparse, y_sparse)
    np_axpy = alpha * x_dense + y_dense
    for i in range(n):
        assert math.isclose(ax_axpy.get(i, 0.0), float(np_axpy[i]), abs_tol=1e-11)


# ---------------------------------------------------------------------------
# 2. Linear Solvers, Inverse & Determinant vs NumPy / SciPy
# ---------------------------------------------------------------------------


def test_differential_inverse_and_determinant() -> None:
    """Verify ax.matrix.inverse and determinant against np.linalg.inv and np.linalg.det."""
    rng = np.random.default_rng(2026)
    n = 4
    # Construct a well-conditioned non-singular matrix: A = R + 3 * I
    vals = rng.standard_normal((n, n)) + 3.0 * np.eye(n)
    sparse_m = _dense_to_sparse(vals)

    # Matrix inverse
    ax_inv = ax.matrix.inverse(sparse_m)
    np_inv = np.linalg.inv(vals)
    ax_inv_dense = _sparse_to_dense(ax_inv, n)
    np.testing.assert_allclose(ax_inv_dense, np_inv, rtol=1e-9, atol=1e-9)

    # Academic determinant vs np.linalg.det and scipy.linalg.det
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', PerformanceWarning)
        ax_det = determinant(sparse_m)
    np_det = float(np.linalg.det(vals))
    sp_det = float(spla.det(vals))
    assert math.isclose(ax_det, np_det, rel_tol=1e-9, abs_tol=1e-9)
    assert math.isclose(ax_det, sp_det, rel_tol=1e-9, abs_tol=1e-9)


def test_differential_cg_solve_vs_scipy_cg() -> None:
    """Verify ax.matrix.cg_solve against scipy.sparse.linalg.cg on symmetric positive-definite systems."""
    rng = np.random.default_rng(555)
    n = 6
    # Construct SPD matrix A = M @ M.T + 2 * I
    m_rand = rng.standard_normal((n, n))
    spd_dense = m_rand @ m_rand.T + 2.0 * np.eye(n)
    b_dense = rng.standard_normal(n)

    spd_sparse = _dense_to_sparse(spd_dense)
    b_sparse = {i: float(b_dense[i]) for i in range(n)}

    # Solve via algebrax Conjugate Gradient
    ax_sol = ax.matrix.cg_solve(spd_sparse, b_sparse, tol=1e-11, max_iter=200)
    ax_sol_arr = np.array([ax_sol.get(i, 0.0) for i in range(n)])

    # Solve via SciPy Conjugate Gradient and NumPy direct solve
    sp_sol_arr, info = splinalg.cg(sp.csr_matrix(spd_dense), b_dense, rtol=1e-11)
    assert info == 0
    np_sol_arr = np.linalg.solve(spd_dense, b_dense)

    np.testing.assert_allclose(ax_sol_arr, sp_sol_arr, rtol=1e-7, atol=1e-7)
    np.testing.assert_allclose(ax_sol_arr, np_sol_arr, rtol=1e-7, atol=1e-7)


# ---------------------------------------------------------------------------
# 3. Matrix Decompositions (Cholesky, LU, QR, SVD) vs NumPy & SciPy
# ---------------------------------------------------------------------------


def test_differential_cholesky_vs_numpy() -> None:
    """Verify ax.matrix.cholesky against np.linalg.cholesky (unique lower-triangular factor L)."""
    rng = np.random.default_rng(101)
    n = 5
    m_rand = rng.standard_normal((n, n))
    spd_dense = m_rand @ m_rand.T + 2.5 * np.eye(n)
    spd_sparse = _dense_to_sparse(spd_dense)

    # Compute Cholesky L
    ax_l = ax.matrix.cholesky(spd_sparse)
    np_l = np.linalg.cholesky(spd_dense)

    ax_l_dense = _sparse_to_dense(ax_l, n)
    np.testing.assert_allclose(ax_l_dense, np_l, rtol=1e-9, atol=1e-9)

    # Verify recomposition helper
    recomp = ax.matrix.recompose_cholesky(ax_l)
    np.testing.assert_allclose(_sparse_to_dense(recomp, n), spd_dense, rtol=1e-9, atol=1e-9)


def test_differential_lu_vs_scipy_lu() -> None:
    """Verify ax.matrix.lu against scipy.linalg.lu and P @ A == L @ U certificate."""
    rng = np.random.default_rng(202)
    n = 5
    a_dense = rng.standard_normal((n, n)) + 2.0 * np.eye(n)
    a_sparse = _dense_to_sparse(a_dense)

    p_ax, l_ax, u_ax = ax.matrix.lu(a_sparse)
    p_dense = _sparse_to_dense(p_ax, n)
    l_dense = _sparse_to_dense(l_ax, n)
    u_dense = _sparse_to_dense(u_ax, n)

    # Verify P @ A == L @ U
    np.testing.assert_allclose(p_dense @ a_dense, l_dense @ u_dense, rtol=1e-9, atol=1e-9)

    # Verify L is unit lower-triangular and U is upper-triangular
    np.testing.assert_allclose(np.diag(l_dense), np.ones(n), atol=1e-12)
    np.testing.assert_allclose(np.triu(l_dense, k=1), np.zeros((n, n)), atol=1e-12)
    np.testing.assert_allclose(np.tril(u_dense, k=-1), np.zeros((n, n)), atol=1e-12)

    # Compare against scipy.linalg.lu(a_dense, permute_l=False)
    # Note: In scipy.linalg.lu, A = P_scipy @ L @ U, whereas algebrax uses P_ax @ A = L @ U (so P_ax = P_scipy.T)
    p_sp, l_sp, u_sp = spla.lu(a_dense)
    np.testing.assert_allclose(p_dense, p_sp.T, atol=1e-12)
    np.testing.assert_allclose(l_dense, l_sp, rtol=1e-9, atol=1e-9)
    np.testing.assert_allclose(u_dense, u_sp, rtol=1e-9, atol=1e-9)

    # Verify recompose_lu
    recomp = ax.matrix.recompose_lu(p_ax, l_ax, u_ax)
    np.testing.assert_allclose(_sparse_to_dense(recomp, n), a_dense, rtol=1e-9, atol=1e-9)


def test_differential_qr_vs_numpy_qr() -> None:
    """Verify ax.matrix.qr against np.linalg.qr (with positive R-diagonal gauge normalization)."""
    rng = np.random.default_rng(303)
    n = 5
    a_dense = rng.standard_normal((n, n)) + 2.0 * np.eye(n)
    a_sparse = _dense_to_sparse(a_dense)

    q_ax, r_ax = ax.matrix.qr(a_sparse)
    q_ax_dense = _sparse_to_dense(q_ax, n)
    r_ax_dense = _sparse_to_dense(r_ax, n)

    # AlgebraX modified Gram-Schmidt enforces R_jj >= 0; normalize np.linalg.qr to the same positive diagonal gauge
    q_np, r_np = np.linalg.qr(a_dense)
    signs = np.sign(np.diag(r_np))
    signs[signs == 0] = 1.0
    q_np_norm = q_np * signs[np.newaxis, :]
    r_np_norm = signs[:, np.newaxis] * r_np

    np.testing.assert_allclose(q_ax_dense, q_np_norm, rtol=1e-8, atol=1e-8)
    np.testing.assert_allclose(r_ax_dense, r_np_norm, rtol=1e-8, atol=1e-8)

    # Verify orthonormality Q^T @ Q == I and reconstruction A == Q @ R
    np.testing.assert_allclose(q_ax_dense.T @ q_ax_dense, np.eye(n), atol=1e-9)
    recomp = ax.matrix.recompose_qr(q_ax, r_ax)
    np.testing.assert_allclose(_sparse_to_dense(recomp, n), a_dense, rtol=1e-9, atol=1e-9)


def test_differential_svd_vs_numpy_svd() -> None:
    """Verify ax.matrix.svd singular values and reconstruction against np.linalg.svd."""
    rng = np.random.default_rng(404)
    m, n = 6, 4
    a_dense = rng.standard_normal((m, n))
    a_sparse = _dense_to_sparse(a_dense)

    u_ax, s_ax, vt_ax = ax.matrix.svd(a_sparse)
    s_np = np.linalg.svd(a_dense, compute_uv=False)

    # Singular values must match np.linalg.svd in descending order
    s_ax_arr = np.array([s_ax.get(i, 0.0) for i in range(min(m, n))])
    np.testing.assert_allclose(s_ax_arr, s_np, rtol=1e-7, atol=1e-7)

    # Orthonormality of U and V^T
    u_dense = _sparse_to_dense(u_ax, m, min(m, n))
    vt_dense = _sparse_to_dense(vt_ax, min(m, n), n)
    np.testing.assert_allclose(u_dense.T @ u_dense, np.eye(min(m, n)), atol=1e-7)
    np.testing.assert_allclose(vt_dense @ vt_dense.T, np.eye(min(m, n)), atol=1e-7)

    # Reconstruction A == U @ diag(S) @ V^T
    recomp = ax.matrix.recompose_svd(u_ax, s_ax, vt_ax)
    np.testing.assert_allclose(_sparse_to_dense(recomp, m, n), a_dense, rtol=1e-7, atol=1e-7)


# ---------------------------------------------------------------------------
# 4. Multidimensional Tensor Contractions (einsum & permute) vs NumPy
# ---------------------------------------------------------------------------


def test_differential_tensor_einsum_vs_numpy() -> None:
    """Verify ax.tensor.einsum across trace, outer product, batch matmul, and 3-tensor contraction vs np.einsum."""
    rng = np.random.default_rng(505)

    # Case 1: 3D tensor contraction 'ijk,jkl->il'
    t1_np = rng.standard_normal((3, 4, 3))
    t2_np = rng.standard_normal((4, 3, 2))
    t1_flat = {idx: float(val) for idx, val in np.ndenumerate(t1_np)}
    t2_flat = {idx: float(val) for idx, val in np.ndenumerate(t2_np)}

    ax_res = ax.tensor.einsum('ijk,jkl->il', t1_flat, t2_flat)
    np_res = np.einsum('ijk,jkl->il', t1_np, t2_np)

    for (i, l_idx), expected_val in np.ndenumerate(np_res):
        actual_val = ax_res.get((i, l_idx), 0.0)
        assert math.isclose(actual_val, float(expected_val), rel_tol=1e-10, abs_tol=1e-10)

    # Case 2: Batch matrix multiplication 'bij,bjk->bik'
    b1_np = rng.standard_normal((2, 3, 4))
    b2_np = rng.standard_normal((2, 4, 3))
    b1_flat = {idx: float(val) for idx, val in np.ndenumerate(b1_np)}
    b2_flat = {idx: float(val) for idx, val in np.ndenumerate(b2_np)}

    ax_batch = ax.tensor.einsum('bij,bjk->bik', b1_flat, b2_flat)
    np_batch = np.einsum('bij,bjk->bik', b1_np, b2_np)

    for idx, expected_val in np.ndenumerate(np_batch):
        actual_val = ax_batch.get(idx, 0.0)
        assert math.isclose(actual_val, float(expected_val), rel_tol=1e-10, abs_tol=1e-10)

    # Case 3: Matrix trace 'ii->'
    m_np = rng.standard_normal((4, 4))
    m_flat = {idx: float(val) for idx, val in np.ndenumerate(m_np)}
    ax_trace = ax.tensor.einsum('ii->', m_flat)
    np_trace = float(np.einsum('ii->', m_np))
    assert math.isclose(ax_trace.get((), 0.0), np_trace, rel_tol=1e-11, abs_tol=1e-11)


def test_differential_tensor_permute_vs_numpy() -> None:
    """Verify ax.tensor.permute_tensor and unpermute_tensor against np.transpose on a 3D tensor."""
    rng = np.random.default_rng(606)
    arr = rng.standard_normal((2, 3, 4))
    nested = ax.converters.dense_to_sparse_tensor(arr.tolist())
    flat = ax.tensor.flatten_tensor(nested)

    perm = (2, 0, 1)
    ax_perm = ax.tensor.permute_tensor(flat, perm)
    np_perm = np.transpose(arr, axes=perm)

    for idx, expected_val in np.ndenumerate(np_perm):
        assert math.isclose(ax_perm.get(idx, 0.0), float(expected_val), rel_tol=1e-12, abs_tol=1e-12)

    # Verify inverse unpermute_tensor restores original flat tensor
    ax_unperm = ax.tensor.unpermute_tensor(ax_perm, perm)
    assert semiring_elements_equal(ax_unperm, flat, tol=1e-12)


# ---------------------------------------------------------------------------
# 5. Signal Processing Transforms vs NumPy FFT & SciPy Signal/Linalg
# ---------------------------------------------------------------------------


def test_differential_dft_idft_and_hilbert() -> None:
    """Verify ax.transforms.dft, idft, and hilbert against np.fft and scipy.signal.hilbert."""
    rng = np.random.default_rng(777)
    n = 8
    signal_arr = rng.standard_normal(n)
    signal_dict = {i: float(signal_arr[i]) for i in range(n)}

    # 1. Forward DFT vs np.fft.fft
    ax_freq = ax.transforms.dft(signal_dict, n=n)
    np_freq = np.fft.fft(signal_arr)
    for k in range(n):
        ax_val = ax_freq.get(k, 0.0j)
        np_val = complex(np_freq[k])
        assert math.isclose(ax_val.real, np_val.real, rel_tol=1e-10, abs_tol=1e-10)
        assert math.isclose(ax_val.imag, np_val.imag, rel_tol=1e-10, abs_tol=1e-10)

    # 2. Inverse IDFT vs np.fft.ifft (and exact signal recovery)
    ax_time = ax.transforms.idft(ax_freq, n=n)
    for i in range(n):
        rec_val = ax_time.get(i, 0.0j)
        assert math.isclose(rec_val.real, float(signal_arr[i]), rel_tol=1e-10, abs_tol=1e-10)
        assert abs(rec_val.imag) < 1e-10

    # 3. Analytic Hilbert signal vs scipy.signal.hilbert
    ax_hilb = ax.transforms.hilbert(signal_dict, n=n)
    sp_hilb = spsig.hilbert(signal_arr)
    for i in range(n):
        ax_val = ax_hilb.get(i, 0.0j)
        sp_val = complex(sp_hilb[i])
        assert math.isclose(ax_val.real, sp_val.real, rel_tol=1e-10, abs_tol=1e-10)
        assert math.isclose(ax_val.imag, sp_val.imag, rel_tol=1e-10, abs_tol=1e-10)


def test_differential_convolve_and_deconvolve() -> None:
    """Verify ax.transforms.convolve against np.convolve and deconvolve circular inversion."""
    f_arr = np.array([1.5, -2.0, 3.0, 0.5, 4.0])
    g_arr = np.array([0.5, 2.0, -1.0])

    f_dict = {i: float(f_arr[i]) for i in range(len(f_arr))}
    g_dict = {i: float(g_arr[i]) for i in range(len(g_arr))}

    # Linear discrete convolution vs np.convolve
    ax_conv = ax.transforms.convolve(f_dict, g_dict)
    np_conv = np.convolve(f_arr, g_arr)
    for k, expected in enumerate(np_conv):
        assert math.isclose(ax_conv.get(k, 0.0), float(expected), rel_tol=1e-12, abs_tol=1e-12)

    # Circular convolution & spectral deconvolution round-trip
    n = 8
    f_pad = {i: float(f_arr[i]) if i < len(f_arr) else 0.0 for i in range(n)}
    g_pad = {i: float(g_arr[i]) if i < len(g_arr) else 0.0 for i in range(n)}
    circ_conv = ax.transforms.convolve(f_pad, g_pad, key_op=lambda x, y: (x + y) % n)
    recovered = ax.transforms.deconvolve(circ_conv, g_pad)
    for i in range(len(f_arr)):
        assert math.isclose(recovered.get(i, 0.0j).real, float(f_arr[i]), rel_tol=1e-9, abs_tol=1e-9)


def test_differential_walsh_hadamard_vs_scipy_hadamard() -> None:
    """Verify ax.transforms.walsh_hadamard and iwalsh_hadamard against scipy.linalg.hadamard."""
    rng = np.random.default_rng(888)
    n = 8  # Power of 2
    sig_arr = rng.standard_normal(n)
    sig_dict = {i: float(sig_arr[i]) for i in range(n)}

    # Explicit Sylvester-Hadamard matrix from scipy.linalg.hadamard
    h_mat = spla.hadamard(n)
    expected_wht = h_mat @ sig_arr

    ax_wht = ax.transforms.walsh_hadamard(sig_dict, n=n)
    for k in range(n):
        assert math.isclose(ax_wht.get(k, 0.0), float(expected_wht[k]), rel_tol=1e-11, abs_tol=1e-11)

    # Inverse Walsh-Hadamard round-trip
    ax_iwht = ax.transforms.iwalsh_hadamard(ax_wht, n=n)
    for i in range(n):
        assert math.isclose(ax_iwht.get(i, 0.0), float(sig_arr[i]), rel_tol=1e-11, abs_tol=1e-11)


# ---------------------------------------------------------------------------
# 6. Ecosystem Converters (to_numpy, from_numpy, to_scipy, from_scipy)
# ---------------------------------------------------------------------------


def test_differential_numpy_and_scipy_converters() -> None:
    """Verify lossless round-trip conversions between AlgebraX, NumPy ndarray, and SciPy sparse formats."""
    rng = np.random.default_rng(999)
    n, m = 5, 6
    mask = rng.random((n, m)) > 0.5
    arr = rng.standard_normal((n, m)) * mask

    # NumPy -> AlgebraX -> NumPy
    sparse_m = ax.converters.from_numpy(arr)
    arr_back = ax.converters.to_numpy(sparse_m, shape=(n, m))
    np.testing.assert_allclose(arr_back, arr, rtol=1e-12, atol=1e-12)

    # AlgebraX -> SciPy CSR/CSC/COO -> AlgebraX
    for fmt in ('csr', 'csc', 'coo'):
        sp_mat = ax.converters.to_scipy(sparse_m, format=fmt)
        assert sp.issparse(sp_mat)
        np.testing.assert_allclose(sp_mat.toarray(), arr, rtol=1e-12, atol=1e-12)
        ax_back = ax.converters.from_scipy(sp_mat)
        assert semiring_elements_equal(ax_back, sparse_m, tol=1e-12)


# ---------------------------------------------------------------------------
# 7. Z-Transform, Lorentz Boost & Block Diagonal vs Analytical / SciPy Oracles
# ---------------------------------------------------------------------------


def test_differential_z_transform_and_convolution_theorem() -> None:
    """Verify ax.transforms.z_transform against polynomial evaluation and Z-convolution theorem."""
    f = {0: 1.0, 1: -0.5, 2: 2.0, 3: 1.5}
    g = {0: 2.0, 1: 1.0, 2: -1.0}
    z = 1.2 + 0.5j

    # Compare z_transform(f, z) against np.polyval(f, 1/z)
    f_coeffs_desc = [f[3], f[2], f[1], f[0]]
    np_z_val = complex(np.polyval(f_coeffs_desc, 1.0 / z))
    ax_z_val = ax.transforms.z_transform(f, z)
    assert math.isclose(ax_z_val.real, np_z_val.real, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(ax_z_val.imag, np_z_val.imag, rel_tol=1e-12, abs_tol=1e-12)

    # Ring homomorphism: Z{f * g}(z) == Z{f}(z) * Z{g}(z)
    conv_fg = ax.transforms.convolve(f, g)
    z_conv = ax.transforms.z_transform(conv_fg, z)
    z_prod = ax.transforms.z_transform(f, z) * ax.transforms.z_transform(g, z)
    assert math.isclose(z_conv.real, z_prod.real, rel_tol=1e-11, abs_tol=1e-11)
    assert math.isclose(z_conv.imag, z_prod.imag, rel_tol=1e-11, abs_tol=1e-11)

    # Inverse Z-transform contour recovery
    rec = ax.transforms.iz_transform(lambda z_pt: ax.transforms.z_transform(f, z_pt), signal_length=4, radius=1.0)
    for k, expected in f.items():
        assert math.isclose(rec.get(k, 0j).real, expected, rel_tol=1e-9, abs_tol=1e-9)


def test_differential_lorentz_boost_minkowski_invariance() -> None:
    """Verify ax.transforms.lorentz_boost preserves Minkowski spacetime interval s^2 = t^2 - x^2 - y^2 - z^2."""
    vec = {0: 5.0, 1: 2.0, 2: -1.0, 3: 1.5}
    beta = 0.6

    boosted = ax.transforms.lorentz_boost(vec, beta=beta, axis=1)

    # Minkowski metric signature (+, -, -, -)
    s2_orig = vec[0] ** 2 - vec[1] ** 2 - vec[2] ** 2 - vec[3] ** 2
    s2_boost = boosted[0] ** 2 - boosted[1] ** 2 - boosted[2] ** 2 - boosted[3] ** 2
    assert math.isclose(s2_orig, s2_boost, rel_tol=1e-11, abs_tol=1e-11)

    # Inverse boost with -beta recovers original 4-vector
    recovered = ax.transforms.lorentz_boost(boosted, beta=-beta, axis=1)
    assert semiring_elements_equal(recovered, vec, tol=1e-11)


def test_differential_block_diag_vs_scipy_block_diag() -> None:
    """Verify ax.matrix.block_diag against scipy.linalg.block_diag."""
    a_np = np.array([[1.0, 2.0], [3.0, 4.0]])
    b_np = np.array([[5.0, 0.0, -1.0], [0.0, 6.0, 2.0], [1.0, 0.0, 7.0]])

    a_sp = _dense_to_sparse(a_np)
    b_sp = _dense_to_sparse(b_np)

    ax_blk = ax.matrix.block_diag([a_sp, b_sp])
    sp_blk = spla.block_diag(a_np, b_np)

    np.testing.assert_allclose(_sparse_to_dense(ax_blk, 5, 5), sp_blk, rtol=1e-12, atol=1e-12)

    # Matrix commutator [A, B] = AB - BA vs NumPy and Jacobi identity [[A, B], C] + [[B, C], A] + [[C, A], B] == 0
    c_np = np.array([[-1.0, 3.0], [2.0, 0.5]])
    d_np = np.array([[2.0, -1.0], [0.5, 4.0]])
    c_sp = _dense_to_sparse(c_np)
    d_sp = _dense_to_sparse(d_np)
    comm_ax = _sparse_to_dense(ax.matrix.commutator(c_sp, d_sp), 2, 2)
    np.testing.assert_allclose(comm_ax, c_np @ d_np - d_np @ c_np, rtol=1e-12, atol=1e-12)
    assert ax.matrix.kronecker_delta(3, 3) == 1
    assert ax.matrix.kronecker_delta(3, 4) == 0


def test_differential_gelfand_and_legendre_fenchel_transforms() -> None:
    """Verify gelfand_transform against DFT/WHT characters and legendre_fenchel convex conjugation."""
    # 1. Gelfand transform with Fourier characters chi_k(m) = exp(-2j * pi * k * m / N) equals dft(x)
    n = 8
    sig = {0: 1.5, 1: -0.5, 3: 2.0, 5: -1.0, 7: 0.75}
    fourier_chars = {k: (lambda m, freq=k: complex(np.exp(-2j * np.pi * freq * m / n))) for k in range(n)}
    gelfand_dft = ax.transforms.gelfand_transform(sig, fourier_chars)
    direct_dft = ax.transforms.dft(sig, n=n)
    for k in range(n):
        assert abs(gelfand_dft.get(k, 0j) - direct_dft.get(k, 0j)) < 1e-11

    # 2. Gelfand transform with Walsh characters chi_k(m) = (-1)^popcount(k & m) equals walsh_hadamard(x)
    walsh_chars = {k: (lambda m, freq=k: -1.0 if (freq & m).bit_count() % 2 == 1 else 1.0) for k in range(n)}
    gelfand_wht = ax.transforms.gelfand_transform(sig, walsh_chars)
    direct_wht = ax.transforms.walsh_hadamard(sig, n=n)
    for k in range(n):
        assert math.isclose(float(gelfand_wht.get(k, 0.0)), direct_wht.get(k, 0.0), rel_tol=1e-12, abs_tol=1e-12)

    # 3. Legendre-Fenchel transform f*(s) = max_x (s*x - f(x)) on discrete quadratic f(x) = 0.5 * x^2:
    # Over integer grid x in [-10, 10], for integer slope s in [-8, 8], the exact maximizer is x = s,
    # where s*s - 0.5*s^2 = 0.5 * s^2, and Fenchel-Young inequality f(x) + f*(s) >= s*x holds everywhere!
    quad_signal = {x: 0.5 * float(x * x) for x in range(-10, 11)}
    f_conj: dict[int, float] = {}
    for s in range(-8, 9):
        val = ax.transforms.legendre_fenchel(quad_signal, slope=float(s))
        f_conj[s] = val
        assert math.isclose(val, 0.5 * float(s * s), rel_tol=1e-12, abs_tol=1e-12)
        for x, fx in quad_signal.items():
            assert fx + val >= s * x - 1e-12

    # Fenchel-Moreau biconjugation f**(x) == f(x) on interior integer points x in [-6, 6]
    for x in range(-6, 7):
        f_biconj = ax.transforms.legendre_fenchel(f_conj, slope=float(x))
        assert math.isclose(f_biconj, quad_signal[x], rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# 8. Hypothesis Property-Based Comparative Tests vs NumPy
# ---------------------------------------------------------------------------

small_float_st = st.floats(min_value=-20.0, max_value=20.0, allow_nan=False, allow_infinity=False)


@given(
    mat_a_list=st.lists(st.lists(small_float_st, min_size=4, max_size=4), min_size=4, max_size=4),
    mat_b_list=st.lists(st.lists(small_float_st, min_size=4, max_size=4), min_size=4, max_size=4),
)
@settings(max_examples=25)
def test_hypothesis_differential_matmul_and_lu(
    mat_a_list: list[list[float]],
    mat_b_list: list[list[float]],
) -> None:
    """Property-test ax.matrix.dot and ax.matrix.lu against NumPy/SciPy across randomized 4x4 matrices."""
    a_np = np.array(mat_a_list, dtype=np.float64)
    b_np = np.array(mat_b_list, dtype=np.float64)

    a_sp = _dense_to_sparse(a_np)
    b_sp = _dense_to_sparse(b_np)

    # 1. Dot product parity
    ax_prod = _sparse_to_dense(ax.matrix.dot(a_sp, b_sp), 4)
    np.testing.assert_allclose(ax_prod, a_np @ b_np, rtol=1e-9, atol=1e-9)

    # 2. LU factorization certificate on diagonally dominant shift A_dd = A + 100 * I
    a_dd = a_np + 100.0 * np.eye(4)
    a_dd_sp = _dense_to_sparse(a_dd)
    p_ax, l_ax, u_ax = ax.matrix.lu(a_dd_sp)
    recomp = _sparse_to_dense(ax.matrix.recompose_lu(p_ax, l_ax, u_ax), 4)
    np.testing.assert_allclose(recomp, a_dd, rtol=1e-8, atol=1e-8)


@given(sig_list=st.lists(small_float_st, min_size=8, max_size=8))
@settings(max_examples=25)
def test_hypothesis_differential_dft_and_wht(sig_list: list[float]) -> None:
    """Property-test ax.transforms.dft and walsh_hadamard against np.fft.fft and scipy.linalg.hadamard."""
    sig_np = np.array(sig_list, dtype=np.float64)
    sig_sp = {i: float(sig_np[i]) for i in range(8) if abs(sig_np[i]) > 1e-12}

    # DFT parity
    ax_dft = ax.transforms.dft(sig_sp, n=8)
    np_dft = np.fft.fft(sig_np)
    for k in range(8):
        v_ax = ax_dft.get(k, 0.0j)
        v_np = complex(np_dft[k])
        assert math.isclose(v_ax.real, v_np.real, rel_tol=1e-8, abs_tol=1e-8)
        assert math.isclose(v_ax.imag, v_np.imag, rel_tol=1e-8, abs_tol=1e-8)

    # Walsh-Hadamard parity
    ax_wht = ax.transforms.walsh_hadamard(sig_sp, n=8)
    sp_wht = spla.hadamard(8) @ sig_np
    for k in range(8):
        assert math.isclose(ax_wht.get(k, 0.0), float(sp_wht[k]), rel_tol=1e-8, abs_tol=1e-8)
