"""Benchmarks for the linear algebra core: matrix products, invariants and factorizations."""

import sys

import pytest

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from _generators import sparse_matrix, sparse_signal, symmetric_positive_definite

import algebrax as ax

# region Core Operations


@pytest.mark.benchmark(group="matrix-add")
@pytest.mark.parametrize("density", [0.10, 0.50])
def test_benchmark_matrix_add(benchmark, density: float):
    m_a = sparse_matrix(120, 120, density, seed=1)
    m_b = sparse_matrix(120, 120, density, seed=2)

    result = benchmark(ax.matrix.add, m_a, m_b)
    assert result is not None


@pytest.mark.benchmark(group="matrix-mat-vec")
@pytest.mark.parametrize("density", [0.10, 0.50])
def test_benchmark_matrix_mat_vec(benchmark, density: float):
    m_a = sparse_matrix(200, 200, density, seed=1)
    vec = sparse_signal(200, 0.5, seed=2)

    result = benchmark(ax.matrix.mat_vec, m_a, vec)
    assert result is not None


@pytest.mark.benchmark(group="matrix-power")
@pytest.mark.parametrize("exponent", [4, 16])
def test_benchmark_matrix_power(benchmark, exponent: int):
    m_a = sparse_matrix(30, 30, 0.15, seed=1)

    result = benchmark(ax.matrix.power, m_a, exponent)
    assert result is not None


@pytest.mark.benchmark(group="matrix-power")
def test_benchmark_matrix_power_tropical(benchmark):
    """All-pairs shortest paths via repeated squaring over the tropical semiring."""
    m_a = sparse_matrix(30, 30, 0.15, seed=1)
    trop = ax.semiring.TropicalSemiring()

    result = benchmark(ax.matrix.power, m_a, 8, trop)
    assert result is not None


@pytest.mark.benchmark(group="matrix-inner")
def test_benchmark_matrix_inner(benchmark):
    v_a = sparse_signal(5_000, 0.5, seed=1)
    v_b = sparse_signal(5_000, 0.5, seed=2)

    result = benchmark(ax.matrix.inner, v_a, v_b)
    assert result is not None


# endregion


# region Academic Invariants


@pytest.mark.benchmark(group="matrix-determinant")
@pytest.mark.parametrize("size", [6, 8])
def test_benchmark_matrix_determinant(benchmark, size: int):
    m_a = symmetric_positive_definite(size, seed=1)

    result = benchmark(ax.matrix.determinant, m_a)
    assert result is not None


@pytest.mark.benchmark(group="matrix-inverse")
def test_benchmark_matrix_inverse(benchmark):
    m_a = symmetric_positive_definite(6, seed=1)

    result = benchmark(ax.matrix.inverse, m_a)
    assert result is not None


@pytest.mark.benchmark(group="matrix-eigen-centrality")
def test_benchmark_matrix_eigen_centrality(benchmark):
    m_a = sparse_matrix(80, 80, 0.15, seed=1)

    result = benchmark(ax.matrix.eigen_centrality, m_a)
    assert result is not None


# endregion


# region Decompositions


@pytest.mark.benchmark(group="matrix-decompose")
@pytest.mark.parametrize("size", [12, 24])
def test_benchmark_matrix_lu(benchmark, size: int):
    m_a = symmetric_positive_definite(size, seed=1)

    result = benchmark(ax.matrix.lu, m_a)
    assert result is not None


@pytest.mark.benchmark(group="matrix-decompose")
@pytest.mark.parametrize("size", [12, 24])
def test_benchmark_matrix_qr(benchmark, size: int):
    m_a = symmetric_positive_definite(size, seed=1)

    result = benchmark(ax.matrix.qr, m_a)
    assert result is not None


@pytest.mark.benchmark(group="matrix-decompose")
def test_benchmark_matrix_cholesky(benchmark):
    m_a = symmetric_positive_definite(24, seed=1)

    result = benchmark(ax.matrix.cholesky, m_a)
    assert result is not None


@pytest.mark.benchmark(group="matrix-decompose")
@pytest.mark.parametrize("rank", [2, 6])
def test_benchmark_matrix_svd(benchmark, rank: int):
    m_a = symmetric_positive_definite(16, seed=1)

    result = benchmark(ax.matrix.svd, m_a, rank)
    assert result is not None


# endregion


# region Tensors


@pytest.mark.benchmark(group="tensor-outer")
def test_benchmark_tensor_outer_product(benchmark):
    v_a = sparse_signal(60, 0.5, seed=1)
    v_b = sparse_signal(60, 0.5, seed=2)

    result = benchmark(ax.tensor.outer_product, v_a, v_b)
    assert result is not None


@pytest.mark.benchmark(group="tensor-flatten")
def test_benchmark_tensor_flatten(benchmark):
    tensor = {i: sparse_matrix(20, 20, 0.3, seed=i) for i in range(5)}

    result = benchmark(ax.tensor.flatten_tensor, tensor)
    assert result is not None


@pytest.mark.benchmark(group="tensor-permute")
def test_benchmark_tensor_permute(benchmark):
    tensor = ax.tensor.flatten_tensor({i: sparse_matrix(20, 20, 0.3, seed=i) for i in range(5)})

    result = benchmark(ax.tensor.permute_tensor, tensor, (2, 0, 1))
    assert result is not None


# endregion
