import sys
from typing import Any

import pytest
from mappingtools.structures import Dictifier, LazyDictifier, dictify

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from _generators import nested_dict, sparse_matrix, sparse_signal, unbalanced_dict

import algebrax as ax

# region Data Generators


def naive_dense_multiply(a_mat: list[list[float]], b_mat: list[list[float]]) -> list[list[float]]:
    rows_a = len(a_mat)
    cols_a = len(a_mat[0])
    cols_b = len(b_mat[0])
    c_mat = [[0.0 for _ in range(cols_b)] for _ in range(rows_a)]
    for i in range(rows_a):
        for j in range(cols_b):
            total = 0.0
            for k in range(cols_a):
                total += a_mat[i][k] * b_mat[k][j]
            c_mat[i][j] = total
    return c_mat


# endregion


# region Matrix Benchmarks


@pytest.mark.benchmark(group="matrix-dot")
@pytest.mark.parametrize("density", [0.05, 0.25, 0.50, 0.75])
def test_benchmark_matrix_dot(benchmark, density: float):
    m_a = sparse_matrix(80, 80, density, seed=1)
    m_b = sparse_matrix(80, 80, density, seed=2)

    result = benchmark(ax.matrix.dot, m_a, m_b)
    assert result is not None


@pytest.mark.benchmark(group="matrix-dot-vs-naive")
@pytest.mark.parametrize("implementation", ["sparse_dot", "naive_dense"])
def test_benchmark_matrix_dot_vs_naive(benchmark, implementation: str):
    n_dim = 15
    density = 0.20
    sparse_a = sparse_matrix(n_dim, n_dim, density, seed=1)
    sparse_b = sparse_matrix(n_dim, n_dim, density, seed=2)

    if implementation == "sparse_dot":
        result = benchmark(ax.matrix.dot, sparse_a, sparse_b)
        assert result is not None
    else:
        dense_a = ax.converters.sparse_to_dense_matrix(sparse_a, shape=(n_dim, n_dim))
        dense_b = ax.converters.sparse_to_dense_matrix(sparse_b, shape=(n_dim, n_dim))
        result = benchmark(naive_dense_multiply, dense_a, dense_b)
        assert result is not None


@pytest.mark.benchmark(group="matrix-dot-tropical")
@pytest.mark.parametrize("density", [0.05, 0.25, 0.50])
def test_benchmark_matrix_dot_tropical(benchmark, density: float):
    m_a = sparse_matrix(60, 60, density, seed=1)
    m_b = sparse_matrix(60, 60, density, seed=2)
    trop = ax.semiring.TropicalSemiring()

    result = benchmark(ax.matrix.dot, m_a, m_b, semiring=trop)
    assert result is not None


@pytest.mark.benchmark(group="matrix-transpose")
@pytest.mark.parametrize("density", [0.10, 0.50])
def test_benchmark_matrix_transpose(benchmark, density: float):
    m_a = sparse_matrix(100, 100, density)

    result = benchmark(ax.matrix.transpose, m_a)
    assert result is not None


# endregion


# region Flatten & Converters Benchmarks


@pytest.mark.benchmark(group="converters-nested-to-flat")
@pytest.mark.parametrize(
    ("scenario", "tree"),
    [
        ("balanced_d5_w5", nested_dict(depth=5, width=5)),
        ("wide_d2_w100", nested_dict(depth=2, width=100)),
        ("deep_d50_w1", nested_dict(depth=50, width=1)),
        ("unbalanced", unbalanced_dict(depth=6, max_width=4)),
    ],
)
def test_benchmark_nested_to_flat(benchmark, scenario: str, tree: Any):
    result = benchmark(ax.converters.nested_to_flat, tree)
    assert result is not None


# endregion


# region Mappingtools & Dictifier Benchmarks


class Greeter:

    def __init__(self, i: int):
        self.i = i

    def greet(self) -> str:
        return f"Hello {self.i}"


@dictify
class GreeterCollection:

    def __init__(self, i: int):
        self.i = i

    def greet(self) -> str:
        return f"Hello {self.i}"


@pytest.mark.benchmark(group="mappingtools-dictifier")
@pytest.mark.parametrize("mode", ["native_loop", "dictifier_generic", "dictify_decorator", "lazy_dictifier"])
def test_benchmark_dictifier_modes(benchmark, mode: str):
    size = 100
    data = {str(i): Greeter(i) for i in range(size)}

    if mode == "native_loop":
        result = benchmark(lambda: {k: v.greet() for k, v in data.items()})
        assert len(result) == size
    elif mode == "dictifier_generic":
        dictifier = Dictifier[Greeter](data)
        result = benchmark(lambda: dictifier.greet())
        assert len(result) == size
    elif mode == "dictify_decorator":
        dec_data = {str(i): GreeterCollection.Item(i) for i in range(size)}
        collection = GreeterCollection(dec_data)
        result = benchmark(lambda: collection.greet())
        assert len(result) == size
    elif mode == "lazy_dictifier":
        lazy = LazyDictifier[Greeter](data)
        result = benchmark(lambda: dict(lazy.greet()))
        assert len(result) == size


# endregion


# region Tensor Benchmarks


@pytest.mark.benchmark(group="tensor-einsum")
@pytest.mark.parametrize("density", [0.05, 0.25, 0.50])
def test_benchmark_tensor_einsum(benchmark, density: float):
    t1 = sparse_matrix(50, 50, density, seed=1)
    t2 = sparse_matrix(50, 50, density, seed=2)

    result = benchmark(ax.tensor.einsum, "ij,jk->ik", t1, t2)
    assert result is not None


# endregion


# region Transforms Benchmarks


@pytest.mark.benchmark(group="transforms-dft")
@pytest.mark.parametrize("density", [0.10, 0.50])
def test_benchmark_transforms_dft(benchmark, density: float):
    sig = sparse_signal(150, density)

    result = benchmark(ax.transforms.dft, sig, 150)
    assert result is not None


@pytest.mark.benchmark(group="transforms-convolve")
@pytest.mark.parametrize("density", [0.10, 0.50])
def test_benchmark_transforms_convolve(benchmark, density: float):
    f = sparse_signal(100, density, seed=1)
    g = sparse_signal(100, density, seed=2)

    result = benchmark(ax.transforms.convolve, f, g)
    assert result is not None


# endregion


# region Homology & Trie Benchmarks


@pytest.mark.benchmark(group="homology-betti")
def test_benchmark_homology_betti(benchmark):
    sc = ax.homology.SimplicialComplex([(0, 1), (1, 2), (2, 0)])

    result = benchmark(sc.betti_numbers, max_k=1)
    assert result == {0: 1, 1: 1}


@pytest.mark.benchmark(group="trie-insertion")
def test_benchmark_trie_insertion(benchmark):
    def insert_keys():
        trie = ax.trie.AlgebraicTrie()
        for i in range(200):
            trie[(i, i + 1, i + 2)] = i * 1.5
        return trie

    result = benchmark(insert_keys)
    assert len(result) == 200


# endregion
