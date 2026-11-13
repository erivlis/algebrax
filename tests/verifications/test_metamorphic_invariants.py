"""
Metamorphic invariant testing for algebraic, topological, and spectral operations.

Verifies mathematical necessary conditions (metamorphic relations) across transformations
without requiring external golden oracles.
"""

from __future__ import annotations

import math
from typing import Any

import pytest

import algebrax as ax
from algebrax.semiring import (
    ArcticSemiring,
    BooleanSemiring,
    StandardSemiring,
    TropicalSemiring,
)
from algebrax.topology import Cochain, SimplicialComplex, SparseChainComplex
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.metamorphic]


# ---------------------------------------------------------------------------
# Metamorphic Relation 1: Matrix Transpose Duality (A @ B)^T == B^T @ A^T
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'semiring',
    [
        StandardSemiring(),
        TropicalSemiring(),
        ArcticSemiring(),
        BooleanSemiring(),
    ],
)
def test_metamorphic_matrix_transpose_duality(semiring: Any) -> None:
    """Verify that (A @ B)^T == B^T @ A^T holds for all commutative semirings."""
    if isinstance(semiring, BooleanSemiring):
        mat_a = {
            0: {0: True, 1: True},
            1: {1: True, 2: False},
            2: {0: False, 2: True},
        }
        mat_b = {
            0: {1: True, 2: False},
            1: {0: False, 2: True},
            2: {1: True},
        }
    else:
        mat_a = {
            0: {0: 2.0, 1: 5.0},
            1: {1: 3.0, 2: 7.0},
            2: {0: 1.0, 2: 4.0},
        }
        mat_b = {
            0: {1: 4.0, 2: 2.0},
            1: {0: 1.0, 2: 6.0},
            2: {1: 3.0},
        }

    # Left hand side: (A @ B)^T
    prod_ab = ax.matrix.dot(mat_a, mat_b, semiring=semiring)
    lhs = ax.matrix.transpose(prod_ab)

    # Right hand side: B^T @ A^T
    a_t = ax.matrix.transpose(mat_a)
    b_t = ax.matrix.transpose(mat_b)
    rhs = ax.matrix.dot(b_t, a_t, semiring=semiring)

    assert semiring_elements_equal(lhs, rhs, tol=1e-10)


# ---------------------------------------------------------------------------
# Metamorphic Relation 2: Scalar Homogeneity in Semiring Matrix Multiplication
# ---------------------------------------------------------------------------


def test_metamorphic_scalar_homogeneity() -> None:
    """Verify scalar distributivity: c * (A @ B) == (c * A) @ B for numeric rings."""
    mat_a = {0: {0: 1.5, 1: 2.0}, 1: {0: 3.0, 1: 0.5}}
    mat_b = {0: {0: 4.0, 1: 1.0}, 1: {0: 2.0, 1: 5.0}}
    c = 3.0

    # LHS: c * (A @ B)
    ab = ax.matrix.dot(mat_a, mat_b)
    lhs = {r: {col: c * val for col, val in row.items()} for r, row in ab.items()}

    # RHS: (c * A) @ B
    ca = {r: {col: c * val for col, val in row.items()} for r, row in mat_a.items()}
    rhs = ax.matrix.dot(ca, mat_b)

    assert semiring_elements_equal(lhs, rhs, tol=1e-10)


# ---------------------------------------------------------------------------
# Metamorphic Relation 3: Simplicial Chain Nilpotency (d^2 == 0)
# ---------------------------------------------------------------------------


def test_metamorphic_simplicial_boundary_nilpotency() -> None:
    """Verify the fundamental topological invariant: d_{k-1} o d_k == 0."""
    # Tetrahedron with vertices 0, 1, 2, 3
    tetrahedron_faces = [
        (0, 1, 2),
        (0, 1, 3),
        (0, 2, 3),
        (1, 2, 3),
    ]
    sc = SimplicialComplex(tetrahedron_faces)

    d1 = sc.boundary_matrices[1]
    d2 = sc.boundary_matrices[2]

    # Wrap in SparseChainComplex and verify nilpotency
    scc = SparseChainComplex({1: d1, 2: d2})
    assert scc.verify_nilpotency(2) is True

    # Alternatively, direct matrix dot product: d1 @ d2 == 0
    d1_d2 = ax.matrix.dot(d1, d2)
    # Result must be completely empty or contain only exact zeroes
    for row in d1_d2.values():
        for val in row.values():
            assert abs(val) < 1e-12


# ---------------------------------------------------------------------------
# Metamorphic Relation 4: Cochain Orientation Antisymmetry
# ---------------------------------------------------------------------------


def test_metamorphic_cochain_orientation_antisymmetry() -> None:
    """Verify alternating antisymmetry w(pi(sigma)) = sgn(pi) * w(sigma) and degenerate annihilation."""
    data = {(0, 1): 4.5, (1, 2): 2.0, (0, 2): -1.5}
    omega = Cochain(data, degree=1)

    # Transposition must negate value
    assert omega[(0, 1)] == 4.5
    assert omega[(1, 0)] == -4.5

    # Degenerate simplex with repeated vertex must annihilate to 0.0 via get() and raise KeyError on item access
    assert omega.get((0, 0)) == 0.0
    assert omega.get((2, 2)) == 0.0
    with pytest.raises(KeyError):
        _ = omega[(0, 0)]


# ---------------------------------------------------------------------------
# Metamorphic Relation 5: DFT Circular Shift Magnitude Invariance
# ---------------------------------------------------------------------------


def test_metamorphic_dft_circular_shift_invariance() -> None:
    """Verify that circular time shift preserves the DFT magnitude spectrum: |F(shift(x))| == |F(x)|."""
    x = {0: 1.0, 1: 2.0, 2: 3.0, 3: 5.0, 4: 0.0, 5: -1.0}
    n = len(x)
    shift_amount = 2

    # Shifted signal: x_shifted[i] = x[(i - shift) % n]
    x_shifted = {(i + shift_amount) % n: val for i, val in x.items()}

    # Compute DFTs
    dft_orig = ax.transforms.dft(x, n=n)
    dft_shifted = ax.transforms.dft(x_shifted, n=n)

    # Assert magnitude spectrum is identical for all frequencies k
    for k in range(n):
        mag_orig = abs(dft_orig[k])
        mag_shifted = abs(dft_shifted[k])
        assert math.isclose(mag_orig, mag_shifted, rel_tol=1e-10, abs_tol=1e-10)


# ---------------------------------------------------------------------------
# Metamorphic Relation 6: Graph Laplacian Permutation Conjugacy
# ---------------------------------------------------------------------------


def test_metamorphic_graph_laplacian_permutation_conjugacy() -> None:
    """Verify that relabeling graph vertices conjugates the Laplacian: L(P A P^T) == P L(A) P^T."""
    # Triangle graph with an attached node: 0-1, 1-2, 2-0, 2-3
    adj = {
        0: {1: 1.0, 2: 1.0},
        1: {0: 1.0, 2: 1.0},
        2: {0: 1.0, 1: 1.0, 3: 1.0},
        3: {2: 1.0},
    }

    # Graph Laplacian L = D - A
    lap_orig = ax.matrix.laplacian_matrix(adj)

    # Permutation map: swap 0 and 3
    perm = {0: 3, 1: 1, 2: 2, 3: 0}

    # Permute adjacency: A_perm[p(u)][p(v)] = A[u][v]
    adj_perm: dict[int, dict[int, float]] = {}
    for u, neighbors in adj.items():
        pu = perm[u]
        adj_perm[pu] = {}
        for v, w in neighbors.items():
            pv = perm[v]
            adj_perm[pu][pv] = w

    # Compute Laplacian of permuted graph
    lap_perm = ax.matrix.laplacian_matrix(adj_perm)

    # Permute lap_orig directly
    expected_lap_perm: dict[int, dict[int, float]] = {}
    for u, neighbors in lap_orig.items():
        pu = perm[u]
        expected_lap_perm[pu] = {}
        for v, val in neighbors.items():
            pv = perm[v]
            expected_lap_perm[pu][pv] = val

    assert semiring_elements_equal(lap_perm, expected_lap_perm, tol=1e-10)


# ---------------------------------------------------------------------------
# Metamorphic Relation 7: Denjoy-Conway Sum-Star Identity (A + B)* == (A* B)* A*
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'semiring',
    [
        BooleanSemiring(),
        TropicalSemiring(),
    ],
)
def test_metamorphic_sum_star_conway_identity(semiring: Any) -> None:
    r"""Verify the fundamental Denjoy-Conway sum-star identity: (A + B)* == (A* · B)* · A*."""
    if isinstance(semiring, BooleanSemiring):
        a = {0: {1: True}, 1: {2: False}}
        b = {1: {2: True}, 2: {0: True}}
    else:
        a = {0: {1: 2.0}, 1: {2: 10.0}}
        b = {1: {2: 3.0}, 2: {0: 4.0}}

    # LHS: (A + B)*
    a_plus_b = ax.matrix.add(a, b, semiring=semiring)
    lhs = ax.matrix.star(a_plus_b, semiring=semiring)

    # RHS: (A* · B)* · A*
    a_star = ax.matrix.star(a, semiring=semiring)
    astar_b = ax.matrix.dot(a_star, b, semiring=semiring)
    astar_b_star = ax.matrix.star(astar_b, semiring=semiring)
    rhs = ax.matrix.dot(astar_b_star, a_star, semiring=semiring)

    assert semiring_elements_equal(lhs, rhs, tol=1e-9)


# ---------------------------------------------------------------------------
# Metamorphic Relation 8: Product-Star Sliding Identity (A · B)* · A == A · (B · A)*
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'semiring',
    [
        BooleanSemiring(),
        TropicalSemiring(),
    ],
)
def test_metamorphic_product_star_sliding_identity(semiring: Any) -> None:
    r"""Verify the Conway product-star sliding identity: (A · B)* · A == A · (B · A)*."""
    if isinstance(semiring, BooleanSemiring):
        a = {0: {1: True}, 1: {0: True}}
        b = {0: {0: False, 1: True}, 1: {1: True}}
    else:
        a = {0: {1: 1.0}, 1: {0: 3.0}}
        b = {0: {1: 2.0}, 1: {1: 4.0}}

    ab = ax.matrix.dot(a, b, semiring=semiring)
    ba = ax.matrix.dot(b, a, semiring=semiring)

    # LHS: (A · B)* · A
    ab_star = ax.matrix.star(ab, semiring=semiring)
    lhs = ax.matrix.dot(ab_star, a, semiring=semiring)

    # RHS: A · (B · A)*
    ba_star = ax.matrix.star(ba, semiring=semiring)
    rhs = ax.matrix.dot(a, ba_star, semiring=semiring)

    assert semiring_elements_equal(lhs, rhs, tol=1e-9)


# ---------------------------------------------------------------------------
# Metamorphic Relation 9: Permutation Equivariance of Star and Plus Closures
# ---------------------------------------------------------------------------


def test_metamorphic_matrix_closure_permutation_equivariance() -> None:
    r"""Verify that graph node permutation commutes with star and plus closures:
    star(P · A · P^T) == P · star(A) · P^T and plus(P · A · P^T) == P · plus(A) · P^T.
    """
    b = BooleanSemiring()
    adj = {
        0: {1: True},
        1: {2: True},
        2: {0: False},
    }
    perm = {0: 2, 1: 0, 2: 1}

    # Permute input graph
    adj_perm: dict[int, dict[int, bool]] = {}
    for u, neighbors in adj.items():
        pu = perm[u]
        adj_perm[pu] = {}
        for v, val in neighbors.items():
            pv = perm[v]
            adj_perm[pu][pv] = val

    # 1. Star closure equivariance
    star_orig = ax.matrix.star(adj, b)
    star_perm = ax.matrix.star(adj_perm, b)
    expected_star_perm: dict[int, dict[int, bool]] = {}
    for u, row in star_orig.items():
        pu = perm[u]
        expected_star_perm[pu] = {}
        for v, val in row.items():
            pv = perm[v]
            expected_star_perm[pu][pv] = val

    assert semiring_elements_equal(star_perm, expected_star_perm, tol=1e-9)

    # 2. Plus closure equivariance
    plus_orig = ax.matrix.plus(adj, b)
    plus_perm = ax.matrix.plus(adj_perm, b)
    expected_plus_perm: dict[int, dict[int, bool]] = {}
    for u, row in plus_orig.items():
        pu = perm[u]
        expected_plus_perm[pu] = {}
        for v, val in row.items():
            pv = perm[v]
            expected_plus_perm[pu][pv] = val

    assert semiring_elements_equal(plus_perm, expected_plus_perm, tol=1e-9)

