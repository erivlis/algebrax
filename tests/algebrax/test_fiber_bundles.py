"""Tests for EP-0203: Discrete Fiber Bundles, Gauge Connections, Holonomy, and Connection Laplacians."""

from __future__ import annotations

import math

import pytest

from algebrax.topology import (
    CellularSheaf,
    DiscreteConnection,
    DiscreteOrthogonalConnection,
    FunctorialSheaf,
    apply_gauge_transformation,
    build_connection_laplacian,
    compute_face_holonomy,
    covariant_exterior_derivative,
    is_flat_bundle,
)
from algebrax.verification import (
     semiring_elements_equal,
    verify_connection_inversion,
    verify_gauge_covariance,
)


def _rot2d(theta: float) -> dict[int, dict[int, float]]:
    c = math.cos(theta)
    s = math.sin(theta)
    return {
        0: {0: c, 1: -s},
        1: {0: s, 1: c},
    }


def test_discrete_orthogonal_connection_basics_and_holonomy() -> None:
    with pytest.raises(ValueError, match='Fiber dimension must be positive'):
        DiscreteOrthogonalConnection(0)

    conn = DiscreteOrthogonalConnection(fiber_dim=2)
    assert isinstance(conn, DiscreteConnection)
    assert conn.fiber_dim == 2

    # Flat SO(2) bundle on triangle (0, 1, 2): angles pi/4 + pi/4 = pi/2
    conn.set_transport(0, 1, _rot2d(math.pi / 4))
    conn.set_transport(1, 2, _rot2d(math.pi / 4))
    conn.set_transport(0, 2, _rot2d(math.pi / 2))

    assert conn.vertices == {0, 1, 2}
    assert (0, 1) in conn.edges
    assert (1, 0) in conn.edges
    assert conn.transport(0, 0) == {0: {0: 1.0}, 1: {1: 1.0}}
    assert conn.transport_path([0]) == {0: {0: 1.0}, 1: {1: 1.0}}
    assert compute_face_holonomy(conn, []) == {0: {0: 1.0}, 1: {1: 1.0}}

    with pytest.raises(KeyError, match='No connection defined'):
        conn.transport(0, 99)

    assert verify_connection_inversion(conn, [(0, 1), (1, 2), (0, 2)])
    assert is_flat_bundle(conn, [(0, 1, 2)])

    # Non-flat (curved) bundle: holonomy around (0, 1, 2) is rotation by pi
    curved = DiscreteOrthogonalConnection(fiber_dim=2)
    curved.set_transport(0, 1, _rot2d(0.0))
    curved.set_transport(1, 2, _rot2d(0.0))
    curved.set_transport(0, 2, _rot2d(math.pi))
    assert not is_flat_bundle(curved, [(0, 1, 2)])


def test_connection_laplacian_sheaf_equivalence_and_gauge_covariance() -> None:
    conn = DiscreteOrthogonalConnection(fiber_dim=2)
    conn.set_transport(0, 1, _rot2d(math.pi / 3))
    conn.set_transport(1, 2, _rot2d(math.pi / 6))
    conn.set_transport(0, 2, _rot2d(math.pi / 2))

    adjacency = {0: {1, 2}, 1: {0, 2}, 2: {0, 1}}
    l_conn = build_connection_laplacian(conn, adjacency)

    # 1. Compare with CellularSheaf Laplacian via to_sheaf()
    sheaf = conn.to_sheaf()
    assert isinstance(sheaf, CellularSheaf)
    assert isinstance(sheaf, FunctorialSheaf)
    l_sheaf = sheaf.laplacian_matrix()
    assert semiring_elements_equal(l_conn, l_sheaf, tol=1e-9)

    # 2. Verify covariant exterior derivative matches sheaf coboundary on 0-cochain
    section = {
        (0, 0): 1.0,
        (0, 1): 0.0,
        (1, 0): math.cos(math.pi / 3),
        (1, 1): math.sin(math.pi / 3),
        (2, 0): math.cos(math.pi / 2),
        (2, 1): math.sin(math.pi / 2),
    }
    # Parallel section on flat bundle -> covariant derivative vanishes!
    d_sec = covariant_exterior_derivative(conn, section, [(0, 1), (1, 2), (0, 2)])
    assert d_sec == {}

    # Perturb vertex 1 -> non-zero covariant exterior derivative
    perturbed = dict(section)
    perturbed[(1, 0)] += 1.0
    d_pert = covariant_exterior_derivative(conn, perturbed, [(0, 1)])
    assert abs(d_pert[((0, 1), 0)] - 1.0) < 1e-12

    # 3. Verify local gauge covariance L_{nabla'} == G L_nabla G^T
    gauge = {
        0: _rot2d(0.4),
        1: _rot2d(-0.7),
        2: _rot2d(1.2),
    }
    assert verify_gauge_covariance(conn, adjacency, gauge)


def test_connection_verification_negative_cases() -> None:
    class NonOrthogonalConnection:
        @property
        def fiber_dim(self) -> int:
            return 1

        def transport(self, u: int, v: int) -> dict[int, dict[int, float]]:
            return {0: {0: 2.0}}  # 2 * 2 = 4 != 1

        def transport_path(self, path: list[int]) -> dict[int, dict[int, float]]:
            return {0: {0: 2.0}}

    bad_conn = NonOrthogonalConnection()
    assert not verify_connection_inversion(bad_conn, [(0, 1)])

    conn = DiscreteOrthogonalConnection(fiber_dim=1)
    with pytest.raises(ValueError, match='Self-loop'):
        conn.set_transport(0, 0, {0: {0: 1.0}})
    assert build_connection_laplacian(conn, {0: set()}) == {}

