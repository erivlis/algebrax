"""Benchmarks for the algebraic structures: semirings, Galois fields, Clifford algebra and groups."""

import math
import sys

import pytest

sys.path.insert(0, "src")
sys.path.insert(0, ".")

from _generators import multivector, rng, sparse_matrix

import algebrax as ax

SEMIRINGS = {
    "standard": ax.semiring.StandardSemiring,
    "tropical": ax.semiring.TropicalSemiring,
    "arctic": ax.semiring.ArcticSemiring,
    "viterbi": ax.semiring.ViterbiSemiring,
    "bottleneck": ax.semiring.BottleneckSemiring,
    "log": ax.semiring.LogSemiring,
    "boolean": ax.semiring.BooleanSemiring,
}

# region Semiring Dispatch


@pytest.mark.benchmark(group="semiring-matrix-dot")
@pytest.mark.parametrize("name", list(SEMIRINGS))
def test_benchmark_semiring_matrix_dot(benchmark, name: str):
    """Same product, different algebra: isolates the cost of the semiring dispatch."""
    semiring = SEMIRINGS[name]()
    m_a = sparse_matrix(40, 40, 0.25, seed=1)
    m_b = sparse_matrix(40, 40, 0.25, seed=2)

    if name == "boolean":
        m_a = {r: dict.fromkeys(row, True) for r, row in m_a.items()}
        m_b = {r: dict.fromkeys(row, True) for r, row in m_b.items()}

    result = benchmark(ax.matrix.dot, m_a, m_b, semiring=semiring)
    assert result is not None


@pytest.mark.benchmark(group="semiring-elementwise")
@pytest.mark.parametrize("name", ["standard", "tropical", "viterbi", "log"])
def test_benchmark_semiring_elementwise(benchmark, name: str):
    """Raw cost of the `add` / `mul` primitives, without any container overhead."""
    semiring = SEMIRINGS[name]()
    rand = rng(7)
    values = [rand.uniform(0.01, 0.99) for _ in range(500)]

    def fold():
        acc = semiring.one
        for value in values:
            acc = semiring.add(semiring.mul(acc, value), value)
        return acc

    result = benchmark(fold)
    assert result is not None


@pytest.mark.benchmark(group="semiring-verification")
@pytest.mark.parametrize("name", ["Standard", "Tropical", "Boolean", "Expectation"])
def test_benchmark_verify_semiring_laws(benchmark, name: str):
    semiring, samples = ax.verification.get_semiring_samples(name)

    result = benchmark(ax.verification.verify_semiring_laws, semiring, samples)
    assert all(result.values())


# endregion


# region Galois Fields


@pytest.mark.benchmark(group="galois-matrix-mul")
def test_benchmark_galois_matrix_mul(benchmark):
    def gf_matrix(seed: int):
        """Matrix whose entries are GF(2^8) elements, i.e. polynomials {exponent: coefficient}."""
        local = rng(seed)
        return {
            r: {
                c: {e: 1 for e in range(8) if local.random() < 0.5} or {0: 1}
                for c in range(12)
                if local.random() < 0.4
            }
            for r in range(12)
        }

    m_a = gf_matrix(11)
    m_b = gf_matrix(12)

    result = benchmark(ax.galois.gf_matrix_mul, m_a, m_b)
    assert result is not None


@pytest.mark.benchmark(group="galois-semiring")
def test_benchmark_galois_semiring_mul(benchmark):
    gf = ax.semiring.GaloisFieldSemiring(2)
    a = {0: 1, 1: 1, 3: 1}
    b = {0: 1, 2: 1}

    def repeated_mul():
        acc = a
        for _ in range(50):
            acc = gf.mul(acc, b)
        return acc

    result = benchmark(repeated_mul)
    assert result is not None


# endregion


# region Clifford Algebra


@pytest.mark.benchmark(group="clifford-geometric-product")
@pytest.mark.parametrize("terms", [2, 8])
def test_benchmark_clifford_geometric_product(benchmark, terms: int):
    a = multivector(terms, seed=1)
    b = multivector(terms, seed=2)

    result = benchmark(ax.clifford.geometric_product, a, b)
    assert result is not None


@pytest.mark.benchmark(group="clifford-rotor")
def test_benchmark_clifford_rotor_rotation(benchmark):
    vector = {(0,): 1.0, (1,): 0.5, (2,): -0.25}

    result = benchmark(ax.clifford.rotor_rotation, vector, (0, 1), math.pi / 3)
    assert result is not None


# endregion


# region Groups & Category Theory


@pytest.mark.benchmark(group="group-permutation")
@pytest.mark.parametrize("operation", ["compose", "invert", "signature"])
def test_benchmark_group_permutation(benchmark, operation: str):
    size = 500
    rand = rng(13)
    domain = list(range(size))
    image = domain[:]
    rand.shuffle(image)
    perm = dict(zip(domain, image, strict=True))
    other = dict(zip(domain, sorted(image, reverse=True), strict=True))

    if operation == "compose":
        result = benchmark(ax.group.compose, perm, other)
    elif operation == "invert":
        result = benchmark(ax.group.invert, perm)
    else:
        result = benchmark(ax.group.signature, perm)

    assert result is not None


@pytest.mark.benchmark(group="category-kleisli")
def test_benchmark_category_kleisli_compose(benchmark):
    f = sparse_matrix(40, 40, 0.25, seed=1)
    g = sparse_matrix(40, 40, 0.25, seed=2)

    result = benchmark(ax.category.kleisli_compose, f, g)
    assert result is not None


# endregion


# region Tries


@pytest.mark.benchmark(group="trie-contract")
def test_benchmark_trie_contract(benchmark):
    trie = ax.trie.AlgebraicTrie()
    for i in range(200):
        trie[(i % 10, i % 7, i)] = i * 1.5

    result = benchmark(trie.contract)
    assert result is not None


@pytest.mark.benchmark(group="trie-lookup")
def test_benchmark_trie_lookup(benchmark):
    trie = ax.trie.AlgebraicTrie()
    keys = [(i % 10, i % 7, i) for i in range(200)]
    for i, key in enumerate(keys):
        trie[key] = i * 1.5

    def lookup_all():
        return sum(trie[key] for key in keys)

    result = benchmark(lookup_all)
    assert result is not None


# endregion
