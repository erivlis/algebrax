"""
Proof-carrying solver (PCS) verification certificates.

Verifies independent, self-certifying algebraic witnesses (e.g., Helmholtz-Hodge
orthogonal flow decomposition certificates) in linear O(|E|) time without repeating
iterative numerical solver computations.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pytest

import algebrax as ax
from algebrax.homology import Cochain, SimplicialComplex, helmholtz_hodge_decomposition
from algebrax.verification import semiring_elements_equal

pytestmark = [pytest.mark.verification, pytest.mark.certificates]


def _inner_product(
    f1: Mapping[tuple[int, ...], float],
    f2: Mapping[tuple[int, ...], float],
) -> float:
    """Compute Euclidean L^2 inner product between two sparse cochains."""
    acc = 0.0
    for simplex, val in f1.items():
        if simplex in f2:
            acc += val * f2[simplex]
    return acc


def test_helmholtz_hodge_decomposition_certificate() -> None:
    """Verify in O(|E|) time that Helmholtz-Hodge decomposition satisfies the 3 orthogonal certificate conditions."""
    # Build a triangulated annulus (ring of triangles with an open hole)
    # Outer cycle: 0-1-2-3-0; Inner hole: 4-5-6-4
    # Simple complex with 1 hole: triangles (0, 1, 4), (1, 2, 4), (2, 3, 4)
    triangles = [
        (0, 1, 2),
        (2, 3, 4),
        (4, 5, 0),
        (0, 2, 4),
    ]
    sc = SimplicialComplex(triangles)

    # An arbitrary edge flow w on 1-simplices
    raw_flow = {
        (0, 1): 2.5,
        (1, 2): 1.5,
        (2, 3): -3.0,
        (3, 4): 2.0,
        (4, 5): 1.0,
        (5, 0): -0.5,
        (0, 2): 1.0,
        (2, 4): -1.2,
    }
    flow = Cochain(raw_flow, degree=1)

    # Run solver once to obtain the certificate (HodgeDecomposition witness)
    decomp = helmholtz_hodge_decomposition(sc, flow, tol=1e-9)

    exact = decomp.exact
    coexact = decomp.coexact
    harmonic = decomp.harmonic

    # -----------------------------------------------------------------------
    # Certificate Condition 1: Recomposition Identity (w = w_exact + w_coexact + w_harmonic)
    # -----------------------------------------------------------------------
    recomposed: dict[tuple[int, ...], float] = {}
    for comp in (exact, coexact, harmonic):
        for e, v in comp.items():
            recomposed[e] = recomposed.get(e, 0.0) + v

    # Clean near-zero residues
    recomposed_clean = {e: v for e, v in recomposed.items() if abs(v) > 1e-9}
    flow_clean = {e: v for e, v in flow.items() if abs(v) > 1e-9}

    assert semiring_elements_equal(recomposed_clean, flow_clean, tol=1e-6), (
        f'Recomposition certificate failed: {recomposed_clean} != {flow_clean}'
    )

    # -----------------------------------------------------------------------
    # Certificate Condition 2: L^2 Orthogonality Witnesses
    # <w_exact, w_coexact> == 0
    # <w_exact, w_harmonic> == 0
    # <w_coexact, w_harmonic> == 0
    # -----------------------------------------------------------------------
    dot_exact_coexact = _inner_product(exact, coexact)
    dot_exact_harmonic = _inner_product(exact, harmonic)
    dot_coexact_harmonic = _inner_product(coexact, harmonic)

    assert abs(dot_exact_coexact) < 1e-6, f'Exact and Coexact are not orthogonal: {dot_exact_coexact}'
    assert abs(dot_exact_harmonic) < 1e-6, f'Exact and Harmonic are not orthogonal: {dot_exact_harmonic}'
    assert abs(dot_coexact_harmonic) < 1e-6, f'Coexact and Harmonic are not orthogonal: {dot_coexact_harmonic}'

    # -----------------------------------------------------------------------
    # Certificate Condition 3: Curl-free and Divergence-free Invariants
    # d_1(w_exact) == 0 (exact is curl-free)
    # partial_1(w_coexact) == 0 (coexact is divergence-free)
    # -----------------------------------------------------------------------
    b1 = sc.boundary_matrices.get(1, {})
    b2 = sc.boundary_matrices.get(2, {})

    if b2:
        # Coboundary d_1 = b2^T
        d1 = ax.matrix.transpose(b2)
        curl_exact = ax.matrix.mat_vec(d1, exact)
        for tri, val in curl_exact.items():
            assert abs(val) < 1e-6, f'Exact component is not curl-free on triangle {tri}: {val}'

    if b1:
        div_coexact = ax.matrix.mat_vec(b1, coexact)
        for vertex, val in div_coexact.items():
            assert abs(val) < 1e-6, f'Coexact component is not divergence-free on vertex {vertex}: {val}'
