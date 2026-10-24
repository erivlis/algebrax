"""
Schwartz-Zippel Randomized Polynomial Identity Testing (PIT).

Tests high-degree algebraic identities over unexpanded arithmetic circuits by evaluating
identities on random integer/rational coordinates sampled from large finite subsets,
bounding the false-positive error probability to under 10^-15 (Schwartz 1980, Saxena 2014).
"""

from __future__ import annotations

import random
from typing import Any

import pytest

import algebrax as ax
from algebrax.lie import LieAlgebra, g2, sl_n, so_n

pytestmark = [pytest.mark.verification, pytest.mark.pit]

SAMPLE_SPACE_BOUND = 10_000  # |S| = 2*10^4; x*y*z <= 10^12 << 2^53 (exact integer float precision)
NUM_TRIALS = 4  # (d / |S|)^4 <= (2 / 20000)^4 = 10^-16


def _random_vector(dim: int, sample_space: range) -> dict[int, float]:
    """Sample random integer coordinates for a Lie algebra element."""
    return {i: float(random.choice(sample_space)) for i in range(dim)}


# ---------------------------------------------------------------------------
# PIT 1: Lie Algebra Jacobi Identity in Classical & Exceptional Algebras
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('lie_algebra_factory', 'name'),
    [
        (lambda: so_n(3), 'so(3) - 3D Rotations'),
        (lambda: sl_n(2), 'sl(2) - Special Linear'),
        (lambda: so_n(4), 'so(4) - 4D Orthogonal (dim 6)'),
        (lambda: g2(), 'g2 - Exceptional Lie Algebra (dim 14)'),
    ],
)
def test_pit_lie_algebra_jacobi_identity(lie_algebra_factory: Any, name: str) -> None:
    """Verify that Jacobi identity [x, [y, z]] + [y, [z, x]] + [z, [x, y]] == 0 holds via PIT."""
    g: LieAlgebra = lie_algebra_factory()
    sample_space = range(-SAMPLE_SPACE_BOUND, SAMPLE_SPACE_BOUND)

    for trial in range(NUM_TRIALS):
        # Sample independent random coordinates x, y, z in S^dim(g)
        x = _random_vector(g.dim, sample_space)
        y = _random_vector(g.dim, sample_space)
        z = _random_vector(g.dim, sample_space)

        # Term 1: [x, [y, z]]
        yz = g.bracket(y, z)
        term1 = g.bracket(x, yz)

        # Term 2: [y, [z, x]]
        zx = g.bracket(z, x)
        term2 = g.bracket(y, zx)

        # Term 3: [z, [x, y]]
        xy = g.bracket(x, y)
        term3 = g.bracket(z, xy)

        # Jacobi sum J = term1 + term2 + term3
        jacobi_sum: dict[int, float | complex] = {}
        for term in (term1, term2, term3):
            for k, val in term.items():
                jacobi_sum[k] = jacobi_sum.get(k, 0.0) + val

        # Clean tiny float residues
        cleaned_norm = sum(abs(v) for v in jacobi_sum.values())
        assert cleaned_norm < 1e-7, f'Jacobi identity failed for {name} on trial {trial}: {jacobi_sum}'


# ---------------------------------------------------------------------------
# PIT 2: Lie Bracket Antisymmetry [x, y] == -[y, x]
# ---------------------------------------------------------------------------


def test_pit_lie_bracket_antisymmetry() -> None:
    """Verify Lie bracket antisymmetry [x, y] + [y, x] == 0 via PIT."""
    g = so_n(3)
    sample_space = range(-SAMPLE_SPACE_BOUND, SAMPLE_SPACE_BOUND)

    for _ in range(NUM_TRIALS):
        x = _random_vector(g.dim, sample_space)
        y = _random_vector(g.dim, sample_space)

        xy = g.bracket(x, y)
        yx = g.bracket(y, x)

        antisym_sum: dict[int, float | complex] = {}
        for k, v in xy.items():
            antisym_sum[k] = antisym_sum.get(k, 0.0) + v
        for k, v in yx.items():
            antisym_sum[k] = antisym_sum.get(k, 0.0) + v

        assert all(abs(v) < 1e-10 for v in antisym_sum.values())
