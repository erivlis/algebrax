"""
Differential testing against NumPy reference oracle.

Verifies that algebrax sparse matrix and transform operations produce results
numerically equivalent to NumPy reference dense implementations (McKeeman 1998).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import algebrax as ax
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.differential]


def _sparse_to_dense(m: dict[int, dict[int, float]], n: int) -> np.ndarray:
    """Convert an algebrax sparse dict matrix to a dense NumPy array."""
    res = np.zeros((n, n), dtype=np.float64)
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
# Differential 1: Matrix Multiplication vs NumPy Dot Product
# ---------------------------------------------------------------------------


def test_differential_matrix_multiplication() -> None:
    """Verify ax.matrix.dot against np.dot on random structured sparse matrices."""
    np.random.seed(42)
    n = 6
    # Create two random sparse matrices with 40% density
    mask_a = np.random.rand(n, n) > 0.6
    mask_b = np.random.rand(n, n) > 0.6
    vals_a = np.random.randn(n, n) * mask_a
    vals_b = np.random.randn(n, n) * mask_b

    a_sparse = _dense_to_sparse(vals_a)
    b_sparse = _dense_to_sparse(vals_b)

    # Compute via algebrax
    ax_prod = ax.matrix.dot(a_sparse, b_sparse)

    # Compute via NumPy
    np_prod = vals_a @ vals_b
    expected_sparse = _dense_to_sparse(np_prod)

    assert semiring_elements_equal(ax_prod, expected_sparse, tol=1e-10)


# ---------------------------------------------------------------------------
# Differential 2: Matrix Transpose and Trace vs NumPy
# ---------------------------------------------------------------------------


def test_differential_transpose_and_trace() -> None:
    """Verify ax.matrix.transpose and ax.matrix.trace against NumPy equivalents."""
    np.random.seed(123)
    n = 5
    vals = np.random.randn(n, n)
    sparse_m = _dense_to_sparse(vals)

    # Transpose differential
    ax_trans = ax.matrix.transpose(sparse_m)
    np_trans_sparse = _dense_to_sparse(vals.T)
    assert semiring_elements_equal(ax_trans, np_trans_sparse, tol=1e-12)

    # Trace differential
    ax_tr = ax.matrix.trace(sparse_m)
    np_tr = float(np.trace(vals))
    assert math.isclose(ax_tr, np_tr, rel_tol=1e-12, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Differential 3: Matrix Power vs np.linalg.matrix_power
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('exponent', [0, 1, 2, 4])
def test_differential_matrix_power(exponent: int) -> None:
    """Verify binary exponentiation ax.matrix.power against np.linalg.matrix_power."""
    np.random.seed(99)
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
    np_pow = np.linalg.matrix_power(vals, exponent)
    np_pow_sparse = _dense_to_sparse(np_pow)

    assert semiring_elements_equal(ax_pow, np_pow_sparse, tol=1e-10)


# ---------------------------------------------------------------------------
# Differential 4: 1D Discrete Fourier Transform vs np.fft.fft
# ---------------------------------------------------------------------------


def test_differential_dft() -> None:
    """Verify ax.transforms.dft against np.fft.fft reference signal transform."""
    np.random.seed(777)
    n = 8
    signal_arr = np.random.randn(n)
    signal_dict = {i: float(signal_arr[i]) for i in range(n)}

    # Compute via algebrax
    ax_freq = ax.transforms.dft(signal_dict, n=n)

    # Compute via NumPy FFT
    np_freq = np.fft.fft(signal_arr)

    # Verify complex frequency coefficients match
    for k in range(n):
        ax_val = ax_freq.get(k, 0.0j)
        np_val = complex(np_freq[k])
        assert math.isclose(ax_val.real, np_val.real, rel_tol=1e-10, abs_tol=1e-10)
        assert math.isclose(ax_val.imag, np_val.imag, rel_tol=1e-10, abs_tol=1e-10)
