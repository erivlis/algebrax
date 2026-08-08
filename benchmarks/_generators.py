"""Deterministic data generators shared by the benchmark suite.

Every generator draws from a freshly seeded ``random.Random`` instance so that the
inputs of a given benchmark are byte-for-byte identical between runs. Stable inputs
are a prerequisite for CodSpeed: without them, a measurement difference between two
commits cannot be attributed to a code change.
"""

import random
from typing import Any

import algebrax as ax

SEED = 20_240_101


def rng(seed: int = SEED) -> random.Random:
    """Return an isolated, seeded pseudo random number generator."""
    return random.Random(seed)


def sparse_matrix(rows: int, cols: int, density: float, seed: int = SEED) -> ax.SparseMatrix[int, float]:
    """Build a sparse matrix with roughly ``density`` non-zero entries per row."""
    rand = rng(seed)
    mat: ax.SparseMatrix[int, float] = {}
    for r in range(rows):
        row: dict[int, float] = {c: rand.uniform(1.0, 10.0) for c in range(cols) if rand.random() < density}
        if row:
            mat[r] = row
    return mat


def sparse_signal(n: int, density: float, seed: int = SEED) -> dict[int, float]:
    """Build a sparse 1-D signal of length ``n``."""
    rand = rng(seed)
    return {i: rand.uniform(1.0, 5.0) for i in range(n) if rand.random() < density}


def nested_dict(depth: int, width: int) -> Any:
    """Build a perfectly balanced nested mapping."""
    if depth == 0:
        return 1
    return {i: nested_dict(depth - 1, width) for i in range(width)}


def unbalanced_dict(depth: int, max_width: int, seed: int = SEED) -> Any:
    """Build a nested mapping with random branching factors and early leaves."""
    rand = rng(seed)

    def build(remaining: int) -> Any:
        if remaining == 0 or rand.random() < 0.1:
            return 1
        return {i: build(remaining - 1) for i in range(rand.randint(1, max_width))}

    return build(depth)


def dense_matrix(rows: int, cols: int, seed: int = SEED) -> list[list[float]]:
    """Build a dense matrix as a list of lists."""
    rand = rng(seed)
    return [[rand.uniform(1.0, 10.0) for _ in range(cols)] for _ in range(rows)]


def graph(n: int, density: float, seed: int = SEED, weighted: bool = True) -> ax.SparseMatrix[int, float]:
    """Build a symmetric (undirected) weighted adjacency matrix without self loops."""
    rand = rng(seed)
    adjacency: dict[int, dict[int, float]] = {i: {} for i in range(n)}
    for u in range(n):
        for v in range(u + 1, n):
            if rand.random() < density:
                weight = rand.uniform(0.5, 4.0) if weighted else 1.0
                adjacency[u][v] = weight
                adjacency[v][u] = weight
    return {u: row for u, row in adjacency.items() if row}


def stochastic_matrix(n: int, density: float, seed: int = SEED) -> ax.SparseMatrix[int, float]:
    """Build a row-stochastic transition matrix suitable for Markov chain benchmarks."""
    rand = rng(seed)
    matrix: dict[int, dict[int, float]] = {}
    for u in range(n):
        targets = [v for v in range(n) if rand.random() < density] or [(u + 1) % n]
        weights = [rand.uniform(0.1, 1.0) for _ in targets]
        total = sum(weights)
        matrix[u] = {v: w / total for v, w in zip(targets, weights, strict=True)}
    return matrix


def distribution(n: int, seed: int = SEED) -> dict[int, float]:
    """Build a normalized probability distribution over ``n`` outcomes."""
    rand = rng(seed)
    weights = {i: rand.uniform(0.1, 1.0) for i in range(n)}
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


def symmetric_positive_definite(n: int, seed: int = SEED) -> ax.SparseMatrix[int, float]:
    """Build a dense-in-shape symmetric positive definite matrix (A @ A.T + n * I)."""
    rand = rng(seed)
    base = [[rand.uniform(-1.0, 1.0) for _ in range(n)] for _ in range(n)]
    matrix: dict[int, dict[int, float]] = {}
    for i in range(n):
        row: dict[int, float] = {}
        for j in range(n):
            value = sum(base[i][k] * base[j][k] for k in range(n))
            if i == j:
                value += n
            row[j] = value
        matrix[i] = row
    return matrix


def multivector(terms: int, seed: int = SEED) -> dict[tuple[int, ...], float]:
    """Build a Clifford multivector over the blades of Cl(3, 0, 0)."""
    rand = rng(seed)
    blades = [(), (0,), (1,), (2,), (0, 1), (0, 2), (1, 2), (0, 1, 2)]
    return {blade: rand.uniform(0.5, 2.0) for blade in blades[:terms]}
