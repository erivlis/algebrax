"""
Unit & Falsification Tests for Langlands Root Duality, Hecke Algebras, Ramanujan Bounds & p-Adic Valuations.
"""

from __future__ import annotations

import math

import pytest

from algebrax.algebra import Algebra, Field, HasNorm, PAdicField
from algebrax.analysis import adjacency_spectrum, hecke_graph_operator, is_ramanujan_graph
from algebrax.lie import (
    IwahoriHeckeAlgebra,
    RootSystem,
    coroot_in_dual,
    langlands_dual_root_system,
    root_inner_product,
)
from algebrax.matrix.core import dot
from algebrax.semiring import TropicalSemiring
from algebrax.verification import (
    verify_cartan_duality,
    verify_field_laws,
    verify_padic_ultrametric,
    verify_padic_ultrametric_inequality,
    verify_ramanujan_spectral_gap,
)


def test_langlands_dual_bn_cn_and_self_dual_types() -> None:
    """Verify B_n <-> C_n Langlands duality and self-duality of A_n, D_n, G2, F4, E6, E7, E8."""
    for rank in (2, 3, 4):
        b_n = RootSystem.from_dynkin('B', rank)
        c_n = RootSystem.from_dynkin('C', rank)

        b_dual = langlands_dual_root_system(b_n)
        assert b_dual.dynkin_type == f'C{rank}'
        assert b_dual.cartan_matrix == c_n.cartan_matrix
        assert b_dual.positive_roots == c_n.positive_roots
        assert b_n.langlands_dual() == b_dual

        c_dual = langlands_dual_root_system(c_n)
        assert c_dual.dynkin_type == f'B{rank}'
        assert c_dual.cartan_matrix == b_n.cartan_matrix
        assert c_dual.positive_roots == b_n.positive_roots

        assert all(verify_cartan_duality(b_n).values())
        assert all(verify_cartan_duality(c_n).values())

    # Simply-laced root systems are strictly self-dual (A^T == A)
    for fam, rk in [('A', 1), ('A', 3), ('D', 4), ('E6', None), ('E7', None), ('E8', None)]:
        rs = RootSystem.from_dynkin(fam, rk)
        dual = langlands_dual_root_system(rs)
        assert dual.cartan_matrix == rs.cartan_matrix
        assert all(verify_cartan_duality(rs).values())

    # Non-simply-laced self-dual up to isomorphism (G2, F4) satisfy involution and coroot bijection
    for exc in ('G2', 'F4'):
        rs = RootSystem.from_dynkin(exc)
        res = verify_cartan_duality(rs)
        assert all(res.values()), f'Failed Cartan duality for {exc}: {res}'


def test_coroot_in_dual_swaps_long_and_short_roots() -> None:
    """Verify that coroot_in_dual swaps long and short roots between B_2 and C_2."""
    b2 = RootSystem.from_dynkin('B', 2)
    c2 = RootSystem.from_dynkin('C', 2)

    # In B_2: alpha_0 = (1, 0) has norm_sq = 4 (long), alpha_1 = (0, 1) has norm_sq = 2 (short)
    assert root_inner_product(b2, (1, 0), (1, 0)) == 4
    assert root_inner_product(b2, (0, 1), (0, 1)) == 2

    # Short root (1, 1) in B_2 maps to long root (2, 1) in C_2
    assert coroot_in_dual(b2, (1, 1)) == (2, 1)
    assert root_inner_product(c2, (2, 1), (2, 1)) == 4

    # Long root (1, 2) in B_2 maps to short root (1, 1) in C_2
    assert coroot_in_dual(b2, (1, 2)) == (1, 1)
    assert root_inner_product(c2, (1, 1), (1, 1)) == 2

    with pytest.raises(ValueError, match='positive squared norm'):
        coroot_in_dual(b2, (0, 0))


def test_iwahori_hecke_algebra_quadratic_and_braid_relations() -> None:
    """Verify Iwahori-Hecke quadratic relations (T_i - q)(T_i + 1) = 0 and Coxeter braid laws."""
    a2 = RootSystem.from_dynkin('A', 2)
    hecke_a2 = IwahoriHeckeAlgebra(a2, q=2.5)
    assert Algebra in IwahoriHeckeAlgebra.__mro__
    assert isinstance(hecke_a2, Algebra)

    t0 = hecke_a2.generator(0)
    t1 = hecke_a2.generator(1)
    one = hecke_a2.one

    # Quadratic relation: T_i^2 = (q - 1) T_i + q * 1
    for ti in (t0, t1):
        ti_sq = hecke_a2.mul(ti, ti)
        expected = hecke_a2.add(hecke_a2.scale(hecke_a2.q - 1.0, ti), hecke_a2.scale(hecke_a2.q, one))
        assert hecke_a2.is_zero(hecke_a2.sub(ti_sq, expected))

    # A_2 braid relation (m_{01} = 3): T_0 T_1 T_0 == T_1 T_0 T_1
    lhs_a2 = hecke_a2.mul(hecke_a2.mul(t0, t1), t0)
    rhs_a2 = hecke_a2.mul(hecke_a2.mul(t1, t0), t1)
    assert hecke_a2.is_zero(hecke_a2.sub(lhs_a2, rhs_a2))
    # Longest element w_0 of A_2 has Coxeter length 3
    w0_key = next(iter(lhs_a2.keys()))
    assert hecke_a2.coxeter_length(w0_key) == 3

    # B_2 braid relation (m_{01} = 4): T_0 T_1 T_0 T_1 == T_1 T_0 T_1 T_0
    b2 = RootSystem.from_dynkin('B', 2)
    hecke_b2 = IwahoriHeckeAlgebra(b2, q=3.0)
    u0 = hecke_b2.generator(0)
    u1 = hecke_b2.generator(1)
    lhs_b2 = hecke_b2.mul(hecke_b2.mul(hecke_b2.mul(u0, u1), u0), u1)
    rhs_b2 = hecke_b2.mul(hecke_b2.mul(hecke_b2.mul(u1, u0), u1), u0)
    assert hecke_b2.is_zero(hecke_b2.sub(lhs_b2, rhs_b2))

    # At q = 1, T_i^2 = 1 (classical Weyl group algebra R[W])
    weyl_alg = IwahoriHeckeAlgebra(a2, q=1.0)
    s0 = weyl_alg.generator(0)
    assert weyl_alg.mul(s0, s0) == weyl_alg.one

    with pytest.raises(IndexError, match='out of bounds'):
        hecke_a2.generator(5)


def test_ramanujan_expander_and_hecke_operators() -> None:
    """Verify Ramanujan spectral bound on Petersen/complete graphs vs non-Ramanujan cycle C_6."""
    # Complete graph K_4 is 3-regular with eigenvalues {3, -1, -1, -1}
    # max non-trivial |lambda| = 1 <= 2*sqrt(2) ≈ 2.828 -> Ramanujan!
    k4: dict[int, dict[int, float]] = {
        i: {j: 1.0 for j in range(4) if j != i}
        for i in range(4)
    }
    is_ram_k4, max_nt_k4, thresh_k4 = is_ramanujan_graph(k4)
    assert is_ram_k4 is True
    assert math.isclose(max_nt_k4, 1.0, abs_tol=1e-6)
    assert math.isclose(thresh_k4, 2.0 * math.sqrt(2.0), abs_tol=1e-6)
    assert all(verify_ramanujan_spectral_gap(k4).values())

    # Petersen graph (3-regular, 10 vertices): spectrum {3^1, 1^5, (-2)^4}
    # max non-trivial |lambda| = 2.0 <= 2*sqrt(2) ≈ 2.8284 -> Ramanujan!
    petersen_edges = [
        (0, 1), (1, 2), (2, 3), (3, 4), (4, 0),
        (5, 7), (7, 9), (9, 6), (6, 8), (8, 5),
        (0, 5), (1, 6), (2, 7), (3, 8), (4, 9),
    ]
    petersen: dict[int, dict[int, float]] = {i: {} for i in range(10)}
    for u, v in petersen_edges:
        petersen[u][v] = 1.0
        petersen[v][u] = 1.0
    is_ram_pet, max_nt_pet, _ = is_ramanujan_graph(petersen, degree=3)
    assert is_ram_pet is True
    assert math.isclose(max_nt_pet, 2.0, abs_tol=1e-5)
    assert all(verify_ramanujan_spectral_gap(petersen, degree=3).values())

    # Verify Hecke walk operators T_0, T_1, T_2, T_3 commute pairwise on Petersen graph
    t0 = hecke_graph_operator(petersen, 0)
    t1 = hecke_graph_operator(petersen, 1)
    t2 = hecke_graph_operator(petersen, 2)
    t3 = hecke_graph_operator(petersen, 3)
    assert len(t0) == 10
    # On Petersen graph (girth 5), diagonal of T_2 = A^2 - 3I is zero (no self-returns in 2 non-backtracking steps)
    for i in range(10):
        assert t2.get(i, {}).get(i, 0.0) == 0.0
    assert dot(t2, t3) == dot(t3, t2)
    assert dot(t1, t3) == dot(t3, t1)

    # Disconnected union of two K_3 triangles (2-regular on 6 vertices):
    # Spectrum is {2, 2, -1, -1, -1, -1} ( wait: if we take a 3-regular graph with a bottleneck,
    # e.g. two K_4s with 1 edge swapped (dumbbell 3-regular on 8 vertices):
    # Edges of K_4 on {0,1,2,3} minus (2,3), K_4 on {4,5,6,7} minus (4,5), plus bridges (2,4) and (3,5).
    dumbbell: dict[int, dict[int, float]] = {i: {} for i in range(8)}
    dumbbell_edges = [
        (0, 1), (0, 2), (0, 3), (1, 2), (1, 3),
        (4, 6), (4, 7), (5, 6), (5, 7), (6, 7),
        (2, 4), (3, 5),
    ]
    for u, v in dumbbell_edges:
        dumbbell[u][v] = 1.0
        dumbbell[v][u] = 1.0
    # Extend to 16-vertex cycle of 4 clusters so second eigenvalue approaches 3 > 2*sqrt(2) ≈ 2.8284
    ring_clusters: dict[int, dict[int, float]] = {i: {} for i in range(24)}
    for c in range(6):
        base = 4 * c
        nxt = 4 * ((c + 1) % 6)
        local_edges = [
            (base, base + 1), (base, base + 2), (base, base + 3),
            (base + 1, base + 2), (base + 1, base + 3),
            (base + 3, nxt + 2),
        ]
        for u, v in local_edges:
            ring_clusters[u][v] = 1.0
            ring_clusters[v][u] = 1.0
    is_ram_ring, max_nt_ring, thresh_ring = is_ramanujan_graph(ring_clusters, degree=3)
    assert is_ram_ring is False
    assert max_nt_ring > thresh_ring
    gap_res = verify_ramanujan_spectral_gap(ring_clusters, degree=3)
    assert gap_res['degree_regularity'] is True
    assert gap_res['ramanujan_bound'] is False
    assert gap_res['hecke_commutativity'] is True

    # Irregular graph raises ValueError
    irregular = {0: {1: 1.0, 2: 1.0}, 1: {0: 1.0}, 2: {0: 1.0}}
    with pytest.raises(ValueError, match='not regular'):
        is_ramanujan_graph(irregular)
    assert verify_ramanujan_spectral_gap(irregular)['degree_regularity'] is False


def test_padic_field_axioms_and_tropical_valuation_bridge() -> None:
    """Verify PAdicField satisfies Field axioms, HasNorm, ultrametric inequality, and TropicalSemiring bridge."""
    qp = PAdicField(p=5, precision=10)
    assert Field in PAdicField.__mro__
    assert HasNorm in PAdicField.__mro__
    assert isinstance(qp, Field)
    assert isinstance(qp, HasNorm)
    assert qp.p == 5
    assert qp.precision == 10

    samples = [
        qp.zero,
        qp.one,
        qp.from_int(2),
        qp.from_int(5),
        qp.from_int(15),
        qp.from_int(-7),
        qp.from_rational(3, 5),
        qp.from_rational(7, 4),
    ]

    # Verify Field laws on Z_p units/integers
    unit_samples = [
        qp.zero,
        qp.one,
        qp.from_int(2),
        qp.from_int(3),
        qp.from_int(-7),
        qp.from_rational(7, 4),
    ]
    field_res = verify_field_laws(qp, unit_samples)
    assert all(field_res.values()), f'Failed PAdicField laws: {field_res}'

    # Also verify exact inversion on non-unit elements with positive and negative valuations
    for x in [qp.from_int(5), qp.from_int(15), qp.from_rational(3, 5)]:
        x_inv = qp.inv(x)
        assert qp.mul(x, x_inv) == qp.one

    # Verify ultrametric and tropical valuation laws
    ultra_res = verify_padic_ultrametric_inequality(qp, samples)
    assert all(ultra_res.values()), f'Failed p-adic ultrametric laws: {ultra_res}'
    assert verify_padic_ultrametric(qp, samples) == ultra_res

    # Explicit bridge to TropicalSemiring (min-plus)
    trop = TropicalSemiring()
    a = qp.from_int(25)   # v_5(25) = 2
    b = qp.from_int(125)  # v_5(125) = 3
    assert qp.valuation(a) == 2.0
    assert qp.valuation(b) == 3.0
    assert qp.valuation(qp.zero) == trop.zero  # +inf
    assert qp.valuation(qp.one) == trop.one    # 0.0

    # Multiplication in Q_p maps to tropical multiplication (+)
    assert qp.valuation(qp.mul(a, b)) == trop.mul(qp.valuation(a), qp.valuation(b)) == 5.0
    # Addition of distinct valuations maps to tropical addition (min)
    assert qp.valuation(qp.add(a, b)) == trop.add(qp.valuation(a), qp.valuation(b)) == 2.0
    # When lowest digits cancel (e.g. 1 + 4 = 5 in Q_5), valuation strictly increases: v_5(1 + 4) = 1 > min(0, 0)
    c1 = qp.from_int(1)
    c4 = qp.from_int(4)
    assert qp.valuation(qp.add(c1, c4)) == 1.0 > trop.add(qp.valuation(c1), qp.valuation(c4))


def test_padic_validation_and_falsification() -> None:
    """Verify PAdicField input validation and Popperian falsification of broken norms."""
    with pytest.raises(ValueError, match='prime integer'):
        PAdicField(p=4)
    with pytest.raises(ValueError, match='precision must be >= 1'):
        PAdicField(p=3, precision=0)

    qp = PAdicField(p=3, precision=8)
    with pytest.raises(ZeroDivisionError):
        qp.inv(qp.zero)
    with pytest.raises(ZeroDivisionError):
        qp.div(qp.one, qp.zero)
    with pytest.raises(ZeroDivisionError):
        qp.from_rational(1, 0)

    # Falsify ultrametric inequality with an Archimedean norm (where |1 + 1| = 2 > max(1, 1) = 1)
    class BrokenArchimedeanPAdic(PAdicField):
        def norm(self, x: dict[int, int]) -> float:
            return float(sum(abs(v) * (self.p**k) for k, v in x.items()))

    broken = BrokenArchimedeanPAdic(p=3, precision=8)
    res = verify_padic_ultrametric_inequality(broken, [broken.zero, broken.one, broken.from_int(2)])
    assert res['ultrametric_inequality'] is False
