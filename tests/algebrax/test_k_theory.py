r"""
Unit and property tests for Universal Grothendieck Groups/Rings (`algebrax.algebra._grothendieck`)
and Topological K-Theory & Characteristic Classes (`algebrax.topology.k_theory`).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import pytest

from algebrax.algebra import AddCommGroup, AddCommMonoid, CommRing, GrothendieckGroup, GrothendieckRing
from algebrax.semiring import Semiring
from algebrax.topology import (
    DiscreteOrthogonalConnection,
    TopologicalKTheoryRing,
    bundle_direct_sum,
    bundle_tensor_product,
    chern_character,
    compute_chern_character_1,
    compute_chern_character_2,
    compute_face_curvature_angle,
    first_chern_number,
    trivial_bundle,
)
from algebrax.verification import (
    verify_add_comm_group_laws,
    verify_chern_character_additivity,
    verify_chern_number_integrality,
    verify_comm_ring_laws,
    verify_grothendieck_universal_property,
)


def _rot2d(theta: float) -> dict[int, dict[int, float]]:
    c = math.cos(theta)
    s = math.sin(theta)
    return {
        0: {0: c, 1: -s},
        1: {0: s, 1: c},
    }


def _make_conn(
    fiber_dim: int,
    edge_transports: dict[tuple[Any, Any], dict[int, dict[int, float]]],
) -> DiscreteOrthogonalConnection:
    conn = DiscreteOrthogonalConnection(fiber_dim)
    for (u, v), mat in edge_transports.items():
        conn.set_transport(u, v, mat)
    return conn


class _NatMonoid(AddCommMonoid[int]):
    """Additive commutative monoid (N, +, 0)."""

    @property
    def zero(self) -> int:
        return 0

    def add(self, a: int, b: int) -> int:
        return a + b


class _NatSemiring(Semiring[int]):
    """Commutative semiring (N, +, *, 0, 1)."""

    @property
    def zero(self) -> int:
        return 0

    @property
    def one(self) -> int:
        return 1

    def add(self, a: int, b: int) -> int:
        return a + b

    def mul(self, a: int, b: int) -> int:
        return a * b


class _RealAddGroup(AddCommGroup[float]):
    """Additive abelian group (R, +, 0, -)."""

    @property
    def zero(self) -> float:
        return 0.0

    def add(self, a: float, b: float) -> float:
        return a + b

    def neg(self, a: float) -> float:
        return -a


class _NonCancellativeMonoid(AddCommMonoid[int]):
    """Idempotent saturating monoid on {0, 1, 2} where x + y = min(2, x + y).

    Non-cancellative: 1 + 2 = 2 = 2 + 2, even though 1 != 2.
    """

    @property
    def zero(self) -> int:
        return 0

    def add(self, a: int, b: int) -> int:
        return min(2, a + b)


def _canonical_int_pair(pair: tuple[int, int]) -> tuple[int, int]:
    m = min(pair[0], pair[1])
    return (pair[0] - m, pair[1] - m)


# =============================================================================
# 1. Universal Grothendieck Group & Ring Tests
# =============================================================================


def test_grothendieck_group_mro_and_basic_operations() -> None:
    """Verify nominal MRO inheritance and formal difference arithmetic on K_0(N) = Z."""
    nat = _NatMonoid()
    k0 = GrothendieckGroup(nat, normalize_fn=_canonical_int_pair)

    assert isinstance(k0, AddCommGroup)
    assert k0.zero == (0, 0)
    assert k0.embed(5) == (5, 0)

    x = (5, 2)  # +3
    y = (1, 4)  # -3
    assert k0.add(x, y) == (0, 0)
    assert k0.neg(x) == (0, 3)
    assert k0.sub(x, x) == (0, 0)
    assert k0.equiv((5, 2), (10, 7))
    assert not k0.equiv((5, 2), (5, 3))


def test_grothendieck_group_axiomatic_laws() -> None:
    """Verify AddCommGroup laws on normalized K_0(N)."""
    k0 = GrothendieckGroup(_NatMonoid(), normalize_fn=_canonical_int_pair)
    samples = [(0, 0), (3, 0), (0, 2), (5, 0), (0, 7)]
    laws = verify_add_comm_group_laws(k0, samples)
    assert all(laws.values()), f'Failed group laws: {laws}'


def test_grothendieck_ring_mro_and_comm_ring_laws() -> None:
    """Verify nominal CommRing inheritance and ring axioms on K_0(N, +, *)."""
    k0_ring = GrothendieckRing(_NatSemiring(), normalize_fn=_canonical_int_pair)

    assert isinstance(k0_ring, GrothendieckGroup)
    assert isinstance(k0_ring, CommRing)
    assert k0_ring.zero == (0, 0)
    assert k0_ring.one == (1, 0)

    # (3 - 1) * (2 - 5) = 2 * (-3) = -6 -> (0, 6)
    prod = k0_ring.mul((3, 1), (2, 5))
    assert prod == (0, 6)

    samples = [(0, 0), (1, 0), (2, 0), (0, 3), (4, 0)]
    laws = verify_comm_ring_laws(k0_ring, samples)
    assert all(laws.values()), f'Failed CommRing laws: {laws}'


def test_grothendieck_non_cancellative_stabilizer_equivalence() -> None:
    """Verify stabilized equivalence a + d + k = b + c + k for non-cancellative monoids."""
    monoid = _NonCancellativeMonoid()
    k0 = GrothendieckGroup(monoid)

    # In saturating monoid {0, 1, 2}, (1, 0) and (2, 0) have 1 + 0 = 1 != 0 + 2 = 2
    # without stabilizer, but with k = 2: (1 + 0) + 2 = 2 == (0 + 2) + 2 = 2!
    assert not k0.equiv((1, 0), (2, 0))
    assert k0.equiv((1, 0), (2, 0), stabilizers=[0, 1, 2])


def test_grothendieck_universal_property_and_falsification() -> None:
    """Verify universal property lifting f: N -> R and Popperian falsification of non-homomorphic map."""
    k0 = GrothendieckGroup(_NatMonoid())
    target = _RealAddGroup()

    # Valid monoid homomorphism f(n) = 2.5 * n
    res_valid = verify_grothendieck_universal_property(
        k0,
        target,
        monoid_map=lambda n: 2.5 * float(n),
        monoid_samples=[0, 1, 2, 3],
    )
    assert all(res_valid.values()), f'Universal property failed: {res_valid}'

    # Popperian falsification: f(n) = n^2 + 1 is NOT a monoid homomorphism
    res_invalid = verify_grothendieck_universal_property(
        k0,
        target,
        monoid_map=lambda n: float(n * n + 1),
        monoid_samples=[0, 1, 2],
    )
    assert not res_invalid['monoid_homomorphism']


# =============================================================================
# 2. Vector Bundle Semiring Operations (Whitney Sum & Tensor Product)
# =============================================================================


def test_bundle_direct_sum_and_tensor_product() -> None:
    """Verify Whitney direct sum E_1 (+) E_2 and Kronecker tensor product E_1 (x) E_2."""
    theta1 = 0.3
    theta2 = -0.5
    conn1 = _make_conn(2, {(0, 1): _rot2d(theta1)})
    conn2 = _make_conn(2, {(0, 1): _rot2d(theta2)})

    # Whitney direct sum has fiber_dim 2 + 2 = 4
    dsum = bundle_direct_sum(conn1, conn2)
    assert dsum.fiber_dim == 4
    u_sum = dsum.transport(0, 1)
    assert math.isclose(u_sum[0][0], math.cos(theta1))
    assert math.isclose(u_sum[2][2], math.cos(theta2))
    assert u_sum.get(0, {}).get(2, 0.0) == 0.0

    # Tensor product has fiber_dim 2 * 2 = 4
    tprod = bundle_tensor_product(conn1, conn2)
    assert tprod.fiber_dim == 4
    u_prod = tprod.transport(0, 1)
    assert math.isclose(u_prod[0][0], math.cos(theta1) * math.cos(theta2))
    assert math.isclose(u_prod[0][1], -math.cos(theta1) * math.sin(theta2))


def test_trivial_bundle_validation() -> None:
    """Verify trivial_bundle rank validation and flat transport identity."""
    with pytest.raises(ValueError, match='positive'):
        trivial_bundle(0, [(0, 1)])

    flat = trivial_bundle(2, [(0, 1), (1, 2), (0, 2)])
    assert flat.fiber_dim == 2
    assert compute_face_curvature_angle(flat, (0, 1, 2)) == 0.0


# =============================================================================
# 3. Characteristic Chern Classes & Chern Number Quantization
# =============================================================================


def test_chern_character_additivity_under_whitney_sum() -> None:
    """Verify ch_0, ch_1, and ch_2 are additive over E_1 (+) E_2."""
    faces = [(0, 1, 2), (0, 2, 3)]
    conn1 = _make_conn(
        2,
        {
            (0, 1): _rot2d(0.25),
            (1, 2): _rot2d(0.35),
            (0, 2): _rot2d(-0.15),
            (2, 3): _rot2d(0.40),
            (0, 3): _rot2d(0.10),
        },
    )
    conn2 = _make_conn(
        2,
        {
            (0, 1): _rot2d(-0.20),
            (1, 2): _rot2d(0.50),
            (0, 2): _rot2d(0.05),
            (2, 3): _rot2d(-0.30),
            (0, 3): _rot2d(0.25),
        },
    )

    res = verify_chern_character_additivity(conn1, conn2, faces)
    assert all(res.values()), f'Chern character additivity failed: {res}'


def test_chern_number_integer_quantization_on_closed_tetrahedron() -> None:
    """Verify that the first Chern number on the closed boundary of a tetrahedron S^2 is an integer."""
    # Outward-oriented boundary 2-cycle of tetrahedron [0, 1, 2, 3]:
    # d[0, 1, 2, 3] = [1, 2, 3] - [0, 2, 3] + [0, 1, 3] - [0, 1, 2]
    # Reversing orientation of negatively-signed faces gives coherently oriented faces:
    oriented_faces = [(1, 2, 3), (0, 3, 2), (0, 1, 3), (0, 2, 1)]

    # Case 1: Smooth connection with small angles -> net topological charge c_1 = 0
    conn_zero = _make_conn(
        2,
        {
            (0, 1): _rot2d(0.4),
            (0, 2): _rot2d(-0.3),
            (0, 3): _rot2d(0.2),
            (1, 2): _rot2d(0.5),
            (1, 3): _rot2d(-0.4),
            (2, 3): _rot2d(0.3),
        },
    )
    c1_zero = first_chern_number(conn_zero, oriented_faces)
    assert math.isclose(c1_zero, 0.0, abs_tol=1e-9)
    assert verify_chern_number_integrality(conn_zero, oriented_faces)

    # Case 2: Monopole / Dirac string vortex carrying -1 topological quantum (-2*pi flux)
    conn_monopole = _make_conn(
        2,
        {
            (0, 1): _rot2d(0.0),
            (0, 2): _rot2d(0.0),
            (0, 3): _rot2d(0.0),
            (1, 2): _rot2d(2.2),
            (2, 3): _rot2d(2.2),
            (1, 3): _rot2d(-2.2),
        },
    )
    c1_monopole = first_chern_number(conn_monopole, oriented_faces)
    assert math.isclose(c1_monopole, -1.0, abs_tol=1e-9)
    assert verify_chern_number_integrality(conn_monopole, oriented_faces)

    # Popperian falsification: integrating over a single open triangle with non-quantized flux is NOT integer
    assert not verify_chern_number_integrality(conn_monopole, [(0, 1, 2)])


def test_chern_character_2_with_four_simplices_and_tuple() -> None:
    """Verify ch_2 on both 2-faces and 4-simplices via Alexander-Whitney cup product."""
    faces = [(0, 1, 2), (2, 3, 4)]
    four_simplices = [(0, 1, 2, 3, 4)]
    conn = _make_conn(
        2,
        {
            (0, 1): _rot2d(0.5),
            (1, 2): _rot2d(0.5),
            (0, 2): _rot2d(0.0),
            (2, 3): _rot2d(0.5),
            (3, 4): _rot2d(0.5),
            (2, 4): _rot2d(0.0),
        },
    )

    ch0, ch1, ch2_faces = chern_character(conn, faces)
    assert ch0 == 1  # complex rank of SO(2) bundle is 2 // 2 == 1
    assert (0, 1, 2) in ch1
    assert (0, 1, 2) in ch2_faces

    ch2_4d = compute_chern_character_2(conn, faces, four_simplices=four_simplices)
    assert (0, 1, 2, 3, 4) in ch2_4d
    expected = 0.5 * (1.0 / (2.0 * math.pi)) ** 2
    assert math.isclose(ch2_4d[(0, 1, 2, 3, 4)], expected, rel_tol=1e-9)


# =============================================================================
# 4. TopologicalKTheoryRing K^0(X) Tests
# =============================================================================


def test_topological_k_theory_ring_virtual_bundles() -> None:
    """Verify virtual bundle arithmetic, virtual rank, and virtual Chern character in K^0(X)."""
    edges = [(0, 1), (1, 2), (0, 2)]
    faces = [(0, 1, 2)]
    k_ring = TopologicalKTheoryRing(edges=edges)

    assert isinstance(k_ring, CommRing)
    assert k_ring.virtual_rank(k_ring.zero) == 0
    assert k_ring.virtual_rank(k_ring.one) == 1

    e1 = _make_conn(
        2,
        {(0, 1): _rot2d(0.6), (1, 2): _rot2d(0.2), (0, 2): _rot2d(0.0)},
    )
    e2 = trivial_bundle(2, edges)

    # Reduced virtual bundle [E_1] - [epsilon^2] has virtual rank 0 but non-zero ch_1!
    reduced = (e1, e2)
    assert k_ring.virtual_rank(reduced) == 0
    v_ch1 = k_ring.virtual_chern_1(reduced, faces)
    assert math.isclose(v_ch1[(0, 1, 2)], 0.8 / (2.0 * math.pi), rel_tol=1e-9)

    # In K^0(X), x - x has virtual rank 0 and vanishing virtual Chern character
    diff = k_ring.sub(reduced, reduced)
    assert k_ring.virtual_rank(diff) == 0
    diff_ch1 = k_ring.virtual_chern_1(diff, faces)
    assert math.isclose(diff_ch1[(0, 1, 2)], 0.0, abs_tol=1e-12)

    # Ring multiplication distributes over virtual bundles
    prod = k_ring.mul(k_ring.embed(e1), k_ring.one)
    assert k_ring.virtual_rank(prod) == 2
